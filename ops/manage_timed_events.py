#!/usr/bin/env python3
"""
Timed Event Operations Manager
IEEE AUSB: Case File: The Mid-Sem Leak

Interactive and CLI controller for live-event moments:
  - 4:35 PM: Vanishing Bonus Challenge appears (15-min window)
  - 4:45 PM: First Clue Drop
  - 4:50 PM: Vanishing Bonus Challenge vanishes
  - 5:00 PM: 10-Minute Lightning Round begins (double points via bonus awards)
  - 5:10 PM: Lightning Round ends & Second Clue Drop
  - 5:15 PM: Scoreboard Blackout (Suspense mode)
  - 5:30 PM: Scoreboard Reveal (Closing ceremony)

Scoring notes
-------------
CTFd re-prices dynamic challenges *retroactively*: a team's score is the sum of
the current `value` of every challenge it has solved. Bumping `initial` for ten
minutes would therefore inflate every earlier solve as well, so a time-boxed
"double points" round cannot be implemented by touching challenge values.

Instead `lightning_end` scans `submissions` for correct answers inside the
recorded window and pays each team a discrete bonus award equal to the current
value of each challenge solved inside it — a true 2x for that window only.

Vanishing / Lightning challenge names are read from the environment so the ops
runbook stays declarative:
    BONUS_VANISHING_CHALLENGE   (default: "Vanishing")
    BONUS_LIGHTNING_CHALLENGE   (default: "Lightning", optional)
"""

import os
import sys
import argparse
import subprocess
import requests
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# Bonus challenge names (override in .env / shell, keep runbook declarative).
VANISHING_CHALLENGE = os.getenv("BONUS_VANISHING_CHALLENGE", "Vanishing")
LIGHTNING_CHALLENGE = os.getenv("BONUS_LIGHTNING_CHALLENGE", "Lightning")

# CTFd config keys used to track the lightning window across CLI invocations.
LIGHTNING_WINDOW_KEY = "lightning_window_start"
LIGHTNING_AWARDED_KEY = "lightning_window_awarded"
LIGHTNING_BONUS_AWARD = "⚡ Lightning Round Bonus (2x)"


def load_env():
    env_file = ROOT_DIR / ".env"
    env_vars = {}
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars


def run_sql(sql):
    """Runs a statement against the live CTFd database (tracked, reproducible)."""
    env = load_env()
    pwd = env.get("MYSQL_ROOT_PASSWORD", "")
    db = env.get("MYSQL_DATABASE", "ctfd")
    cmd = [
        "docker", "exec", "ctfd_db", "mariadb",
        "-uroot", f"-p{pwd}", db, "-N", "-B", "-e", sql,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or "SQL execution failed")
    return res.stdout.strip()


def flush_cache():
    """Scoreboard/awards are cached in Redis; flush so ops changes show instantly."""
    subprocess.run(
        ["docker", "exec", "ctfd_cache", "redis-cli", "FLUSHALL"],
        capture_output=True, text=True,
    )


def get_config(key, default=None):
    try:
        out = run_sql(f"SELECT value FROM config WHERE `key` = '{key}' LIMIT 1;")
    except RuntimeError:
        return default
    return out or default


def set_config(key, value):
    if run_sql(f"SELECT COUNT(*) FROM config WHERE `key` = '{key}';").strip() in ("0", ""):
        run_sql(f"INSERT INTO config (`key`, value) VALUES ('{key}', '{value}');")
    else:
        run_sql(f"UPDATE config SET value = '{value}' WHERE `key` = '{key}';")


def get_headers(token):
    return {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }


def send_ctfd_notification(title, content):
    env = load_env()
    token = env.get("CTFD_ADMIN_TOKEN", "")
    api_url = env.get("CTFD_API_URL", "http://localhost")
    if not token or token == "placeholder_generate_after_ctfd_first_run":
        print(f"[*] Broadcast Alert: [{title}] {content}")
        return False
    try:
        url = f"{api_url.rstrip('/')}/api/v1/notifications"
        payload = {"title": title, "content": content}
        res = requests.post(url, json=payload, headers=get_headers(token), timeout=5)
        if res.status_code == 200:
            print(f"[+] Alert broadcasted to all teams: '{title}'")
            return True
    except Exception as e:
        print(f"[!] Notification error: {e}")
    return False


def _api_challenges(token, api_url):
    """Returns the challenge list via the admin API, or None if the token is rejected."""
    try:
        res = requests.get(
            f"{api_url.rstrip('/')}/api/v1/challenges",
            headers=get_headers(token), timeout=5,
        )
        if res.status_code == 200:
            return res.json().get("data", [])
        print(f"[!] Admin API rejected the token (HTTP {res.status_code}).")
        print("    Falling back to direct database control. Regenerate the token in")
        print("    CTFd Admin -> Settings -> Access Tokens and update CTFD_ADMIN_TOKEN.")
        return None
    except Exception as e:
        print(f"[!] API error: {e}")
        return None


