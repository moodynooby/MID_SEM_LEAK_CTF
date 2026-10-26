#!/usr/bin/env python3
"""
Scoreboard Projector Theme Applier
IEEE AUSB: Case File: The Mid-Sem Leak

Pushes ctfd-theme/scoreboard-projector.{css,js} into CTFd's
`theme_header` / `theme_footer` configs via the REST API, so the
big-screen /scoreboard styling is version-controlled and reproducible
instead of a manual, uncommitted Admin UI edit.

CTFd injects `theme_header` into <head> and `theme_footer` just before
</body> on every page; the CSS/JS themselves are scoped to /scoreboard
only (see ctfd-theme/README.md), so this is safe to apply site-wide.

Re-run after every fresh CTFd setup (and after any `docker compose
down -v`, which wipes the config table along with everything else in
MariaDB) — this script is the single source of truth, not the Admin
UI.
"""

import sys
import requests
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
THEME_DIR = ROOT_DIR / "ctfd-theme"


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
    print(" [IEEE AUSB CTF] Applying Scoreboard Projector Theme")
    print("==========================================================")

    css_file = THEME_DIR / "scoreboard-projector.css"
    js_file = THEME_DIR / "scoreboard-projector.js"
    if not css_file.exists() or not js_file.exists():
        print(f"[!] Missing theme source files in {THEME_DIR}")
        sys.exit(1)

    theme_header = f"<style id=\"projector-mode-style\">\n{css_file.read_text()}\n</style>"
    theme_footer = f"<script>\n{js_file.read_text()}\n</script>"

    env = load_env()
    token = env.get("CTFD_ADMIN_TOKEN", "")
    api_url = env.get("CTFD_API_URL", "http://localhost")

    if not token or token == "placeholder_generate_after_ctfd_first_run":
        print("[!] CTFD_ADMIN_TOKEN not set in .env — cannot apply theme live.")
        print("    Generate one from CTFd Admin -> Profile -> Access Tokens,")
        print("    add it to .env, then re-run: uv run ctf theme")
        sys.exit(1)

    print("[*] Pushing theme_header (CSS) via CTFd API...")
    header_ok = set_config(api_url, token, "theme_header", theme_header)
    print("[*] Pushing theme_footer (JS) via CTFd API...")
    footer_ok = set_config(api_url, token, "theme_footer", theme_footer)

    if header_ok and footer_ok:
        print("[+] Scoreboard projector theme applied successfully!")
        print("    Open /scoreboard on the projector and press F11 for fullscreen.")
    else:
        print("[!] Failed to apply one or both configs. Check CTFD_ADMIN_TOKEN and CTFD_API_URL.")
        sys.exit(1)


if __name__ == "__main__":
    main()
