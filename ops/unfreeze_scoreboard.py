#!/usr/bin/env python3
"""
Scoreboard Unfreeze Trigger
IEEE AUSB: Case File: The Mid-Sem Leak (5:30 PM Closing Ceremony Reveal)

Unfreezes the CTFd scoreboard to reveal the final winner standings.
"""

import os
import sys
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

def unfreeze_via_api(api_url, token):
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    url = f"{api_url.rstrip('/')}/api/v1/configs"
    payload = {"value": "false"}
    resp = requests.patch(f"{url}/freeze", json=payload, headers=headers, timeout=5)
    return resp.status_code == 200

def unfreeze_via_db(env_vars):
    cli = "docker" if subprocess.run(["which", "docker"], capture_output=True).returncode == 0 else "podman"
    user = env_vars.get("MYSQL_USER", "ctfd")
    password = env_vars.get("MYSQL_PASSWORD", "ctfd_secure_pass")
    db = env_vars.get("MYSQL_DATABASE", "ctfd")

    query = (
        "INSERT INTO config (`key`, `value`) VALUES ('freeze', 'false') "
        "ON DUPLICATE KEY UPDATE `value`='false';"
    )
    cmd = [
        cli, "exec", "ctfd_db", "mariadb",
        f"-u{user}", f"-p{password}", db,
        "-e", query
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        subprocess.run([cli, "restart", "ctfd_cache"], capture_output=True)
        return True
    print(f"[!] DB Error: {res.stderr}")
    return False

def main():
    print("==========================================================")
    print(" [IEEE AUSB CTF] 5:30 PM Scoreboard Reveal & Closing Ceremony")
    print("==========================================================")
    env = load_env()
    token = env.get("CTFD_ADMIN_TOKEN", "")
    api_url = env.get("CTFD_API_URL", "http://localhost")

    success = False
    if token and token != "placeholder_generate_after_ctfd_first_run":
        try:
            print("[*] Attempting unfreeze via CTFd REST API...")
            if unfreeze_via_api(api_url, token):
                print("[+] Scoreboard successfully UNFROZEN via API!")
                success = True
        except Exception as e:
            print(f"[!] API call failed ({e}). Falling back to database...")

    if not success:
        print("[*] Unfreezing scoreboard directly via MariaDB configuration...")
        if unfreeze_via_db(env):
            print("[+] Scoreboard successfully UNFROZEN via Database!")
            success = True

    if success:
        print("\n[FINAL SCORES REVEALED!]")
        print("Refresh the projector display to reveal the final winner rankings.")
    else:
        print("[!] Failed to unfreeze scoreboard. Check container status.")
        sys.exit(1)

if __name__ == "__main__":
    main()
