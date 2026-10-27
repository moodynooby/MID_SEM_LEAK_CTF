#!/usr/bin/env python3
"""
Participant & Team Import Utility for CTFd
Case File: The Mid-Sem Leak — IEEE AUSB CTF 2026

Parses Google Form registration responses CSV, validates participants & teams,
handles branching forms (CTF / Both / Talk only), cleans placeholder values,
resolves unformed/solo teams, imports accounts into CTFd, flushes Redis cache,
and exports a printable credentials dossier for event check-in desks.
"""

import os
import sys
import re
import csv
import json
import argparse
import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()
ROOT_DIR = Path(__file__).resolve().parent.parent

DEFAULT_CSV_NAME = "Case Files - Registration Form Responses - Form Responses 1.csv"
PLACEHOLDER_VALUES = {
    "", ".", "..", "...", "na", "n/a", "none", "null", "nil", "no", "-", "--", "tbd"
}


def normalize_str(val: str) -> str:
    if val is None:
        return ""
    return re.sub(r"\s+", " ", str(val)).strip()


def is_placeholder(val: str) -> bool:
    if not val:
        return True
    return normalize_str(val).lower() in PLACEHOLDER_VALUES


def is_unformed_team_name(val: str) -> bool:
    if is_placeholder(val):
        return True
    v = normalize_str(val).lower()
    indicators = [
        "dont know", "don't know", "will form", "form there", "at event",
        "solo", "individual", "not decided", "to be decided"
    ]
    return any(ind in v for ind in indicators)


def is_valid_email(val: str) -> bool:
    if is_placeholder(val):
        return False
    v = normalize_str(val)
    if "@" not in v:
        return False
    parts = v.split("@")
    if len(parts) != 2 or not parts[0] or "." not in parts[1]:
        return False
    return len(v) >= 5


def clean_phone(val: str) -> str:
    v = normalize_str(val)
    if is_placeholder(v):
        return ""
    # Strip any country codes like +91 or non-digits
    digits = re.sub(r"\D", "", v)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    return digits or v


def generate_team_slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")
    return slug[:16] if slug else "team"


