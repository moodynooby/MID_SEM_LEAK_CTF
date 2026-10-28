#!/usr/bin/env python3
"""
Intrusion Punishments, Decoy Honeyflag Trap & Siren Alert Monitor
IEEE AUSB: Case File: The Mid-Sem Leak (Issue #16 & Issue #25 Integration)

Monitors CTFd submissions in real-time for:
  1. Decoy Honeyflags (e.g. case{proctor_emergency_override_lockout_token})
  2. Bruteforce Threshold Violations (5 consecutive incorrect submissions)

When triggered:
  - Engages team lockout cooldown
  - Updates active_alert.json for projector AV siren strobe
  - Optionally broadcasts CTFd announcement to all participants
  - Optionally applies score penalty in CTFd
  - Records full incident audit log

Usage:
  python ops/siren_alert/monitor.py               # Run continuous monitor loop
  python ops/siren_alert/monitor.py --once        # Single audit pass
  python ops/siren_alert/monitor.py --test [TEAM] # Simulate live test siren
"""

import os
import sys
import time
import json
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONF_FILE = ROOT_DIR / "conf" / "gamification.json"
ALERT_FILE = ROOT_DIR / "av-console" / "active_alert.json"
OPS_ALERT_FILE = ROOT_DIR / "ops" / "siren_alert" / "active_alert.json"
AUDIT_LOG_FILE = ROOT_DIR / "ops" / "siren_alert" / "intrusion_audit.log"
LOCKOUTS_FILE = ROOT_DIR / "ops" / "siren_alert" / "active_lockouts.json"

DEFAULT_GAMIFICATION = {
    "intrusion_punishments": {
        "enabled": True,
        "fails_threshold": 5,
        "fails_lockout_seconds": 60,
        "decoy_lockout_seconds": 120,
        "point_deduction_on_decoy": 0,
        "sound_siren": True,
        "siren_duration_seconds": 5,
        "broadcast_to_ctfd": True,
        "decoy_flags": [
            {
                "flag": "case{proctor_emergency_override_lockout_token}",
                "name": "AI Proctor Bot Honeyflag",
                "lockout_seconds": 120,
                "penalty_points": 0,
                "alert_message": "🚨 HONEYPOT TRAP TRIGGERED: Proctor Bot emergency override token entered!"
            },
            {
                "flag": "case{faculty_admin_portal_root_auth_2026}",
                "name": "Faculty Vault Admin Decoy",
                "lockout_seconds": 120,
                "penalty_points": 0,
                "alert_message": "🚨 HONEYPOT TRAP TRIGGERED: Faculty Exam Vault admin decoy entered!"
            },
            {
                "flag": "case{decoy_plaintext_login_honeyflag}",
                "name": "PCAP Plaintext Login Decoy",
                "lockout_seconds": 120,
                "penalty_points": 0,
                "alert_message": "🚨 HONEYPOT TRAP TRIGGERED: Plaintext PCAP login decoy entered!"
            },
            {
                "flag": "case{decoy_telemetry_post_pcap}",
                "name": "PCAP Telemetry Decoy",
                "lockout_seconds": 120,
                "penalty_points": 0,
                "alert_message": "🚨 HONEYPOT TRAP TRIGGERED: Telemetry beacon honeyflag entered!"
            },
            {
                "flag": "case{decoy_student_mac_address}",
                "name": "Wi-Fi DHCP MAC Decoy",
                "lockout_seconds": 120,
                "penalty_points": 0,
                "alert_message": "🚨 HONEYPOT TRAP TRIGGERED: Wi-Fi DHCP spoofed MAC decoy entered!"
            },
            {
                "flag": "case{sansh_vhah_library_ap_decoy}",
                "name": "Wi-Fi Library AP Decoy",
                "lockout_seconds": 120,
                "penalty_points": 0,
                "alert_message": "🚨 HONEYPOT TRAP TRIGGERED: Sansh Vhah innocent alibi decoy entered!"
            },
            {
                "flag": "case{staging_lab207_workstation_setup_key}",
                "name": "CheatSheet Staging Comment Decoy",
                "lockout_seconds": 120,
                "penalty_points": 0,
                "alert_message": "🚨 HONEYPOT TRAP TRIGGERED: Staging workstation setup decoy entered!"
            },
            {
                "flag": "case{decoy_superficial_lead_check_source}",
                "name": "CheatSheet Superficial Lead Decoy",
                "lockout_seconds": 120,
                "penalty_points": 0,
                "alert_message": "🚨 HONEYPOT TRAP TRIGGERED: Superficial lead honeyflag entered!"
            },
            {
                "flag": "case{decoy_git_log_superficial_commit}",
                "name": "Git Commit Red Herring Decoy",
                "lockout_seconds": 120,
                "penalty_points": 0,
                "alert_message": "🚨 HONEYPOT TRAP TRIGGERED: Superficial Git commit red herring entered!"
            },
            {
                "flag": "case{decoy_superficial_html_comment}",
                "name": "HTML Comment Red Herring Decoy",
                "lockout_seconds": 120,
                "penalty_points": 0,
                "alert_message": "🚨 HONEYPOT TRAP TRIGGERED: HTML Comment red herring entered!"
            },
            {
                "flag": "case{nice_try_blind_ai_wifi_grep}",
                "name": "Blind AI Wi-Fi Scraper Trap",
                "lockout_seconds": 120,
                "penalty_points": 0,
                "alert_message": "🚨 HONEYPOT TRAP TRIGGERED: Blind AI scraping pattern trapped!"
            }
        ]
    }
}

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