def find_challenge_id(challenge_name):
    """Returns the CTFd challenge id matching `challenge_name`, or None."""
    env = load_env()
    token = env.get("CTFD_ADMIN_TOKEN", "")
    api_url = env.get("CTFD_API_URL", "http://localhost")
    if token and token != "placeholder_generate_after_ctfd_first_run":
        challenges = _api_challenges(token, api_url)
        if challenges is not None:
            for c in challenges:
                if challenge_name.lower() in c.get("name", "").lower():
                    return c.get("id")
            return None
    try:
        out = run_sql(
            "SELECT id FROM challenges "
            f"WHERE name LIKE '%{challenge_name}%' AND state <> 'deleted' LIMIT 1;"
        )
        return int(out) if out else None
    except (RuntimeError, ValueError):
        return None


def set_challenge_state(challenge_name, state, required=False):
    """Flips a challenge between 'visible' and 'hidden'. Returns True on success.

    Uses the admin API when the token is valid, otherwise writes the row directly
    and flushes Redis (same path the seeder uses), so a stale token can never
    take the 4:35 PM or 5:10 PM milestone down.

    `required=True` makes a missing challenge a hard operational error: we must
    never broadcast "bonus unlocked" when nothing was actually revealed.
    """
    env = load_env()
    token = env.get("CTFD_ADMIN_TOKEN", "")
    api_url = env.get("CTFD_API_URL", "http://localhost")
    cid = find_challenge_id(challenge_name)

    if cid is None:
        level = "ERROR" if required else "WARN"
        print(f"[!] {level}: no challenge matching '{challenge_name}' exists.")
        if required:
            print("    There is no bonus challenge authored for this slot yet. Create")
            print("    challenges/<name>/challenge.yml and run `uv run ctf seed`, or point")
            print("    BONUS_VANISHING_CHALLENGE at an existing challenge name.")
            print("    Refusing to broadcast a bonus drop that does not exist.")
        return False

    use_api = bool(token) and token != "placeholder_generate_after_ctfd_first_run"
    if use_api:
        try:
            patch_url = f"{api_url.rstrip('/')}/api/v1/challenges/{cid}"
            patch_res = requests.patch(
                patch_url, json={"state": state}, headers=get_headers(token), timeout=5
            )
            if patch_res.status_code == 200:
                print(f"[+] Challenge '{challenge_name}' (ID {cid}) set to {state.upper()}!")
                flush_cache()
                return True
        except Exception as e:
            print(f"[!] API error: {e}")

    # Direct DB control (tracked code path, same as the seeder) + cache flush.
    try:
        run_sql(f"UPDATE challenges SET state = '{state}' WHERE id = {cid};")
        flush_cache()
        print(f"[+] Challenge '{challenge_name}' (ID {cid}) set to {state.upper()} via database.")
        return True
    except RuntimeError as e:
        print(f"[!] Database fallback failed: {e}")
        return False


def award_lightning_bonus():
    """Pays a true 2x: every challenge solved inside the window earns its
    current value again as a bonus award. Idempotent per window.
    """
    start = get_config(LIGHTNING_WINDOW_KEY)
    if not start:
        print("[!] No lightning window recorded. Run `--event lightning_start` first.")
        return False

    if get_config(LIGHTNING_AWARDED_KEY) == start:
        print(f"[.] Lightning bonus already paid for window starting {start}. Skipping.")
        return True

    try:
        rows = run_sql(
            "SELECT team_id, challenge_id FROM submissions "
            "WHERE type = 'correct' "
            f"AND date >= '{start}' AND date <= UTC_TIMESTAMP(6);"
        )
    except RuntimeError as e:
        print(f"[!] Could not read submissions: {e}")
        return False

    if not rows:
        print("[.] No solves landed inside the lightning window — no bonus paid.")
        set_config(LIGHTNING_AWARDED_KEY, start)
        return True

    values, team_names = {}, {}
    for line in run_sql("SELECT id, value FROM challenges;").splitlines():
        cid, val = line.split("\t")
        values[int(cid)] = int(val)
    for line in run_sql("SELECT id, name FROM teams;").splitlines():
        tid, tname = line.split("\t", 1)
        team_names[int(tid)] = tname

    per_team, solve_counts = {}, {}
    for line in rows.splitlines():
        team_id, challenge_id = line.split("\t")
        if not team_id or team_id == "NULL":
            continue  # individual-mode solve, no team to credit
        tid, cid = int(team_id), int(challenge_id)
        per_team[tid] = per_team.get(tid, 0) + values.get(cid, 0)
        solve_counts[tid] = solve_counts.get(tid, 0) + 1

    print("\n  ⚡ Lightning Round bonus payouts:")
    for tid, bonus in sorted(per_team.items(), key=lambda kv: -kv[1]):
        n = solve_counts[tid]
        run_sql(
            "INSERT INTO awards (team_id, name, description, date, value, category, type) "
            f"VALUES ({tid}, '{LIGHTNING_BONUS_AWARD}', "
            f"'{n} solve(s) inside the 10-minute lightning window ({start} UTC).', "
            f"UTC_TIMESTAMP(6), {bonus}, 'bonus', 'standard');"
        )
        print(f"    {team_names.get(tid, f'Team {tid}'):24} +{bonus:4} pts ({n} solve(s))")

    set_config(LIGHTNING_AWARDED_KEY, start)
    flush_cache()
    return True


