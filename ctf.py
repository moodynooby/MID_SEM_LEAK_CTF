#!/usr/bin/env python3
"""
Multiplatform CTF Management CLI (Linux / macOS / Windows)
Powered by uv and Docker Compose
IEEE AUSB: Case File: The Mid-Sem Leak — 28/10/2026

Usage:
  uv run ctf.py start      - Launch CTFd stack & detect LAN IP
  uv run ctf.py stop       - Gracefully stop containers
  uv run ctf.py status     - Show container health & connection info
  uv run ctf.py backup     - Create timestamped DB + file snapshot
  uv run ctf.py restore    - Restore latest backup (for standby laptop)
  uv run ctf.py events     - Interactive live-event timeline console
  uv run ctf.py blackout   - 5:15 PM Scoreboard Freeze (Suspense mode)
  uv run ctf.py reveal     - 5:30 PM Scoreboard Reveal (Awards ceremony)
"""

import os
import sys
import shutil
import socket
import argparse
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
ROOT_DIR = Path(__file__).resolve().parent

def detect_compose_cmd():
    """Detect docker compose, docker-compose, or podman compose across platforms."""
    # Check docker compose
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

def detect_lan_ip():
    """Cross-platform LAN IP detection."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't need to be reachable, just triggers local interface selection
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

def cmd_start():
    compose = detect_compose_cmd()
    if not compose:
        console.print("[bold red][ERROR] No container engine found![/bold red]")
        console.print("Please install Docker Desktop (Windows/macOS) or run [bold green]sudo ./install_docker.sh[/bold green] on Linux.")
        sys.exit(1)

    load_env()
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
    backup_sh = ROOT_DIR / "ops" / "backup.sh"
    if os.name != "nt" and backup_sh.exists():
        subprocess.run(["bash", str(backup_sh)], cwd=str(ROOT_DIR))
    else:
        # Cross-platform backup via python
        console.print("[yellow]Running cross-platform snapshot...[/yellow]")
        subprocess.run([sys.executable, str(ROOT_DIR / "ops" / "backup_runner.py")], cwd=str(ROOT_DIR))

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

def main():
    parser = argparse.ArgumentParser(
        description="IEEE AUSB Multiplatform CTF Manager",
        epilog="Powered by uv & Docker Compose"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    subparsers.add_parser("start", help="Start CTFd containers & show LAN URL")
    subparsers.add_parser("stop", help="Stop CTFd containers")
    subparsers.add_parser("status", help="Show container status")
    subparsers.add_parser("backup", help="Create DB & upload snapshot")
    subparsers.add_parser("restore", help="Restore latest backup")
    
    events_p = subparsers.add_parser("events", help="Manage timed events")
    events_p.add_argument("--event", choices=[
        "vanishing_start", "vanishing_end", "clue_drop_1",
        "lightning_start", "lightning_end", "clue_drop_2",
        "blackout", "reveal"
    ], help="Directly trigger a specific event")

    subparsers.add_parser("blackout", help="Trigger 5:15 PM scoreboard blackout")
    subparsers.add_parser("reveal", help="Trigger 5:30 PM closing reveal")

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
        subprocess.run(["bash", str(ROOT_DIR / "ops" / "restore.sh")], cwd=str(ROOT_DIR))
    elif args.command == "events":
        cmd_events(getattr(args, "event", None))
    elif args.command == "blackout":
        cmd_blackout()
    elif args.command == "reveal":
        cmd_reveal()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