def parse_registration_csv(csv_path: Path, include_talk_only: bool = False, default_pwd: str = "case2026!"):
    """
    Parses Google Forms CSV with multiple branching columns for CTF and Both.
    Returns: (teams_list, talk_only_list, stats)
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Registration CSV not found: {csv_path}")

    with open(csv_path, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        try:
            raw_header = next(reader)
        except StopIteration:
            return [], [], {"total_rows": 0, "ctf_teams": 0, "talk_only": 0}

        headers = [normalize_str(h).lower() for h in raw_header]

        # Dynamic column index resolution
        email_col = next((i for i, h in enumerate(headers) if "email address" in h or h == "email"), 1)
        name_col = next((i for i, h in enumerate(headers) if "your name?" in h or h == "name"), 2)
        phone_col = next((i for i, h in enumerate(headers) if "phone" in h), 3)
        choice_col = next((i for i, h in enumerate(headers) if "talk or the competition" in h or "joining" in h), 4)

        # Team name columns (Google Forms creates separate columns per branch)
        team_cols = [i for i, h in enumerate(headers) if "team's name" in h or "team name" in h]

        rows = list(reader)

    parsed_teams = []
    talk_only_attendees = []
    seen_emails = set()
    used_team_names = set()

    for row_idx, row in enumerate(rows, start=1):
        def get_val(idx):
            return row[idx].strip() if idx < len(row) else ""

        email = get_val(email_col).lower()
        name = get_val(name_col)
        phone = clean_phone(get_val(phone_col))
        choice = get_val(choice_col)

        if not email and not name:
            continue

        is_ctf_participant = ("competition" in choice.lower()) or ("both" in choice.lower())

        if not is_ctf_participant and not include_talk_only:
            talk_only_attendees.append({
                "row": row_idx,
                "name": name,
                "email": email,
                "phone": phone,
                "choice": choice
            })
            continue

        # Extract Team details based on branch columns
        # In this form:
        # Branch 1 (CTF competition): Team col 7, Members col 8-13, Phones col 27, 25, 26
        # Branch 2 (Both): Team col 14, Members col 15-20, Phones col 22, 23, 24
        raw_team_name = ""
        member_candidates = []

        # Find which branch has populated team info
        t14 = get_val(14) if len(row) > 14 else ""
        t7 = get_val(7) if len(row) > 7 else ""

        if t14 and not is_placeholder(t14):
            raw_team_name = t14
            member_candidates = [
                (get_val(15), get_val(16), get_val(22)),
                (get_val(17), get_val(18), get_val(23)),
                (get_val(19), get_val(20), get_val(24)),
            ]
        elif t7 and not is_placeholder(t7):
            raw_team_name = t7
            member_candidates = [
                (get_val(8), get_val(9), get_val(27)),
                (get_val(10), get_val(11), get_val(25)),
                (get_val(12), get_val(13), get_val(26)),
            ]
        else:
            # Fallback when team name is placeholder (e.g. NA or Don't know)
            raw_team_name = t14 or t7
            # Inspect both member sets
            m_set_2 = [
                (get_val(15), get_val(16), get_val(22)),
                (get_val(17), get_val(18), get_val(23)),
                (get_val(19), get_val(20), get_val(24)),
            ]
            m_set_1 = [
                (get_val(8), get_val(9), get_val(27)),
                (get_val(10), get_val(11), get_val(25)),
                (get_val(12), get_val(13), get_val(26)),
            ]
            has_valid_m2 = any(not is_placeholder(m[0]) and is_valid_email(m[1]) for m in m_set_2)
            member_candidates = m_set_2 if has_valid_m2 else m_set_1

        # Clean members
        valid_members = []
        for m_name, m_email, m_phone in member_candidates:
            m_name = normalize_str(m_name)
            m_email = normalize_str(m_email).lower()
            m_phone = clean_phone(m_phone)
            if not is_placeholder(m_name) and is_valid_email(m_email):
                if m_email not in seen_emails and m_email != email:
                    seen_emails.add(m_email)
                    valid_members.append({
                        "name": m_name,
                        "email": m_email,
                        "phone": m_phone,
                        "password": default_pwd,
                        "role": "Member"
                    })

        # Sanitize Team Name
        if is_unformed_team_name(raw_team_name):
            candidate_team_name = f"Team {name}".strip() if name else f"Team {email.split('@')[0]}"
        else:
            candidate_team_name = normalize_str(raw_team_name)

        # Ensure unique team name
        unique_team_name = candidate_team_name
        counter = 2
        while unique_team_name.lower() in used_team_names:
            unique_team_name = f"{candidate_team_name} {counter}"
            counter += 1
        used_team_names.add(unique_team_name.lower())

        # Generate credentials
        team_slug = generate_team_slug(unique_team_name)
        team_password = f"{default_pwd}_{team_slug}" if default_pwd.endswith("!") else f"{default_pwd}_{team_slug}"
        # Keep team password clean
        team_password = f"{default_pwd}"

        captain_dict = {
            "name": name or email.split("@")[0],
            "email": email,
            "phone": phone,
            "password": default_pwd,
            "role": "Captain"
        }
        seen_emails.add(email)

        parsed_teams.append({
            "row": row_idx,
            "team_name": unique_team_name,
            "raw_team_name": raw_team_name,
            "choice": choice or ("CTF" if is_ctf_participant else "Talk"),
            "team_password": team_password,
            "captain": captain_dict,
            "members": valid_members,
            "total_members": 1 + len(valid_members)
        })

    stats = {
        "total_rows": len(rows),
        "ctf_teams": len(parsed_teams),
        "total_participants": sum(t["total_members"] for t in parsed_teams),
        "talk_only": len(talk_only_attendees)
    }

    return parsed_teams, talk_only_attendees, stats


def execute_import_in_ctfd(teams_payload: list, default_pwd: str = "case2026!"):
    """
    Executes team & user creation inside CTFd container using native CTFd ORM models.
    """
    python_script = """
import sys
import json
from CTFd.models import db, Users, Teams
from CTFd import create_app

payload = json.loads(sys.stdin.read())
app = create_app()

results = {
    "teams_created": 0,
    "teams_updated": 0,
    "users_created": 0,
    "users_updated": 0,
    "errors": []
}