def trigger_event(event_key):
    print(f"\n---> Executing Event: {event_key.upper()}")

    if event_key == "vanishing_start":
        if set_challenge_state(VANISHING_CHALLENGE, "visible", required=True):
            send_ctfd_notification(
                "⏳ TIME-SENSITIVE EVIDENCE DETECTED!",
                "A temporary cache trace was discovered on the lab network! It will self-destruct in 15 minutes (at 4:50 PM). Investigate now!"
            )

    elif event_key == "vanishing_end":
        if set_challenge_state(VANISHING_CHALLENGE, "hidden"):
            send_ctfd_notification(
                "🔒 EVIDENCE PURGED",
                "The temporary cache trace has vanished from the system."
            )

    elif event_key == "clue_drop_1":
        send_ctfd_notification(
            "📂 CASE UPDATE: Clue Drop #1 Released",
            "Forensics team recovered deleted syslog timestamps. Check Act II: Portal Breach for new hints in the case file!"
        )

    elif event_key == "lightning_start":
        try:
            set_config(LIGHTNING_WINDOW_KEY, run_sql("SELECT UTC_TIMESTAMP(6);"))
            set_config(LIGHTNING_AWARDED_KEY, "")
        except RuntimeError as e:
            print(f"[!] Could not record lightning window: {e}")
            return
        # Optional speed-run puzzle; the bonus applies to every challenge.
        set_challenge_state(LIGHTNING_CHALLENGE, "visible", required=False)
        send_ctfd_notification(
            "⚡ 10-MINUTE LIGHTNING ROUND ACTIVE!",
            "Double points! Every challenge you solve before 5:10 PM earns its points again as a bonus award. Go!"
        )

    elif event_key == "lightning_end":
        set_challenge_state(LIGHTNING_CHALLENGE, "hidden", required=False)
        award_lightning_bonus()
        send_ctfd_notification(
            "⚡ Lightning Round Closed",
            "Lightning round submissions are now closed. Bonus points have been credited to the scoreboard."
        )

    elif event_key == "clue_drop_2":
        send_ctfd_notification(
            "📂 CASE UPDATE: Clue Drop #2 Released",
            "The encrypted chat key derivation function has been identified. Check Act III dossier!"
        )

    elif event_key == "blackout":
        subprocess.run([sys.executable, str(ROOT_DIR / "ops" / "freeze_scoreboard.py")])
        send_ctfd_notification(
            "🌑 SCOREBOARD BLACKOUT",
            "The scoreboard is now dark! Final 15 minutes of investigation. Who will unmask the culprit first?"
        )

    elif event_key == "reveal":
        subprocess.run([sys.executable, str(ROOT_DIR / "ops" / "unfreeze_scoreboard.py")])
        send_ctfd_notification(
            "🏆 CASE CLOSED: Winner Standings Revealed",
            "All submissions calculated. The culprit has been unmasked. Head to the presentation screen!"
        )

    else:
        print(f"[!] Unknown event: {event_key}")


def interactive_menu():
    while True:
        print("\n==========================================================")
        print(" [IEEE AUSB] Live Event Timeline Control Console")
        print(" Event: Case File: The Mid-Sem Leak")
        print("==========================================================")
        print(" 1) [4:35 PM] Unlock 15-Min Vanishing Challenge")
        print(" 2) [4:45 PM] Clue Drop #1 Broadcast")
        print(" 3) [4:50 PM] Close/Hide Vanishing Challenge")
        print(" 4) [5:00 PM] Start 10-Min Lightning Round (Double Points)")
        print(" 5) [5:10 PM] Close Lightning Round & Clue Drop #2")
        print(" 6) [5:15 PM] Trigger Scoreboard Blackout (Freeze)")
        print(" 7) [5:30 PM] Reveal Scoreboard (Closing Ceremony)")
        print(" 8) Create Live Snapshot Backup")
        print(" 0) Exit")
        print("==========================================================")
        choice = input("Select action [0-8]: ").strip()

        if choice == "1":
            trigger_event("vanishing_start")
        elif choice == "2":
            trigger_event("clue_drop_1")
        elif choice == "3":
            trigger_event("vanishing_end")
        elif choice == "4":
            trigger_event("lightning_start")
        elif choice == "5":
            trigger_event("lightning_end")
            trigger_event("clue_drop_2")
        elif choice == "6":
            trigger_event("blackout")
        elif choice == "7":
            trigger_event("reveal")
        elif choice == "8":
            subprocess.run([sys.executable, str(ROOT_DIR / "ctf.py"), "backup"])
        elif choice == "0":
            break
        else:
            print("[!] Invalid option.")


def main():
    parser = argparse.ArgumentParser(description="CTF Event Operations Manager")
    parser.add_argument(
        "--event",
        choices=[
            "vanishing_start", "vanishing_end", "clue_drop_1",
            "lightning_start", "lightning_end", "clue_drop_2",
            "blackout", "reveal"
        ],
        help="Execute a specific scheduled milestone"
    )
    args = parser.parse_args()

    if args.event:
        trigger_event(args.event)
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