def load_config():
    if CONF_FILE.exists():
        try:
            with open(CONF_FILE, "r") as f:
                data = json.load(f)
                return data.get("intrusion_punishments", DEFAULT_GAMIFICATION["intrusion_punishments"])
        except Exception:
            pass
    return DEFAULT_GAMIFICATION["intrusion_punishments"]

def send_ctfd_notification(title, content):
    env = load_env()
    token = env.get("CTFD_ADMIN_TOKEN", "")
    api_url = env.get("CTFD_API_URL", "http://localhost")
    if not token or token == "placeholder_generate_after_ctfd_first_run":
        return False
    try:
        url = f"{api_url.rstrip('/')}/api/v1/notifications"
        headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
        res = requests.post(url, json={"title": title, "content": content}, headers=headers, timeout=4)
        return res.status_code == 200
    except Exception:
        return False

def apply_point_penalty(team_id, points, reason):
    if points <= 0:
        return
    env = load_env()
    user = env.get("MYSQL_USER", "ctfd")
    password = env.get("MYSQL_PASSWORD", "ctfd_secure_pass")
    db = env.get("MYSQL_DATABASE", "ctfd")
    cli = "docker" if subprocess.run(["which", "docker"], capture_output=True).returncode == 0 else "podman"

    query = (
        f"INSERT INTO awards (team_id, name, description, date, value, category, type) "
        f"VALUES ({team_id}, 'Intrusion Penalty', '{reason}', NOW(), -{abs(points)}, 'Penalties', 'standard');"
    )
    cmd = [cli, "exec", "ctfd_db", "mariadb", f"-u{user}", f"-p{password}", db, "-e", query]
    subprocess.run(cmd, capture_output=True)

def write_active_alert(alert_data):
    """Write alert state to both av-console and ops so Web UI catches it."""
    for p in [ALERT_FILE, OPS_ALERT_FILE]:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w") as f:
                json.dump(alert_data, f, indent=2)
        except Exception as e:
            print(f"[!] Alert write error for {p}: {e}")

def log_audit(event_type, team, details):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] [{event_type}] Team: {team} | Details: {details}\n"
    try:
        with open(AUDIT_LOG_FILE, "a") as f:
            f.write(msg)
    except Exception:
        pass
    print(msg.strip())

