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

def ensure_ollama(model="smollm2"):
    """Ensure Ollama daemon is running and required local model is pulled."""
    console.print(f"[bold cyan][*] Checking Ollama AI service and model '{model}'...[/bold cyan]")
    ollama_bin = shutil.which("ollama")
    if not ollama_bin:
        console.print("[yellow][!] Ollama binary not found on PATH. Attempting install...[/yellow]")
        try:
            res = subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True)
            if res.returncode != 0:
                console.print("[bold red][!] Ollama installation failed. Please install from https://ollama.com[/bold red]")
                return False
            ollama_bin = shutil.which("ollama")
        except Exception as e:
            console.print(f"[bold red][!] Ollama auto-install failed: {e}[/bold red]")
            return False

    daemon_running = False
    data = {}
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            daemon_running = True
    except Exception:
        daemon_running = False

    if not daemon_running:
        console.print("[yellow][*] Ollama daemon not reachable. Attempting to start daemon...[/yellow]")
        if shutil.which("systemctl"):
            subprocess.run(["sudo", "systemctl", "start", "ollama"], capture_output=True)
        time.sleep(2)
        try:
            req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                daemon_running = True
        except Exception:
            try:
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(3)
                req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    data = json.loads(resp.read().decode())
                    daemon_running = True
            except Exception as e:
                console.print(f"[bold red][!] Could not start Ollama daemon: {e}[/bold red]")
                return False

    existing_models = [m.get("name", "") for m in data.get("models", [])]
    has_model = any(m == model or m.startswith(f"{model}:") for m in existing_models)
    if not has_model:
        console.print(f"[yellow][*] Model '{model}' not found in Ollama. Pulling model...[/yellow]")
        res = subprocess.run(["ollama", "pull", model])
        if res.returncode != 0:
            console.print(f"[bold red][!] Failed to pull '{model}'.[/bold red]")
            return False
        console.print(f"[bold green][+] Model '{model}' successfully pulled![/bold green]")
    else:
        console.print(f"[bold green][+] Ollama daemon active and model '{model}' is verified.[/bold green]")
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

    lan_ip = detect_lan_ip()
    port = os.getenv("HOST_PORT", "80")

    table = Table(title="Live Connection Endpoints", style="bold green")
    table.add_column("Access Type", style="cyan")
    table.add_column("URL", style="bold white")
    table.add_row("Local Machine", f"http://localhost:{port}")
    table.add_row("Participant LAN URL", f"http://{lan_ip}:{port}")
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

def cmd_sync(target_ip, user="manas", remote_path=None):
    """Sync latest snapshot to the standby laptop over LAN."""
    archive = cmd_backup()
    if not archive:
        return
    if not remote_path:
        remote_path = f"/home/{user}/Desktop/MID_SEM_LEAK_CTF"

    console.print(f"[bold cyan][*] Transferring {archive.name} to {user}@{target_ip}:{remote_path}/backups/...[/bold cyan]")
    # Ensure remote directory exists
    subprocess.run(["ssh", "-o", "ConnectTimeout=5", f"{user}@{target_ip}", f"mkdir -p '{remote_path}/backups'"])
    res = subprocess.run(["scp", str(archive), f"{user}@{target_ip}:{remote_path}/backups/"])
    if res.returncode == 0:
        console.print("[bold green][+] Sync complete! Standby laptop is ready for instant recovery.[/bold green]")
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

def cmd_wheel():
    """Display and launch Big-Screen Projector Spin Wheel."""
    lan_ip = detect_lan_ip()
    port = os.getenv("HOST_PORT", "80")
    wheel_url = f"http://{lan_ip}:{port}/spin-wheel/"
    local_url = f"http://localhost:{port}/spin-wheel/"
    file_path = ROOT_DIR / "tools" / "spin_wheel" / "index.html"

    table = Table(title="Interactive Projector Spin Wheel (Issue #25)", style="bold cyan")
    table.add_column("Display Mode", style="cyan")
    table.add_column("Location / URL", style="bold white")
    table.add_row("Lab Projector LAN URL", wheel_url)
    table.add_row("Local Browser URL", local_url)
    table.add_row("Standalone File", str(file_path))
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
    sync_p.add_argument("user", nargs="?", default="manas", help="SSH username (default: manas)")
    sync_p.add_argument("path", nargs="?", default=None, help="Remote project path")

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
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