with app.app_context():
    for t_data in payload:
        tname = t_data["team_name"]
        tpwd = t_data["team_password"]
        captain_data = t_data["captain"]
        members_data = t_data["members"]

        # 1. Get or create Captain user
        cap_user = Users.query.filter_by(email=captain_data["email"]).first()
        if not cap_user:
            cap_user = Users(
                name=captain_data["name"],
                email=captain_data["email"],
                password=captain_data["password"],
                type="user",
                verified=True,
                hidden=False,
                banned=False
            )
            if captain_data.get("phone"):
                cap_user.affiliation = f"Phone: {captain_data['phone']}"
            db.session.add(cap_user)
            db.session.flush()
            results["users_created"] += 1
        else:
            cap_user.name = captain_data["name"]
            if captain_data.get("phone"):
                cap_user.affiliation = f"Phone: {captain_data['phone']}"
            results["users_updated"] += 1

        # 2. Get or create Team
        team = Teams.query.filter_by(name=tname).first()
        if not team:
            team = Teams(
                name=tname,
                password=tpwd,
                captain_id=cap_user.id,
                hidden=False,
                banned=False
            )
            db.session.add(team)
            db.session.flush()
            results["teams_created"] += 1
        else:
            team.captain_id = cap_user.id
            results["teams_updated"] += 1

        # Associate captain with team
        cap_user.team_id = team.id

        # 3. Get or create Members
        for m in members_data:
            m_user = Users.query.filter_by(email=m["email"]).first()
            if not m_user:
                m_user = Users(
                    name=m["name"],
                    email=m["email"],
                    password=m["password"],
                    type="user",
                    verified=True,
                    hidden=False,
                    banned=False
                )
                if m.get("phone"):
                    m_user.affiliation = f"Phone: {m['phone']}"
                db.session.add(m_user)
                db.session.flush()
                results["users_created"] += 1
            else:
                m_user.name = m["name"]
                if m.get("phone"):
                    m_user.affiliation = f"Phone: {m['phone']}"
                results["users_updated"] += 1
            m_user.team_id = team.id

    db.session.commit()