def trigger_punishment(team_id, team_name, reason, lockout_seconds, penalty_points=0, alert_msg=None):
    now_ts = int(time.time())
    expires_ts = now_ts + lockout_seconds

    if not alert_msg:
        alert_msg = f"🚨 INTRUSION DETECTED: {team_name} locked out for {lockout_seconds}s! Reason: {reason}"

    alert_payload = {
        "active": True,
        "team_id": team_id,
        "team_name": team_name,
        "reason": reason,
        "lockout_seconds": lockout_seconds,
        "triggered_at": now_ts,
        "expires_at": expires_ts,
        "alert_message": alert_msg,
        "sound_siren": True
    }
    write_active_alert(alert_payload)

    # Record active lockout
    lockouts = {}
    if LOCKOUTS_FILE.exists():
        try:
            with open(LOCKOUTS_FILE, "r") as f:
                lockouts = json.load(f)
        except Exception:
            pass
    lockouts[str(team_id)] = {
        "team_name": team_name,
        "expires_at": expires_ts,
        "reason": reason
    }
    with open(LOCKOUTS_FILE, "w") as f:
        json.dump(lockouts, f, indent=2)

    # Broadcast notification to CTFd
    cfg = load_config()
    if cfg.get("broadcast_to_ctfd", True):
        send_ctfd_notification("⚠️ SECURITY INTRUSION ALERT", alert_msg)

    # Point deduction if configured
    if penalty_points > 0:
        apply_point_penalty(team_id, penalty_points, reason)

    log_audit("PUNISHMENT_TRIGGERED", team_name, f"{reason} | Lockout: {lockout_seconds}s | Penalty: -{penalty_points}pts")

