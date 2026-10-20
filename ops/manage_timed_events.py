#!/usr/bin/env python3
"""
Timed Event Operations Manager
IEEE AUSB: Case File: The Mid-Sem Leak

Interactive and CLI controller for live-event moments:
  - 4:35 PM: Vanishing Bonus Challenge appears (15-min window)
  - 4:45 PM: First Clue Drop
  - 4:50 PM: Vanishing Bonus Challenge vanishes
  - 5:00 PM: 10-Minute Lightning Round begins (Speed run, double points)
  - 5:10 PM: Lightning Round ends & Second Clue Drop
  - 5:15 PM: Scoreboard Blackout (Suspense mode)
  - 5:30 PM: Scoreboard Reveal (Closing ceremony)
"""

import os
import sys
import argparse
import subprocess
import requests
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

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

def set_challenge_state(challenge_name, state):
    """state can be 'visible' or 'hidden'"""
    env = load_env()
    token = env.get("CTFD_ADMIN_TOKEN", "")
    api_url = env.get("CTFD_API_URL", "http://localhost")
    if not token or token == "placeholder_generate_after_ctfd_first_run":
        print(f"[*] Simulating state change: Challenge '{challenge_name}' -> {state.upper()}")
        print("    (To execute live, add CTFD_ADMIN_TOKEN in .env)")
        return False

    try:
        # Search for challenge by name
        url = f"{api_url.rstrip('/')}/api/v1/challenges"
        res = requests.get(url, headers=get_headers(token), timeout=5)
        if res.status_code == 200:
            challenges = res.json().get("data", [])
            for c in challenges:
                if challenge_name.lower() in c.get("name", "").lower():
                    cid = c.get("id")
                    patch_url = f"{api_url.rstrip('/')}/api/v1/challenges/{cid}"
                    patch_res = requests.patch(patch_url, json={"state": state}, headers=get_headers(token), timeout=5)
                    if patch_res.status_code == 200:
                        print(f"[+] Challenge '{c.get('name')}' (ID {cid}) set to {state.upper()}!")
                        return True
            print(f"[!] Challenge matching '{challenge_name}' not found.")
    except Exception as e:
        print(f"[!] API error: {e}")
    return False

def trigger_event(event_key):
    print(f"\n---> Executing Event: {event_key.upper()}")
    if event_key == "vanishing_start":
        set_challenge_state("Vanishing", "visible")
        send_ctfd_notification(
            "⏳ TIME-SENSITIVE EVIDENCE DETECTED!",
            "A temporary cache trace was discovered on the lab network! It will self-destruct in 15 minutes (at 4:50 PM). Investigate now!"
        )
    elif event_key == "vanishing_end":
        set_challenge_state("Vanishing", "hidden")
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
        set_challenge_state("Lightning", "visible")
        send_ctfd_notification(
            "⚡ 10-MINUTE LIGHTNING ROUND ACTIVE!",
            "Speed puzzle unlocked! Double points available for solving within the next 10 minutes (until 5:10 PM)!"
        )
    elif event_key == "lightning_end":
        set_challenge_state("Lightning", "hidden")
        send_ctfd_notification(
            "⚡ Lightning Round Closed",
            "Lightning round submissions are now closed."
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
            subprocess.run([str(ROOT_DIR / "ops" / "backup.sh")])
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
