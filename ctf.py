#!/usr/bin/env python3
"""
Multiplatform CTF Management CLI (Linux / macOS / Windows)
Powered by uv and Docker Compose
IEEE AUSB: Case File: The Mid-Sem Leak — 28/10/2026

Usage:
  uv run ctf start             - Launch CTFd stack & detect LAN IP
  uv run ctf stop              - Gracefully stop containers
  uv run ctf status            - Show container health & connection info
  uv run ctf backup            - Create timestamped DB + file snapshot (Cross-platform)
  uv run ctf restore [archive] - Restore database & uploads (for standby laptop)
  uv run ctf sync <ip> [user]  - Push snapshot to standby laptop over LAN
  uv run ctf events            - Interactive live-event timeline console
  uv run ctf blackout          - 5:15 PM Scoreboard Freeze (Suspense mode)
  uv run ctf reveal            - 5:30 PM Scoreboard Reveal (Awards ceremony)
  uv run ctf theme             - Apply big-screen scoreboard projector theme
  uv run ctf seed              - Seed all challenges, flags, attachments & dynamic scoring into CTFd
  uv run ctf import [csv]      - Import teams & participants from registration responses CSV
  uv run ctf setup             - One-shot full setup (DB, challenges, themes, and bindings)
"""

import os
import re
import sys
import time
import shutil
import tarfile
import socket
import argparse
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
import json
import urllib.request
import urllib.error
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
ROOT_DIR = Path(__file__).resolve().parent

def detect_compose_cmd():
    """Detect docker compose, docker-compose, or podman compose across platforms."""
    if shutil.which("docker"):
        res = subprocess.run(["docker", "compose", "version"], capture_output=True)
        if res.returncode == 0:
            return ["docker", "compose"]
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    if shutil.which("podman-compose"):
        return ["podman-compose"]
    if shutil.which("podman"):
        res = subprocess.run(["podman", "compose", "version"], capture_output=True)
        if res.returncode == 0:
            return ["podman", "compose"]
    return None

def detect_container_cli():
    """Detect docker or podman CLI binary name."""
    if shutil.which("docker"):
        return "docker"
    if shutil.which("podman"):
        return "podman"
    return "docker"