def get_db_submissions(since_id=0):
    env = load_env()
    user = env.get("MYSQL_USER", "ctfd")
    password = env.get("MYSQL_PASSWORD", "ieee_ausb_ctfd_db_user_2026!")
    db = env.get("MYSQL_DATABASE", "ctfd")
    cli = "docker" if subprocess.run(["which", "docker"], capture_output=True).returncode == 0 else "podman"

    query = (
        f"SELECT s.id, s.team_id, COALESCE(t.name, 'Station Unknown') as team_name, "
        f"s.provided, s.type, s.date "
        f"FROM submissions s "
        f"LEFT JOIN teams t ON s.team_id = t.id "
        f"WHERE s.id > {since_id} "
        f"ORDER BY s.id ASC;"
    )
    cmd = [
        cli, "exec", "ctfd_db", "mariadb",
        f"-u{user}", f"-p{password}", db,
        "--batch", "--skip-column-names", "-e", query
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return []

    submissions = []
    for line in res.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 5:
            submissions.append({
                "id": int(parts[0]),
                "team_id": parts[1],
                "team_name": parts[2],
                "provided": parts[3].strip(),
                "type": parts[4].strip(),
                "date": parts[5] if len(parts) > 5 else ""
            })
    return submissions

def run_monitor(once=False):
    cfg = load_config()
    decoy_map = {d["flag"].strip().lower(): d for d in cfg.get("decoy_flags", [])}
    consecutive_fails = {}
    last_id = 0

    print("==========================================================")
    print(" [IEEE AUSB CTF] Intrusion & Decoy Flag Monitor Live")
    print(f" Loaded {len(decoy_map)} Decoy Honeyflags | Fails Threshold: {cfg.get('fails_threshold', 5)}")
    print("==========================================================")

    # Initial query to get max id so we only watch future submissions or start from 0
    init_subs = get_db_submissions(0)
    if init_subs:
        last_id = max(s["id"] for s in init_subs)
        print(f"[*] Synchronized with database. Starting from submission ID: {last_id}")

    while True:
        try:
            subs = get_db_submissions(last_id)
            for s in subs:
                sub_id = s["id"]
                team_id = s["team_id"]
                team_name = s["team_name"]
                provided = s["provided"].strip().lower()
                sub_type = s["type"]

                if sub_id > last_id:
                    last_id = sub_id

                # 1. Check for Decoy Honeyflag Match
                if provided in decoy_map:
                    dec = decoy_map[provided]
                    lockout = dec.get("lockout_seconds", cfg.get("decoy_lockout_seconds", 120))
                    penalty = dec.get("penalty_points", cfg.get("point_deduction_on_decoy", 0))
                    msg = dec.get("alert_message", f"🚨 HONEYPOT TRAP: Decoy '{provided}' entered by {team_name}!")
                    print(f"\n[!] DECOY HONEYPOT DETECTED: {team_name} entered {provided}")
                    trigger_punishment(
                        team_id=team_id,
                        team_name=team_name,
                        reason=f"Decoy Honeyflag Triggered: {dec.get('name', 'Honeypot')}",
                        lockout_seconds=lockout,
                        penalty_points=penalty,
                        alert_msg=msg
                    )
                    consecutive_fails[team_id] = 0
                    continue

                # 2. Check for Incorrect Submission (Anti-Bruteforce)
                if sub_type == "incorrect":
                    consecutive_fails[team_id] = consecutive_fails.get(team_id, 0) + 1
                    fails_count = consecutive_fails[team_id]
                    threshold = cfg.get("fails_threshold", 5)

                    if fails_count >= threshold:
                        lockout = cfg.get("fails_lockout_seconds", 60)
                        msg = f"🛑 RATE LIMIT ENGAGED: {team_name} locked out for {lockout}s ({fails_count} failed submissions)."
                        print(f"\n[!] BRUTEFORCE THRESHOLD HIT: {team_name} ({fails_count} consecutive fails)")
                        trigger_punishment(
                            team_id=team_id,
                            team_name=team_name,
                            reason=f"Bruteforce Lockout: {fails_count} consecutive incorrect flags",
                            lockout_seconds=lockout,
                            penalty_points=0,
                            alert_msg=msg
                        )
                        consecutive_fails[team_id] = 0

                elif sub_type == "correct":
                    # Reset failure count on valid solve
                    consecutive_fails[team_id] = 0

            if once:
                break

            time.sleep(1.5)

        except KeyboardInterrupt:
            print("\n[*] Monitor stopped gracefully.")
            break
        except Exception as e:
            print(f"[!] Monitor error: {e}")
            time.sleep(2)

def simulate_test_alert(team_name="Station 4 - HashCrashers", reason="Decoy PCAP Flag Triggered"):
    cfg = load_config()
    print(f"[*] Simulating Live Intrusion Alert for: {team_name}...")
    trigger_punishment(
        team_id=4,
        team_name=team_name,
        reason=reason,
        lockout_seconds=cfg.get("decoy_lockout_seconds", 120),
        penalty_points=cfg.get("point_deduction_on_decoy", 0),
        alert_msg=f"🚨 [TEST SIMULATION] INTRUSION DETECTED: {team_name} trapped in honeypot!"
    )
    print("[+] Test alert written to active_alert.json and logged to intrusion_audit.log!")
    print("    Open http://<LAN_IP>/av-console/siren.html to see the projector strobe & hear siren.")

def main():
    parser = argparse.ArgumentParser(description="CTFd Intrusion & Decoy Flag Monitor")
    parser.add_argument("--once", action="store_true", help="Run single pass and exit")
    parser.add_argument("--test", nargs="?", const="Station 4 - HashCrashers", help="Simulate a test alert for specified team")
    parser.add_argument("--reason", default="Decoy Honeyflag Triggered", help="Reason for test alert")
    args = parser.parse_args()

    if args.test:
        simulate_test_alert(args.test, args.reason)
    else:
        run_monitor(once=args.once)

if __name__ == "__main__":
    main()