print("JSON_RESULT:" + json.dumps(results))
"""

    res = subprocess.run(
        ["docker", "exec", "-i", "ctfd_app", "python", "-c", python_script],
        input=json.dumps(teams_payload),
        text=True,
        capture_output=True
    )

    if res.returncode != 0:
        raise RuntimeError(f"CTFd internal error during participant import:\n{res.stderr.strip()}")

    # Extract JSON_RESULT
    for line in res.stdout.splitlines():
        if line.startswith("JSON_RESULT:"):
            return json.loads(line[len("JSON_RESULT:"):])

    return {"raw_output": res.stdout}


def flush_redis_cache():
    """Flushes Redis cache so all created teams and users appear immediately in CTFd."""
    cmd = ["docker", "exec", "-i", "ctfd_cache", "redis-cli", "FLUSHALL"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode == 0


def export_credentials_csv(teams: list, out_path: Path):
    """Exports credentials dossier CSV for check-in desks."""
    fieldnames = [
        "Team Name", "Team Password", "Role", "Participant Name",
        "Email", "Phone", "Login Password", "Registration Choice"
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in teams:
            tname = t["team_name"]
            tpwd = t["team_password"]
            choice = t["choice"]
            # Captain
            c = t["captain"]
            writer.writerow({
                "Team Name": tname,
                "Team Password": tpwd,
                "Role": c["role"],
                "Participant Name": c["name"],
                "Email": c["email"],
                "Phone": c["phone"],
                "Login Password": c["password"],
                "Registration Choice": choice
            })
            # Members
            for m in t["members"]:
                writer.writerow({
                    "Team Name": tname,
                    "Team Password": tpwd,
                    "Role": m["role"],
                    "Participant Name": m["name"],
                    "Email": m["email"],
                    "Phone": m["phone"],
                    "Login Password": m["password"],
                    "Registration Choice": choice
                })


def print_summary_table(teams: list, stats: dict, dry_run: bool = False):
    table = Table(
        title=f"Participant Import Roster {'[DRY RUN PREVIEW]' if dry_run else '[LIVE IMPORT]'}",
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("No.", style="dim", width=4)
    table.add_column("Team Name", style="bold green", min_width=20)
    table.add_column("Captain (Email / Phone)", style="cyan", min_width=30)
    table.add_column("Team Members (Count)", style="yellow", min_width=30)
    table.add_column("Credentials", style="bold white", min_width=18)

    for idx, t in enumerate(teams, start=1):
        c = t["captain"]
        cap_str = f"{c['name']}\n[dim]{c['email']}[/dim]\n[dim]📞 {c['phone'] or 'N/A'}[/dim]"

        if t["members"]:
            m_lines = []
            for m in t["members"]:
                m_lines.append(f"• {m['name']} ({m['email']})")
            members_str = f"[bold]{len(t['members']) + 1} players[/bold]\n" + "\n".join(m_lines)
        else:
            members_str = "[italic dim]1 player (Solo/Forming)[/italic dim]"

        cred_str = f"User Pwd: [cyan]{c['password']}[/cyan]\nTeam Pwd: [yellow]{t['team_password']}[/yellow]"
        table.add_row(str(idx), t["team_name"], cap_str, members_str, cred_str)

    console.print(table)

    stats_panel = Panel.fit(
        f"[bold white]Total Responses Processed:[/bold white] {stats['total_rows']}\n"
        f"[bold green]CTF Teams Identified:[/bold green] {stats['ctf_teams']}\n"
        f"[bold cyan]Total Active Competitors:[/bold cyan] {stats['total_participants']}\n"
        f"[bold yellow]Talk-Only Attendees (Skipped):[/bold yellow] {stats['talk_only']}",
        title="Registration Intake Metrics"
    )
    console.print(stats_panel)


def main():
    parser = argparse.ArgumentParser(
        description="IEEE AUSB CTF Participant Import Utility",
        epilog="Imports registration responses into CTFd teams and users."
    )
    parser.add_argument(
        "--csv",
        default=str(ROOT_DIR / DEFAULT_CSV_NAME),
        help=f"Path to registration responses CSV (Default: {DEFAULT_CSV_NAME})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and preview teams without modifying CTFd database"
    )
    parser.add_argument(
        "--include-talk-only",
        action="store_true",
        help="Also import participants who registered for 'The Expert Talk only'"
    )
    parser.add_argument(
        "--default-password",
        default="case2026!",
        help="Default login password for imported users and teams (Default: case2026!)"
    )
    parser.add_argument(
        "--export-credentials",
        default=str(ROOT_DIR / "participants_credentials.csv"),
        help="Output CSV path for team credential cards dossier"
    )

    args = parser.parse_args()
    csv_path = Path(args.csv)

    if not csv_path.exists():
        console.print(f"[bold red][!] File not found: {csv_path}[/bold red]")
        sys.exit(1)

    console.print(Panel.fit(
        f"[bold cyan]Case File: The Mid-Sem Leak — Participant Onboarding Utility[/bold cyan]\n"
        f"Input CSV: [bold white]{csv_path.name}[/bold white]\n"
        f"Mode: {'[yellow]DRY RUN (Read Only)[/yellow]' if args.dry_run else '[green]LIVE DATABASE IMPORT[/green]'}",
        title="IEEE AUSB Operations"
    ))

    teams, talk_only, stats = parse_registration_csv(
        csv_path,
        include_talk_only=args.include_talk_only,
        default_pwd=args.default_password
    )

    print_summary_table(teams, stats, dry_run=args.dry_run)

    # Always generate the credentials dossier for convenience
    export_path = Path(args.export_credentials)
    export_credentials_csv(teams, export_path)
    console.print(f"[bold green]✓ Credentials dossier exported to:[/bold green] [white]{export_path}[/white]")

    if args.dry_run:
        console.print("[yellow][*] Dry-run completed. No database changes were made.[/yellow]")
        return

    console.print("[bold cyan][*] Inserting teams and participants into CTFd...[/bold cyan]")
    try:
        results = execute_import_in_ctfd(teams, default_pwd=args.default_password)
        console.print(Panel.fit(
            f"[bold green]✓ CTFd Database Sync Complete![/bold green]\n"
            f"Teams Created: [bold white]{results.get('teams_created', 0)}[/bold white]\n"
            f"Teams Updated: [bold white]{results.get('teams_updated', 0)}[/bold white]\n"
            f"Users Created: [bold white]{results.get('users_created', 0)}[/bold white]\n"
            f"Users Updated: [bold white]{results.get('users_updated', 0)}[/bold white]",
            title="Import Results"
        ))

        # Flush cache
        if flush_redis_cache():
            console.print("[bold green]✓ Redis session & model cache successfully flushed.[/bold green]")
        else:
            console.print("[yellow][!] Warning: Redis cache flush returned non-zero exit code.[/yellow]")

    except Exception as e:
        console.print(f"[bold red][!] Failed to import into CTFd: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
