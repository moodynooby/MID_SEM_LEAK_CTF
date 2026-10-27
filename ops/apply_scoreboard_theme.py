#!/usr/bin/env python3
"""
Theme Activator & Scoreboard Configurator
IEEE AUSB: Case File: The Mid-Sem Leak

Activates `hacker-theme` as the primary CTFd theme via the REST API.
Scoreboard styling, big-screen typography, medals, and live solve ticker
are built directly into `themes/hacker-theme/templates/scoreboard.html`,
eliminating the need for database injection into `theme_header` / `theme_footer`.
"""

import sys
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
        "Content-Type": "application/json",
    }


def set_config(api_url, token, key, value):
    url = f"{api_url.rstrip('/')}/api/v1/configs/{key}"
    resp = requests.patch(url, json={"value": value}, headers=get_headers(token), timeout=5)
    return resp.status_code == 200


def main():
    print("==========================================================")
    print(" [IEEE AUSB CTF] Activating Hacker Theme & Resetting Injections")
    print("==========================================================")

    env = load_env()
    token = env.get("CTFD_ADMIN_TOKEN", "")
    api_url = env.get("CTFD_API_URL", "http://localhost")

    if not token or token == "placeholder_generate_after_ctfd_first_run":
        print("[!] CTFD_ADMIN_TOKEN not set in .env — cannot apply theme live.")
        print("    Generate one from CTFd Admin -> Profile -> Access Tokens,")
        print("    add it to .env, then re-run: uv run ctf theme")
        sys.exit(1)

    print("[*] Activating primary theme 'hacker-theme' via CTFd API...")
    theme_ok = set_config(api_url, token, "ctf_theme", "hacker-theme")

    # Clear legacy raw HTML/JS injections from DB since styles are native in templates
    print("[*] Cleaning up legacy database theme_header & theme_footer injections...")
    header_ok = set_config(api_url, token, "theme_header", "")
    footer_ok = set_config(api_url, token, "theme_footer", "")

    if theme_ok and header_ok and footer_ok:
        print("[+] Primary theme ('hacker-theme') activated successfully!")
        print("    All scoreboard projector styling is now natively rendered from templates.")
    else:
        print("[!] Failed to apply one or more configs. Check CTFD_ADMIN_TOKEN and CTFD_API_URL.")
        sys.exit(1)


if __name__ == "__main__":
    main()