def detect_lan_ip():
    """Cross-platform LAN IP detection."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def load_env():
    env_file = ROOT_DIR / ".env"
    env_vars = {}
    if not env_file.exists():
        example = ROOT_DIR / ".env.example"
        if example.exists():
            console.print("[yellow][!] .env not found. Creating from .env.example...[/yellow]")
            shutil.copy(example, env_file)
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars

def detect_bridge_ip():
    """Return the docker bridge gateway IP (where Ollama must listen).

    Containers reach the host through this address; loopback is not routable
    from inside a bridge network. The bridge can renumber, so never hardcode
    172.17.0.1.
    """
    try:
        res = subprocess.run(["ip", "-4", "-o", "addr", "show", "docker0"], capture_output=True, text=True)
        match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", res.stdout)
        if match:
            return match.group(1)
    except Exception:
        pass
    try:
        cli = detect_container_cli()
        if cli:
            res = subprocess.run(
                [cli, "network", "inspect", "bridge", "-f", "{{range .IPAM.Config}}{{.Gateway}}{{end}}"],
                capture_output=True, text=True,
            )
            gateway = res.stdout.strip()
            if gateway:
                return gateway
    except Exception:
        pass
    return "172.17.0.1"


def ollama_probe_urls():
    return [f"http://{detect_bridge_ip()}:11434", "http://127.0.0.1:11434"]


def _ollama_tags(url, timeout=3):
    req = urllib.request.Request(f"{url}/api/tags")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def ensure_ollama(model="smollm2"):
    """Ensure Ollama is running (bridge-bound) and the local model is pulled."""
    console.print(f"[bold cyan][*] Checking Ollama AI service and model '{model}'...[/bold cyan]")
    ollama_bin = shutil.which("ollama")
    if not ollama_bin:
        console.print(
            "[bold red][!] Ollama binary not found on PATH.[/bold red] "
            "Install it manually from https://ollama.com (no cloud auto-install at event time)."
        )
        return False

    data = None
    active_url = None
    for url in ollama_probe_urls():
        try:
            data = _ollama_tags(url)
            active_url = url
            break
        except Exception:
            continue

    if active_url is None:
        console.print("[yellow][*] Ollama daemon not reachable. Attempting to start daemon...[/yellow]")
        if shutil.which("systemctl"):
            subprocess.run(["sudo", "systemctl", "start", "ollama"], capture_output=True)
            time.sleep(2)
            for url in ollama_probe_urls():
                try:
                    data = _ollama_tags(url)
                    active_url = url
                    break
                except Exception:
                    continue
        if active_url is None:
            bridge = detect_bridge_ip()
            try:
                env = dict(os.environ, OLLAMA_HOST=f"{bridge}:11434")
                subprocess.Popen(
                    ["ollama", "serve"],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(3)
                data = _ollama_tags(f"http://{bridge}:11434")
                active_url = f"http://{bridge}:11434"
            except Exception as exc:
                console.print(f"[bold red][!] Could not start Ollama daemon: {exc}[/bold red]")
                return False

    # `ollama pull` honours OLLAMA_HOST; point the CLI at the daemon we found,
    # otherwise it defaults to 127.0.0.1 and fails once we bind the bridge.
    cli_host = active_url.replace("http://", "")
    cli_env = dict(os.environ, OLLAMA_HOST=cli_host)

    existing_models = [m.get("name", "") for m in data.get("models", [])]
    has_model = any(m == model or m.startswith(f"{model}:") for m in existing_models)
    if not has_model:
        console.print(f"[yellow][*] Model '{model}' not found in Ollama. Pulling model...[/yellow]")
        res = subprocess.run(["ollama", "pull", model], env=cli_env)
        if res.returncode != 0:
            console.print(f"[bold red][!] Failed to pull '{model}'.[/bold red]")
            return False
        console.print(f"[bold green][+] Model '{model}' successfully pulled![/bold green]")
    else:
        console.print(f"[bold green][+] Ollama daemon active on {cli_host} and model '{model}' is verified.[/bold green]")

    if not active_url.startswith(f"http://{detect_bridge_ip()}"):
        console.print(
            "[bold yellow][!] Ollama is not bound to the docker bridge. Containers cannot reach "
            f"{active_url}. Set OLLAMA_HOST={detect_bridge_ip()}:11434 and restart ollama, "
            "or challenge 5002 will fall back to regex heuristics.[/bold yellow]"
        )
    return True

def cmd_start():
    compose = detect_compose_cmd()
    if not compose:
        console.print("[bold red][ERROR] No container engine found![/bold red]")
        console.print("Please install Docker:")
        console.print("  • Official Docker Website: [bold cyan]https://docs.docker.com/get-started/get-docker/[/bold cyan]")
        console.print("  • Ubuntu / Debian Linux:  [bold cyan]https://docs.docker.com/engine/install/ubuntu/[/bold cyan]")
        sys.exit(1)

    load_env()
    ensure_ollama("smollm2")
    console.print(Panel.fit(
        f"[bold blue]Starting CTFd Container Stack[/bold blue]\nEngine: [green]{' '.join(compose)}[/green]",
        title="IEEE AUSB — Case File: The Mid-Sem Leak"
    ))

    cmd = compose + ["up", "-d"]
    subprocess.run(cmd, cwd=str(ROOT_DIR))

    ensure_ops_server()
    lan_ip = detect_lan_ip()
    port = os.getenv("HOST_PORT", "80")

    table = Table(title="Live Connection Endpoints", style="bold green")
    table.add_column("Access Type", style="cyan")
    table.add_column("URL", style="bold white")
    table.add_row("Local Machine", f"http://localhost:{port}")
    table.add_row("Participant LAN URL", f"http://{lan_ip}:{port}")
    table.add_row("Master Live Ops Cockpit", f"http://{lan_ip}:{port}/av-console/")
    console.print(table)

def cmd_stop():
    compose = detect_compose_cmd()
    if not compose:
        console.print("[red]Container engine not found.[/red]")
        return
    console.print("[yellow]Stopping CTFd containers...[/yellow]")
    subprocess.run(compose + ["down"], cwd=str(ROOT_DIR))
    console.print("[green][+] All containers stopped.[/green]")

def cmd_status():
    compose = detect_compose_cmd()
    if not compose:
        console.print("[red]Container engine not found.[/red]")
        return
    console.print(Panel.fit("[bold cyan]Container Stack Status[/bold cyan]"))
    subprocess.run(compose + ["ps"], cwd=str(ROOT_DIR))
    _anubis_cookie_check()
    _ollama_bind_check()
    _challenge_endpoint_check()


def _ollama_bind_check():
    """The AI challenge only works when Ollama listens on the docker bridge."""
    bridge = detect_bridge_ip()
    try:
        _ollama_tags(f"http://{bridge}:11434", timeout=2)
        console.print(f"[green][+] Ollama reachable from containers at {bridge}:11434.[/green]")
        return
    except Exception:
        pass
    try:
        _ollama_tags("http://127.0.0.1:11434", timeout=2)
        console.print(
            f"[bold red][!] Ollama is loopback-only. Containers cannot reach it — challenge 5002 "
            f"will use the heuristic fallback. Set OLLAMA_HOST={bridge}:11434 and restart ollama.[/bold red]"
        )
    except Exception:
        console.print("[yellow][!] Ollama daemon not reachable on loopback or bridge (challenge 5002 degraded).[/yellow]")


def _challenge_endpoint_check():
    """Probe the three hosted challenge services (5001/5002/5003)."""
    table = Table(title="Hosted Challenge Services", style="bold green")
    table.add_column("Port", style="cyan")
    table.add_column("Challenge", style="white")
    table.add_column("HTTP", style="bold white")
    services = [(5001, "cookie_api"), (5002, "ai_prompt_injection"), (5003, "php2shell")]
    for port, name in services:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/", headers={"User-Agent": "ctf-status-check"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                status = f"{resp.status} OK"
        except Exception as exc:
            status = f"[red]DOWN ({exc.__class__.__name__})[/red]"
        table.add_row(str(port), name, status)
    console.print(table)


def _anubis_cookie_check():
    """Guard against the plain-HTTP Anubis cookie loop (Secure/Partitioned flags).

    Anubis v1.28+ defaults to cookie-secure/partitioned = true. Over http:// the
    browser silently drops those cookies and every participant loops on
    "user has cookies disabled", so the flags are pinned in docker-compose.yml.
    """
    port = load_env().get("HOST_PORT", "80")
    url = f"http://127.0.0.1:{port}/"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ctf-status-check"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            cookies = resp.headers.get_all("Set-Cookie") or []
    except Exception as exc:  # stack down / port busy / Anubis not answering
        console.print(f"[yellow][!] Anubis cookie probe skipped: {exc}[/yellow]")
        return

    if not cookies:
        console.print("[yellow][!] Anubis cookie probe: no Set-Cookie seen (already authenticated?)[/yellow]")
        return

    insecure_ok = not any("secure" in c.lower() or "partitioned" in c.lower() for c in cookies)
    if insecure_ok:
        console.print("[green][+] Anubis cookies are plain-HTTP safe (no Secure/Partitioned flags).[/green]")
    else:
        console.print(
            "[bold red][!] Anubis is setting Secure/Partitioned cookies over http:// — "
            "participants will loop on 'user has cookies disabled'. "
            "Set COOKIE_SECURE=false and COOKIE_PARTITIONED=false, then "
            "'docker compose up -d --force-recreate --no-deps anubis'.[/bold red]"
        )

def cmd_backup():
    """Cross-platform backup of MariaDB and CTFd uploads into a compressed tarball."""
    cli = detect_container_cli()
    env = load_env()
    user = env.get("MYSQL_USER", "ctfd")
    password = env.get("MYSQL_PASSWORD", "ctfd_secure_pass")
    db_name = env.get("MYSQL_DATABASE", "ctfd")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backups_dir = ROOT_DIR / "backups"
    backups_dir.mkdir(exist_ok=True)
    archive_path = backups_dir / f"ctfd_backup_{timestamp}.tar.gz"

    console.print(f"[bold cyan][*] Creating CTFd backup snapshot: {timestamp}[/bold cyan]")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        sql_file = tmp_path / "database.sql"
        uploads_dir = tmp_path / "uploads"
        uploads_dir.mkdir(exist_ok=True)

        # 1. Export MariaDB dump
        console.print(f"[*] Dumping database '{db_name}'...")
        dump_cmd = [
            cli, "exec", "ctfd_db", "mariadb-dump",
            f"-u{user}", f"-p{password}",
            "--single-transaction", "--quick", db_name
        ]
        with open(sql_file, "w") as f:
            res = subprocess.run(dump_cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            if res.returncode != 0:
                console.print(f"[bold red][!] Dump failed: {res.stderr}[/bold red]")
                return None

        # 2. Copy uploads from container
        console.print("[*] Copying uploaded challenge attachments...")
        subprocess.run([cli, "cp", "ctfd_app:/var/uploads/.", str(uploads_dir)], capture_output=True)

        # 3. Create compressed tarball
        console.print(f"[*] Compressing into archive: [bold white]{archive_path.name}[/bold white]...")
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(sql_file, arcname="database.sql")
            tar.add(uploads_dir, arcname="uploads")

    size_mb = archive_path.stat().st_size / (1024 * 1024)
    console.print(Panel.fit(
        f"[bold green]✓ Backup successfully created![/bold green]\n"
        f"File: [bold white]{archive_path.name}[/bold white] ({size_mb:.2f} MB)\n"
        f"Path: {archive_path}",
        title="Backup Complete"
    ))
    return archive_path

def cmd_restore(archive_file=None):
    """Cross-platform restore of MariaDB and uploads onto primary or standby backup laptop."""
    backups_dir = ROOT_DIR / "backups"
    if not archive_file:
        archives = sorted(backups_dir.glob("ctfd_backup_*.tar.gz"), key=os.path.getmtime, reverse=True)
        if not archives:
            console.print("[bold red][!] No backup archives found in 'backups/' directory.[/bold red]")
            return
        archive_file = archives[0]
    else:
        archive_file = Path(archive_file)

    if not archive_file.exists():
        console.print(f"[bold red][!] Archive not found: {archive_file}[/bold red]")
        return

    cli = detect_container_cli()
    compose = detect_compose_cmd()
    env = load_env()
    user = env.get("MYSQL_USER", "ctfd")
    password = env.get("MYSQL_PASSWORD", "ctfd_secure_pass")
    db_name = env.get("MYSQL_DATABASE", "ctfd")

    console.print(f"[bold yellow][*] Restoring from archive: {archive_file.name}[/bold yellow]")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        console.print("[*] Extracting snapshot archive...")
        with tarfile.open(archive_file, "r:gz") as tar:
            tar.extractall(path=tmp_path)

        # Ensure db container is up
        console.print("[*] Ensuring MariaDB and Redis are running...")
        subprocess.run(compose + ["up", "-d", "db", "cache"], cwd=str(ROOT_DIR))
        time.sleep(4)

        # Import database
        sql_file = tmp_path / "database.sql"
        if sql_file.exists():
            console.print(f"[*] Importing database dump into MariaDB ({db_name})...")
            with open(sql_file, "r") as f:
                res = subprocess.run(
                    [cli, "exec", "-i", "ctfd_db", "mariadb", f"-u{user}", f"-p{password}", db_name],
                    stdin=f, capture_output=True, text=True
                )
                if res.returncode != 0:
                    console.print(f"[bold red][!] Database restore error: {res.stderr}[/bold red]")
                else:
                    console.print("[bold green][+] Database restored successfully.[/bold green]")

        # Launch entire stack
        subprocess.run(compose + ["up", "-d"], cwd=str(ROOT_DIR))

        # The AI challenge depends on a host-side model that is NOT part of the
        # backup archive. Without this the bot silently degrades to regex
        # heuristics on the standby laptop.
        if not ensure_ollama("smollm2"):
            console.print(
                "[bold yellow][!] Ollama/model unavailable: challenge 5002 will serve the "
                "deterministic heuristic fallback until the model is restored.[/bold yellow]"
            )

        # Restore uploads
        uploads_dir = tmp_path / "uploads"
        if uploads_dir.exists():
            console.print("[*] Restoring uploaded challenge files...")
            subprocess.run([cli, "cp", f"{uploads_dir}/.", "ctfd_app:/var/uploads/"], capture_output=True)
            subprocess.run([cli, "exec", "ctfd_app", "chown", "-R", "1001:1001", "/var/uploads"], capture_output=True)

        # Restart CTFd app container to flush cache
        subprocess.run([cli, "restart", "ctfd_app"], capture_output=True)

    console.print(Panel.fit(
        "[bold green]✓ Restoration Complete![/bold green]\n"
        "CTFd is fully live with all scores, teams, and challenges restored.",
        title="Standby Restore Successful"
    ))

def cmd_sync(target_ip, user=None, remote_path=None):
    """Sync latest snapshot to the standby laptop over LAN.

    No hardcoded username or absolute home path: on the standby, the repo lives
    wherever the operator cloned it. Override with --user / --remote-path.
    """
    import getpass

    user = user or os.getenv("CTF_SYNC_USER") or getpass.getuser()
    remote_path = remote_path or os.getenv("CTF_SYNC_PATH") or f"~/Desktop/MID_SEM_LEAK_CTF"
    archive = cmd_backup()
    if not archive:
        return

    console.print(f"[bold cyan][*] Transferring {archive.name} to {user}@{target_ip}:{remote_path}/backups/...[/bold cyan]")
    # Ensure remote directory exists
    subprocess.run(["ssh", "-o", "ConnectTimeout=5", f"{user}@{target_ip}", f"mkdir -p '{remote_path}/backups'"])
    res = subprocess.run(["scp", str(archive), f"{user}@{target_ip}:{remote_path}/backups/"])
    if res.returncode == 0:
        console.print("[bold green][+] Sync complete! Standby laptop is ready for instant recovery.[/bold green]")
        console.print(
            "[yellow][!] Snapshot contains DB + uploads only. The standby still needs the repo, "
            "the Ollama model, and php2shell uploads (teams re-upload after failover).[/yellow]"
        )
    else:
        console.print("[bold red][!] Sync failed. Check IP and SSH connectivity.[/bold red]")

def cmd_events(event_name=None):
    events_script = ROOT_DIR / "ops" / "manage_timed_events.py"
    if event_name:
        subprocess.run([sys.executable, str(events_script), "--event", event_name], cwd=str(ROOT_DIR))
    else:
        subprocess.run([sys.executable, str(events_script)], cwd=str(ROOT_DIR))

def cmd_blackout():
    script = ROOT_DIR / "ops" / "freeze_scoreboard.py"
    subprocess.run([sys.executable, str(script)], cwd=str(ROOT_DIR))

def cmd_reveal():
    script = ROOT_DIR / "ops" / "unfreeze_scoreboard.py"
    subprocess.run([sys.executable, str(script)], cwd=str(ROOT_DIR))

def cmd_theme():
    script = ROOT_DIR / "ops" / "apply_scoreboard_theme.py"
    subprocess.run([sys.executable, str(script)], cwd=str(ROOT_DIR))

def cmd_seed():
    script = ROOT_DIR / "ops" / "seed_challenges.py"
    subprocess.run([sys.executable, str(script)], cwd=str(ROOT_DIR))

def cmd_import(csv_path=None, dry_run=False, include_talk_only=False, default_password="case2026!", export_credentials=None):
    script = ROOT_DIR / "ops" / "import_participants.py"
    cmd = [sys.executable, str(script)]
    if csv_path:
        cmd.extend(["--csv", str(csv_path)])
    if dry_run:
        cmd.append("--dry-run")
    if include_talk_only:
        cmd.append("--include-talk-only")
    if default_password:
        cmd.extend(["--default-password", default_password])
    if export_credentials:
        cmd.extend(["--export-credentials", str(export_credentials)])
    subprocess.run(cmd, cwd=str(ROOT_DIR))

def cmd_setup():
    console.print(Panel.fit("[bold cyan]Executing Complete Automated CTF Setup...[/bold cyan]"))
    ensure_ollama("smollm2")
    cmd_seed()
    cmd_theme()
    console.print("[bold green][+] CTFd stack fully configured, challenges seeded, and themes bound![/bold green]")

def is_port_in_use(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

def ensure_ops_server():
    """Ensure background Ops Control API is running on localhost:8088."""
    if not is_port_in_use(8088):
        script = ROOT_DIR / "ops" / "control_server.py"
        subprocess.Popen(
            [sys.executable, str(script)],
            cwd=str(ROOT_DIR),
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

def cmd_console():
    """Display and launch Master Live Ops Cockpit & AV Console."""
    ensure_ops_server()
    lan_ip = detect_lan_ip()
    port = os.getenv("HOST_PORT", "80")
    console_url = f"http://{lan_ip}:{port}/av-console/"
    local_url = f"http://localhost:{port}/av-console/"

    table = Table(title="Master Live Ops Cockpit & AV Console (Merged Ops Center)", style="bold magenta")
    table.add_column("Display Mode", style="cyan")
    table.add_column("Location / URL", style="bold white")
    table.add_row("Lab Projector & Ops LAN URL", console_url)
    table.add_row("Local Browser URL", local_url)
    console.print(table)
    console.print("[green][+] Integrated Tools:[/green] [white]Countdown | Wheel | Soundboard | Siren | CLI-to-UI Controls[/white]")

def cmd_wheel():
    """Display and launch Big-Screen Projector Spin Wheel."""
    ensure_ops_server()
    lan_ip = detect_lan_ip()
    port = os.getenv("HOST_PORT", "80")
    wheel_url = f"http://{lan_ip}:{port}/av-console/#wheel"
    local_url = f"http://localhost:{port}/av-console/#wheel"

    table = Table(title="Interactive Projector Spin Wheel (Master Cockpit)", style="bold cyan")
    table.add_column("Display Mode", style="cyan")
    table.add_column("Location / URL", style="bold white")
    table.add_row("Lab Projector LAN URL", wheel_url)
    table.add_row("Local Browser URL", local_url)
    console.print(table)
    console.print("[green][+] Controls:[/green] [white]SPACE = Spin | R = Reset | M = Mute | F = Fullscreen[/white]")

def cmd_siren(once=False, test_team=None, reason=None):
    """Run real-time intrusion & decoy honeyflag monitor or trigger test alert."""
    script = ROOT_DIR / "ops" / "siren_alert" / "monitor.py"
    cmd = [sys.executable, str(script)]
    if test_team:
        cmd.extend(["--test", test_team])
        if reason:
            cmd.extend(["--reason", reason])
    elif once:
        cmd.append("--once")
    subprocess.run(cmd, cwd=str(ROOT_DIR))

def main():
    parser = argparse.ArgumentParser(
        description="IEEE AUSB Multiplatform CTF Manager",
        epilog="Powered by uv & Docker Compose"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    subparsers.add_parser("start", help="Start CTFd containers & show LAN URL")
    subparsers.add_parser("stop", help="Stop CTFd containers")
    subparsers.add_parser("status", help="Show container status")
    subparsers.add_parser("backup", help="Create DB & upload snapshot (cross-platform)")
    
    restore_p = subparsers.add_parser("restore", help="Restore latest backup")
    restore_p.add_argument("archive", nargs="?", help="Specific backup archive path (optional)")

    sync_p = subparsers.add_parser("sync", help="Sync snapshot to standby laptop over LAN")
    sync_p.add_argument("ip", help="Standby laptop LAN IP")
    sync_p.add_argument("user", nargs="?", default=None, help="SSH username (default: current user / $CTF_SYNC_USER)")
    sync_p.add_argument("path", nargs="?", default=None, help="Remote project path (default: ~/Desktop/MID_SEM_LEAK_CTF)")

    events_p = subparsers.add_parser("events", help="Manage timed events")
    events_p.add_argument("--event", choices=[
        "vanishing_start", "vanishing_end", "clue_drop_1",
        "lightning_start", "lightning_end", "clue_drop_2",
        "blackout", "reveal"
    ], help="Directly trigger a specific event")

    subparsers.add_parser("blackout", help="Trigger 5:15 PM scoreboard blackout")
    subparsers.add_parser("reveal", help="Trigger 5:30 PM closing reveal")
    subparsers.add_parser("theme", help="Apply big-screen scoreboard projector theme")
    subparsers.add_parser("seed", help="Seed challenges, flags, files, and theme into CTFd")

    import_p = subparsers.add_parser("import", aliases=["import-participants"], help="Import teams & participants from registration responses CSV")
    import_p.add_argument("csv", nargs="?", default=None, help="Path to registration CSV (optional)")
    import_p.add_argument("--dry-run", action="store_true", help="Preview import without touching database")
    import_p.add_argument("--include-talk-only", action="store_true", help="Also import talk-only participants")
    import_p.add_argument("--default-password", default="case2026!", help="Default password (default: case2026!)")
    import_p.add_argument("--export", dest="export_credentials", default=None, help="Export path for credentials dossier CSV")

    subparsers.add_parser("setup", help="One-shot full setup: configure DB, seed challenges, apply themes")
    subparsers.add_parser("ollama", help="Ensure local Ollama service and neural LLM model are ready")
    subparsers.add_parser("console", aliases=["ui", "deck", "cockpit"], help="Launch Master Live Ops Cockpit & AV Console")
    subparsers.add_parser("wheel", aliases=["spin"], help="Display Big-Screen Projector Spin Wheel URLs and controls")

    siren_p = subparsers.add_parser("siren", aliases=["monitor"], help="Run live intrusion & decoy honeyflag monitor daemon, or test alert")
    siren_p.add_argument("--once", action="store_true", help="Run single audit pass and exit")
    siren_p.add_argument("--test", nargs="?", const="Station 4 - HashCrashers", help="Trigger test siren alert for station")
    siren_p.add_argument("--reason", default="Decoy Honeyflag Triggered", help="Reason string for test alert")

    args = parser.parse_args()

    if args.command == "start":
        cmd_start()
    elif args.command == "stop":
        cmd_stop()
    elif args.command == "status":
        cmd_status()
    elif args.command == "backup":
        cmd_backup()
    elif args.command == "restore":
        cmd_restore(getattr(args, "archive", None))
    elif args.command == "sync":
        cmd_sync(args.ip, args.user, args.path)
    elif args.command == "events":
        cmd_events(getattr(args, "event", None))
    elif args.command == "blackout":
        cmd_blackout()
    elif args.command == "reveal":
        cmd_reveal()
    elif args.command == "theme":
        cmd_theme()
    elif args.command == "seed":
        cmd_seed()
    elif args.command in ["wheel", "spin"]:
        cmd_wheel()
    elif args.command in ["siren", "monitor"]:
        cmd_siren(once=args.once, test_team=args.test, reason=args.reason)
    elif args.command in ["import", "import-participants"]:
        cmd_import(
            csv_path=args.csv,
            dry_run=args.dry_run,
            include_talk_only=args.include_talk_only,
            default_password=args.default_password,
            export_credentials=args.export_credentials
        )
    elif args.command == "setup":
        cmd_setup()
    elif args.command == "ollama":
        ensure_ollama("smollm2")
    elif args.command in ["console", "ui", "deck", "cockpit"]:
        cmd_console()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
