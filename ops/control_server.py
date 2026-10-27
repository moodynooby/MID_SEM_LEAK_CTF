#!/usr/bin/env python3
"""
Lightweight Host Control API Server for CTF Master Console
IEEE AUSB: Case File: The Mid-Sem Leak

Provides local REST endpoints for host lifecycle commands:
  - GET  /api/ops/status  -> Docker container health + last backup info
  - POST /api/ops/backup  -> Triggers cmd_backup() snapshot creation
  - POST /api/ops/sync    -> Triggers cmd_sync(ip) to standby laptop
  - POST /api/ops/seed    -> Re-seeds challenges and flags
  - POST /api/ops/theme   -> Pushes scoreboard projector theme
  - POST /api/ops/siren   -> Triggers test intrusion alert

Binds to 127.0.0.1:8088 by default. Reverse-proxied via Nginx at /api/ops/.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import ctf  # Reuses unified ctf CLI methods

PORT = 8088

def verify_admin_password(candidate_password):
    """Verify candidate string against hashed CTFd admin passwords in MariaDB."""
    if not candidate_password:
        return False
    try:
        from passlib.hash import bcrypt_sha256
        cli = ctf.detect_container_cli()
        env = ctf.load_env()
        root_pass = env.get("MYSQL_ROOT_PASSWORD", "ieee_ausb_midsem_root_sec_2026!")
        cmd = [
            cli, "exec", "ctfd_db", "mariadb",
            "-uroot", f"-p{root_pass}", "ctfd",
            "-s", "-N", "-e", "SELECT password FROM users WHERE type='admin';"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        if res.returncode == 0:
            for line in res.stdout.strip().splitlines():
                pw_hash = line.strip()
                if pw_hash and bcrypt_sha256.verify(candidate_password, pw_hash):
                    return True
    except Exception as e:
        print("[!] verify_admin_password error:", e)
    return False

class OpsHandler(BaseHTTPRequestHandler):
    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Admin-Token")
        self.send_header("Access-Control-Allow-Credentials", "true")

    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self._send_cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def _is_authenticated(self):
        env = ctf.load_env()
        valid_tokens = set()

        admin_token = env.get("CTFD_ADMIN_TOKEN", "").strip()
        if admin_token and admin_token != "your_ctfd_admin_api_token_here" and admin_token != "placeholder_generate_after_ctfd_first_run":
            valid_tokens.add(admin_token)

        secret_key = env.get("SECRET_KEY", "").strip()
        if secret_key:
            valid_tokens.add(secret_key)

        ops_pin = env.get("OPS_CONSOLE_PIN", "").strip()
        if ops_pin:
            valid_tokens.add(ops_pin)

        auth_header = self.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        elif auth_header.startswith("Token "):
            token = auth_header[6:].strip()
        elif "X-Admin-Token" in self.headers:
            token = self.headers.get("X-Admin-Token", "").strip()

        if not token:
            query = parse_qs(urlparse(self.path).query)
            if "token" in query:
                token = query["token"][0].strip()

        if token and (token in valid_tokens or verify_admin_password(token)):
            return True

        # Check CTFd session cookie if present: /api/v1/configs returns 200 strictly for admins!
        cookie_header = self.headers.get("Cookie", "")
        if "session=" in cookie_header:
            try:
                import requests
                api_url = env.get("CTFD_API_URL", "http://localhost")
                r = requests.get(
                    f"{api_url.rstrip('/')}/api/v1/configs",
                    headers={"Cookie": cookie_header, "Accept": "application/json"},
                    timeout=2
                )
                if r.status_code == 200:
                    return True
            except Exception:
                pass

        return False

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path.rstrip("/")

        if path in ["/api/ops/ping", "/ping"]:
            self._send_json(200, {"status": "ok", "service": "midsem_ops_api"})
            return

        if not self._is_authenticated():
            self._send_json(401, {"error": "Unauthorized: Admin authorization token or session required."})
            return

        if path in ["/api/ops/status", "/status"]:
            self.handle_status()
        elif path in ["/api/ops/verify", "/verify"]:
            self._send_json(200, {"success": True, "authenticated": True})
        else:
            self._send_json(404, {"error": "Endpoint not found", "path": path})

    def do_POST(self):
        url = urlparse(self.path)
        path = url.path.rstrip("/")

        content_len = int(self.headers.get("Content-Length", 0))
        body = {}
        if content_len > 0:
            try:
                body = json.loads(self.rfile.read(content_len).decode("utf-8"))
            except Exception:
                pass

        # Handle login verification endpoint
        if path in ["/api/ops/verify", "/verify"]:
            provided_token = body.get("token") or body.get("pin", "") or body.get("password", "")
            env = ctf.load_env()
            valid = {
                env.get("CTFD_ADMIN_TOKEN", "").strip(),
                env.get("SECRET_KEY", "").strip(),
                env.get("OPS_CONSOLE_PIN", "").strip()
            }
            valid.discard("")
            valid.discard("your_ctfd_admin_api_token_here")
            valid.discard("placeholder_generate_after_ctfd_first_run")

            if (provided_token and provided_token in valid) or verify_admin_password(provided_token) or self._is_authenticated():
                self._send_json(200, {"success": True, "authenticated": True, "token": provided_token})
            else:
                self._send_json(401, {"success": False, "error": "Invalid administrator password or token."})
            return

        # All other POST endpoints require strict authentication
        if not self._is_authenticated():
            self._send_json(401, {"error": "Unauthorized: Admin authorization token or session required."})
            return

        if path in ["/api/ops/backup", "/backup"]:
            self.handle_backup()
        elif path in ["/api/ops/sync", "/sync"]:
            self.handle_sync(body)
        elif path in ["/api/ops/seed", "/seed"]:
            self.handle_seed()
        elif path in ["/api/ops/theme", "/theme"]:
            self.handle_theme()
        elif path in ["/api/ops/siren", "/siren"]:
            self.handle_siren(body)
        elif path in ["/api/ops/blackout", "/blackout"]:
            self.handle_blackout()
        elif path in ["/api/ops/reveal", "/reveal"]:
            self.handle_reveal()
        else:
            self._send_json(404, {"error": "Endpoint not found", "path": path})

    def handle_status(self):
        cli = ctf.detect_container_cli()
        compose = ctf.detect_compose_cmd()
        containers = {}

        if cli:
            for name in ["ctfd_app", "ctfd_proxy", "ctfd_db", "ctfd_cache", "ctfd_anubis"]:
                try:
                    res = subprocess.run(
                        [cli, "inspect", "--format", "{{.State.Status}}", name],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    containers[name] = res.stdout.strip() if res.returncode == 0 else "offline"
                except Exception:
                    containers[name] = "offline"

        backups_dir = ROOT_DIR / "backups"
        archives = sorted(backups_dir.glob("ctfd_backup_*.tar.gz"), key=os.path.getmtime, reverse=True) if backups_dir.exists() else []
        last_backup = archives[0].name if archives else None

        self._send_json(200, {
            "status": "ok",
            "containers": containers,
            "container_cli": cli,
            "last_backup": last_backup,
            "total_backups": len(archives),
            "lan_ip": ctf.detect_lan_ip()
        })

    def handle_backup(self):
        try:
            archive = ctf.cmd_backup()
            if archive and archive.exists():
                self._send_json(200, {
                    "success": True,
                    "message": f"Snapshot created: {archive.name}",
                    "filename": archive.name,
                    "size_bytes": archive.stat().st_size
                })
            else:
                self._send_json(500, {"success": False, "error": "Backup generation failed"})
        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})

    def handle_sync(self, body):
        target_ip = body.get("ip") or body.get("target_ip")
        user = body.get("user", "manas")
        if not target_ip:
            self._send_json(400, {"success": False, "error": "target_ip is required"})
            return

        try:
            ctf.cmd_sync(target_ip, user=user)
            self._send_json(200, {
                "success": True,
                "message": f"Snapshot synced to {user}@{target_ip}"
            })
        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})

    def handle_seed(self):
        try:
            ctf.cmd_seed()
            self._send_json(200, {"success": True, "message": "Challenges seeded successfully"})
        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})

    def handle_theme(self):
        try:
            ctf.cmd_theme()
            self._send_json(200, {"success": True, "message": "Scoreboard theme applied"})
        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})

    def handle_blackout(self):
        try:
            ctf.cmd_blackout()
            self._send_json(200, {"success": True, "message": "Scoreboard frozen in suspense blackout"})
        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})

    def handle_reveal(self):
        try:
            ctf.cmd_reveal()
            self._send_json(200, {"success": True, "message": "Scoreboard unfrozen for reveal"})
        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})

    def handle_siren(self, body):
        test_team = body.get("team", "Station 4 - HashCrashers")
        reason = body.get("reason", "Decoy Honeyflag Triggered")
        try:
            ctf.cmd_siren(test_team=test_team, reason=reason)
            self._send_json(200, {
                "success": True,
                "message": f"Test intrusion alert triggered for {test_team}"
            })
        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})

def run(port=PORT):
    server = HTTPServer(("0.0.0.0", port), OpsHandler)
    print(f"[*] CTF Ops Control API Server listening on http://0.0.0.0:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Stopping CTF Ops Control API Server...")
        server.server_close()

if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run(p)
