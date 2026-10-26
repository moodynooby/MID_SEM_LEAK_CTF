#!/usr/bin/env python3
"""
Seed & Orchestrate CTFd Challenges, Themes, and Assets
Case File: The Mid-Sem Leak — IEEE AUSB CTF 2026

Idempotent, offline-first seeder that:
  1. Configures CTFd core metadata (name, theme, user mode, setup status).
  2. Injects big-screen scoreboard projector styling into theme_header / theme_footer.
  3. Discovers all challenges from challenges/**/challenge.yml.
  4. Seeds challenges with dynamic scoring (500 initial / 15 decay / 100 min).
  5. Registers static flags, hints, and category tags.
  6. Copies challenge distribution files into /var/uploads/<sha1>/ and registers them in CTFd.
  7. Flushes Redis cache to ensure immediate live dashboard availability.
"""

import os
import sys
import yaml
import glob
import hashlib
import tempfile
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CHALLENGES_DIR = ROOT_DIR / "challenges"
THEME_DIR = ROOT_DIR / "ctfd-theme"
ENV_FILE = ROOT_DIR / ".env"


def load_env():
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars


def run_sql(sql_script: str) -> str:
    """Executes a SQL script against ctfd_db container using MariaDB CLI."""
    env = load_env()
    db_user = env.get("MYSQL_USER", "ctfd")
    db_pass = env.get("MYSQL_PASSWORD", "ieee_ausb_ctfd_db_user_2026!")
    db_name = env.get("MYSQL_DATABASE", "ctfd")

    cmd = [
        "docker", "exec", "-i", "ctfd_db",
        "mariadb", f"-u{db_user}", f"-p{db_pass}", db_name
    ]
    res = subprocess.run(cmd, input=sql_script, text=True, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(f"Database SQL error: {res.stderr.strip()}")
    return res.stdout


def escape_sql(val: str) -> str:
    if val is None:
        return "NULL"
    # Basic sql string escaping
    escaped = val.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def configure_ctfd_site():
    """Sets initial CTFd configurations in config table."""
    print("[*] Configuring CTFd system parameters & themes...")

    css_file = THEME_DIR / "scoreboard-projector.css"
    js_file = THEME_DIR / "scoreboard-projector.js"

    theme_header = ""
    theme_footer = ""
    if css_file.exists():
        theme_header = f"<style>\n{css_file.read_text()}\n</style>"
    if js_file.exists():
        theme_footer = f"<script>\n{js_file.read_text()}\n</script>"

    configs = {
        "ctf_name": "Case File: The Mid-Sem Leak",
        "ctf_description": "IEEE AUSB Annual Cybersecurity Incident Triage CTF — GICT Labs 207 & 208",
        "ctf_theme": "m0xblood",
        "setup": "1",
        "user_mode": "teams",
        "theme_header": theme_header,
        "theme_footer": theme_footer,
    }

    sql = ""
    for k, v in configs.items():
        sql += f"""
        DELETE FROM config WHERE `key` = {escape_sql(k)};
        INSERT INTO config (`key`, `value`) VALUES ({escape_sql(k)}, {escape_sql(v)});
        """
    run_sql(sql)
    print("  [+] Core site settings and 'm0xblood' theme bindings applied successfully.")


def upload_file_to_ctfd(file_path: Path, challenge_id: int):
    """Uploads file to container /var/uploads/<sha1>/ and registers in files table."""
    if not file_path.exists():
        print(f"  [!] Warning: Distribution file not found: {file_path}")
        return

    content = file_path.read_bytes()
    sha1 = hashlib.sha1(content).hexdigest()
    filename = file_path.name
    rel_location = f"{sha1}/{filename}"

    # Ensure upload directory exists inside container
    mkdir_cmd = ["docker", "exec", "ctfd_app", "mkdir", "-p", f"/var/uploads/{sha1}"]
    subprocess.run(mkdir_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Write file content
    write_cmd = ["docker", "exec", "-i", "ctfd_app", "sh", "-c", f"cat > /var/uploads/{rel_location}"]
    subprocess.run(write_cmd, input=content, check=True)

    # Ensure ownership
    chown_cmd = ["docker", "exec", "ctfd_app", "chown", "-R", "ctfd:ctfd", f"/var/uploads/{sha1}"]
    subprocess.run(chown_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Register in DB if not already present
    check_sql = f"SELECT id FROM files WHERE location = {escape_sql(rel_location)} AND challenge_id = {challenge_id};"
    out = run_sql(check_sql).strip()
    if not out:
        insert_sql = f"""
        INSERT INTO files (type, location, challenge_id, sha1sum)
        VALUES ('standard', {escape_sql(rel_location)}, {challenge_id}, {escape_sql(sha1)});
        """
        run_sql(insert_sql)
        print(f"  [+] Attached file: {filename} (SHA1: {sha1[:10]}...)")
    else:
        print(f"  [.] File already registered: {filename}")


def seed_challenge(yaml_path: Path):
    """Parses and seeds a single challenge into CTFd."""
    challenge_dir = yaml_path.parent
    try:
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"  [!] Error parsing {yaml_path}: {e}")
        return

    name = data.get("name")
    if not name:
        return

    category = data.get("category", "General")
    description = data.get("description", "")
    value = int(data.get("value", 500))
    chal_type = data.get("type", "dynamic")
    state = data.get("state", "visible")
    flags = data.get("flags", [])
    files = data.get("files", [])
    hints = data.get("hints", [])
    tags = data.get("tags", [category])

    print(f"\n[*] Processing Challenge: '{name}' [{category}]")

    # Check if challenge already exists
    sql_find = f"SELECT id FROM challenges WHERE name = {escape_sql(name)};"
    res = run_sql(sql_find).strip()

    if res:
        # Challenge exists, retrieve ID
        lines = res.split("\n")
        challenge_id = int(lines[-1].strip())
        print(f"  [.] Existing challenge found (ID: {challenge_id}). Updating metadata...")
        update_sql = f"""
        UPDATE challenges SET
          description = {escape_sql(description)},
          value = {value},
          category = {escape_sql(category)},
          type = {escape_sql(chal_type)},
          state = {escape_sql(state)}
        WHERE id = {challenge_id};
        """
        run_sql(update_sql)
    else:
        # Insert new challenge
        insert_sql = f"""
        INSERT INTO challenges (name, description, value, category, type, state)
        VALUES ({escape_sql(name)}, {escape_sql(description)}, {value}, {escape_sql(category)}, {escape_sql(chal_type)}, {escape_sql(state)});
        SELECT LAST_INSERT_ID();
        """
        out = run_sql(insert_sql).strip()
        lines = out.split("\n")
        challenge_id = int(lines[-1].strip())
        print(f"  [+] Challenge created (ID: {challenge_id}).")

    # Dynamic challenge scoring parameters
    if chal_type == "dynamic":
        dyn_sql = f"""
        INSERT INTO dynamic_challenge (id, initial, minimum, decay, function)
        VALUES ({challenge_id}, 500, 100, 15, 'logarithmic')
        ON DUPLICATE KEY UPDATE initial = 500, minimum = 100, decay = 15;
        """
        run_sql(dyn_sql)

    # Flags synchronization
    clean_flags_sql = f"DELETE FROM flags WHERE challenge_id = {challenge_id};"
    run_sql(clean_flags_sql)

    for fl in flags:
        flag_str = fl if isinstance(fl, str) else fl.get("flag", "")
        if flag_str:
            flag_sql = f"""
            INSERT INTO flags (challenge_id, type, content, data)
            VALUES ({challenge_id}, 'static', {escape_sql(flag_str)}, '');
            """
            run_sql(flag_sql)
            print(f"  [+] Seeded flag: {flag_str}")

    # Tags synchronization
    clean_tags_sql = f"DELETE FROM tags WHERE challenge_id = {challenge_id};"
    run_sql(clean_tags_sql)
    if isinstance(tags, list):
        for tg in tags:
            tag_sql = f"INSERT INTO tags (challenge_id, value) VALUES ({challenge_id}, {escape_sql(str(tg))});"
            run_sql(tag_sql)

    # Hints synchronization
    if hints and isinstance(hints, list):
        clean_hints_sql = f"DELETE FROM hints WHERE challenge_id = {challenge_id};"
        run_sql(clean_hints_sql)
        for h in hints:
            if isinstance(h, dict):
                h_content = h.get("content", "")
                h_cost = int(h.get("cost", 30))
            else:
                h_content = str(h)
                h_cost = 30
            hint_sql = f"""
            INSERT INTO hints (type, challenge_id, content, cost)
            VALUES ('standard', {challenge_id}, {escape_sql(h_content)}, {h_cost});
            """
            run_sql(hint_sql)
            print(f"  [+] Seeded hint (-{h_cost} pts)")

    # Distribution files
    if files and isinstance(files, list):
        for f_rel in files:
            file_path = challenge_dir / f_rel
            upload_file_to_ctfd(file_path, challenge_id)


def flush_cache():
    """Flushes Redis cache so all updates take effect immediately."""
    print("[*] Flushing CTFd cache in Redis...")
    cmd = ["docker", "exec", "ctfd_cache", "redis-cli", "FLUSHALL"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print("  [+] Cache cleared successfully.")
    else:
        print(f"  [!] Cache flush warning: {res.stderr.strip()}")


def main():
    print("==============================================================")
    print("  IEEE AUSB CTF: Case File: The Mid-Sem Leak — Seeder")
    print("==============================================================")

    # Check container health
    res = subprocess.run(["docker", "ps", "--filter", "name=ctfd_db", "--format", "{{.Names}}"], capture_output=True, text=True)
    if "ctfd_db" not in res.stdout:
        print("[!] Error: ctfd_db container is not running. Please start the stack first:")
        print("    uv run ctf start")
        sys.exit(1)

    # 1. Site configuration & theme bindings
    configure_ctfd_site()

    # 2. Discover and seed all challenge.yml files
    challenge_configs = sorted(glob.glob(str(CHALLENGES_DIR / "**" / "challenge.yml"), recursive=True))
    seeded_count = 0

    for cfg_str in challenge_configs:
        cfg_path = Path(cfg_str)
        if "template" in cfg_path.parts:
            continue
        seed_challenge(cfg_path)
        seeded_count += 1

    # 3. Clear cache
    flush_cache()

    print("\n==============================================================")
    print(f"  [SUCCESS] Successfully seeded {seeded_count} challenges into CTFd!")
    print("  Access the live board at: http://localhost (or your LAN IP)")
    print("==============================================================")


if __name__ == "__main__":
    main()
