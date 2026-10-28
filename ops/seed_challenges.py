#!/usr/bin/env python3
"""
Seed & Orchestrate CTFd Challenges, Themes, and Assets
Case File: The Mid-Sem Leak — IEEE AUSB CTF 2026

Idempotent, offline-first seeder that:
  1. Configures CTFd core metadata (name, theme, user mode, setup status).
  2. Injects big-screen scoreboard projector styling into theme_header / theme_footer.
  3. Discovers all challenges from challenges/**/challenge.yml.
  4. Seeds challenges with difficulty-tiered dynamic scoring
     (easy 300/20/100, medium 500/16/200, hard 700/12/350).
  5. Registers static flags, hints, and category tags.
  6. Synchronises challenge distribution files into /var/uploads/<sha1>/ and registers
     them in CTFd, pruning attachments the YAML no longer declares (so a regenerated
     artifact actually replaces the stale one instead of piling up a second download).
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
ENV_FILE = ROOT_DIR / ".env"

# ---------------------------------------------------------------------------
# Difficulty -> dynamic scoring tier (single source of truth for point weight).
# Mirrored in challenges/README.md (section 3) and EVENT.md (section 8A).
# Floors scale with difficulty so a widely-solved hard challenge can never
# collapse to the same value as a trivial one.
# ---------------------------------------------------------------------------
SCORING_TIERS = {
    "easy": {"initial": 300, "decay": 20, "minimum": 100},
    "medium": {"initial": 500, "decay": 16, "minimum": 200},
    "hard": {"initial": 700, "decay": 12, "minimum": 350},
}

# Legacy / informal tags that still need to resolve to a real tier.
DIFFICULTY_ALIASES = {
    "easy_med": "medium",
    "easy-medium": "medium",
    "med": "medium",
    "medium-hard": "hard",
    "hard_insane": "hard",
    "insane": "hard",
}

# Used only when a challenge.yml declares neither `difficulty:` nor `extra:`.
LEGACY_SCORING = {"initial": 500, "decay": 15, "minimum": 100}


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


def run_sql(sql_script: str, raw: bool = False) -> str:
    """Executes a SQL script against ctfd_db container using MariaDB CLI.

    ``raw=True`` adds ``-N -B`` (batch mode: tab-separated rows, no column
    headers and no table borders), which is what callers iterating a result set
    need. The default keeps the human-readable table output.
    """
    env = load_env()
    db_user = env.get("MYSQL_USER", "ctfd")
    db_pass = env.get("MYSQL_PASSWORD", "ieee_ausb_ctfd_db_user_2026!")
    db_name = env.get("MYSQL_DATABASE", "ctfd")

    cmd = [
        "docker", "exec", "-i", "ctfd_db",
        "mariadb", f"-u{db_user}", f"-p{db_pass}"
    ]
    if raw:
        cmd += ["-N", "-B"]
    cmd.append(db_name)
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

    configs = {
        "ctf_name": "Case File: The Mid-Sem Leak",
        "ctf_description": "IEEE AUSB Annual Cybersecurity Incident Triage CTF — AU Labs 207 & 208",
        "ctf_theme": "core-beta",
        "setup": "1",
        "user_mode": "teams",
        "theme_header": "",
        "theme_footer": "",
    }

    sql = ""
    for k, v in configs.items():
        sql += f"""
        DELETE FROM config WHERE `key` = {escape_sql(k)};
        INSERT INTO config (`key`, `value`) VALUES ({escape_sql(k)}, {escape_sql(v)});
        """
    run_sql(sql)
    print("  [+] Core site settings and 'core-beta' theme bindings applied successfully.")


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

    # Register in DB if not already present.
    # `files.type` drives SQLAlchemy single-table inheritance: CTFd's
    # Challenges.files relationship targets ChallengeFiles (polymorphic identity
    # "challenge"). Inserting 'standard' makes the row load as a plain Files
    # object, so `challenge.files` is EMPTY and the challenge modal renders zero
    # download links (the bytes are still reachable by direct /files/<path> URL).
    check_sql = f"SELECT id FROM files WHERE location = {escape_sql(rel_location)} AND challenge_id = {challenge_id};"
    out = run_sql(check_sql).strip()
    if not out:
        insert_sql = f"""
        INSERT INTO files (type, location, challenge_id, sha1sum)
        VALUES ('challenge', {escape_sql(rel_location)}, {challenge_id}, {escape_sql(sha1)});
        """
        run_sql(insert_sql)
        print(f"  [+] Attached file: {filename} (SHA1: {sha1[:10]}...)")
    else:
        run_sql(
            f"UPDATE files SET type = 'challenge' WHERE id = {int(out.splitlines()[-1].strip())};"
        )
        print(f"  [.] File already registered: {filename}")


def sync_challenge_files(challenge_id: int, challenge_dir: Path, files):
    """Make CTFd's attachment list match the challenge.yml ``files:`` block exactly.

    CTFd stores uploads at ``/var/uploads/<sha1>/<filename>``, so regenerating an
    artifact always produces a NEW location. Uploading alone would therefore
    append a second, identically named download and leave the stale one live —
    the challenge modal would keep advertising the old file. Declarative sync:
    delete every attachment the YAML no longer declares, then upload the rest.
    """
    expected = []
    for f_rel in files if isinstance(files, list) else []:
        file_path = challenge_dir / f_rel
        if not file_path.exists():
            print(f"  [!] Warning: Distribution file not found: {file_path}")
            continue
        sha1 = hashlib.sha1(file_path.read_bytes()).hexdigest()
        expected.append((file_path, f"{sha1}/{file_path.name}"))

    keep = ", ".join(escape_sql(loc) for _, loc in expected)
    # `NOT IN (NULL)` matches nothing, so an emptied `files:` block needs its own
    # WHERE clause — otherwise removing every attachment would prune zero rows.
    where = (
        f"challenge_id = {challenge_id} AND location NOT IN ({keep})"
        if expected
        else f"challenge_id = {challenge_id}"
    )
    stale = run_sql(f"SELECT location FROM files WHERE {where};", raw=True).strip()

    for loc in [line.strip() for line in stale.splitlines() if line.strip()]:
        run_sql(
            f"DELETE FROM files WHERE challenge_id = {challenge_id} AND location = {escape_sql(loc)};"
        )
        # Drop the blob too, but only when no other challenge row references it.
        still_used = run_sql(
            f"SELECT COUNT(*) FROM files WHERE location = {escape_sql(loc)};", raw=True
        ).strip()
        if still_used and still_used.splitlines()[-1].strip() == "0":
            subprocess.run(
                ["docker", "exec", "ctfd_app", "rm", "-rf", f"/var/uploads/{loc.split('/', 1)[0]}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        print(f"  [-] Pruned stale attachment: {loc}")

    for file_path, _ in expected:
        upload_file_to_ctfd(file_path, challenge_id)


def resolve_scoring(data, name):
    """Resolves (initial, decay, minimum) for one challenge.

    Priority: explicit ``extra:`` block in challenge.yml -> ``difficulty:``
    tier -> legacy flat 500/15/100. Returns (scoring_dict, difficulty_label).
    """
    difficulty = str(data.get("difficulty", "")).strip().lower()
    difficulty = DIFFICULTY_ALIASES.get(difficulty, difficulty)

    tier = SCORING_TIERS.get(difficulty)
    if tier:
        scoring = dict(tier)
    else:
        print(
            f"  [!] '{name}' has no valid `difficulty:` (got '{difficulty or 'unset'}'). "
            f"Expected one of: {', '.join(SCORING_TIERS)}. "
            f"Falling back to legacy {LEGACY_SCORING['initial']}/"
            f"{LEGACY_SCORING['decay']}/{LEGACY_SCORING['minimum']}."
        )
        scoring = dict(LEGACY_SCORING)

    # A hand-tuned per-challenge override always wins over the tier default.
    extra = data.get("extra") or {}
    if isinstance(extra, dict):
        for key in ("initial", "decay", "minimum"):
            if extra.get(key) is not None:
                scoring[key] = int(extra[key])

    # Guardrail: the YAML must stay self-consistent so a reader sees the truth.
    tier_initial = (tier or {}).get("initial")
    if tier_initial is not None and scoring["initial"] != tier_initial:
        print(
            f"  [!] '{name}': extra.initial={scoring['initial']} overrides the "
            f"'{difficulty}' tier default ({tier_initial})."
        )
    declared_value = data.get("value")
    if declared_value is not None and int(declared_value) != scoring["initial"]:
        print(
            f"  [!] '{name}': value: {declared_value} does not match the computed "
            f"initial {scoring['initial']} — fix the YAML (drift)."
        )

    return scoring, (difficulty or "unset")


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
    chal_type = data.get("type", "dynamic")
    # Difficulty tier drives the dynamic scoring band (see SCORING_TIERS).
    scoring, difficulty = resolve_scoring(data, name)
    # `challenges.value` is what the UI/API display, while CTFd prices the first
    # solve off `dynamic_challenge.initial` — keep both in lockstep.
    if chal_type == "dynamic":
        value = scoring["initial"]
    else:
        value = int(data.get("value", 500) or 500)
    state = data.get("state", "visible")
    # CTFd declares max_attempts with a *client-side* SQLAlchemy default of 0,
    # so a raw INSERT that omits the column leaves it NULL. core-beta's
    # challenge.html then renders `{% if max_attempts > 0 %}` and blows up with
    # "TypeError: '>' not supported between instances of 'NoneType' and 'int'",
    # i.e. HTTP 500 on every /api/v1/challenges/<id> (challenge pages unusable).
    max_attempts = int(data.get("max_attempts", 0) or 0)
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
          name = {escape_sql(name)},
          description = {escape_sql(description)},
          value = {value},
          category = {escape_sql(category)},
          type = {escape_sql(chal_type)},
          state = {escape_sql(state)},
          max_attempts = {max_attempts}
        WHERE id = {challenge_id};
        """
        run_sql(update_sql)
    else:
        # Insert new challenge
        insert_sql = f"""
        INSERT INTO challenges (name, description, value, category, type, state, max_attempts)
        VALUES ({escape_sql(name)}, {escape_sql(description)}, {value}, {escape_sql(category)}, {escape_sql(chal_type)}, {escape_sql(state)}, {max_attempts});
        SELECT LAST_INSERT_ID();
        """
        out = run_sql(insert_sql).strip()
        lines = out.split("\n")
        challenge_id = int(lines[-1].strip())
        print(f"  [+] Challenge created (ID: {challenge_id}).")

    # Dynamic challenge scoring parameters (difficulty-tiered)
    if chal_type == "dynamic":
        dyn_sql = f"""
        INSERT INTO dynamic_challenge (id, initial, minimum, decay, function)
        VALUES ({challenge_id}, {scoring['initial']}, {scoring['minimum']}, {scoring['decay']}, 'logarithmic')
        ON DUPLICATE KEY UPDATE initial = VALUES(initial), minimum = VALUES(minimum), decay = VALUES(decay);
        """
        run_sql(dyn_sql)
        print(
            f"  [~] Dynamic scoring [{difficulty}]: {scoring['initial']} pt -> "
            f"{scoring['minimum']} pt floor after {scoring['decay']} solves"
        )

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

    # Hints synchronization (DELETE runs unconditionally so emptying `hints:`
    # in the YAML actually clears the DB instead of leaving stale hints behind)
    clean_hints_sql = f"DELETE FROM hints WHERE challenge_id = {challenge_id};"
    run_sql(clean_hints_sql)
    if hints and isinstance(hints, list):
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

    # Distribution files (declarative sync: prune stale rows, then upload)
    sync_challenge_files(challenge_id, challenge_dir, files)


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

    # 1b. Repair rows seeded before max_attempts was written explicitly.
    #     A NULL here makes every challenge page 500 (see seed_challenge()).
    run_sql("UPDATE challenges SET max_attempts = 0 WHERE max_attempts IS NULL;")

    # 1c. Repair challenge attachments seeded as files.type='standard'. CTFd's
    #     polymorphic Files model only links type='challenge' rows to the
    #     challenge modal (see upload_file_to_ctfd()).
    run_sql("UPDATE files SET type = 'challenge' WHERE challenge_id IS NOT NULL AND type <> 'challenge';")

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

    # 4. Self-check: a NULL max_attempts makes every challenge page return 500.
    broken = run_sql("SELECT COUNT(*) FROM challenges WHERE max_attempts IS NULL;").strip()
    if broken and broken.splitlines()[-1].strip() not in ("0", ""):
        print(f"\n[!] ERROR: {broken.splitlines()[-1].strip()} challenge(s) still have NULL max_attempts.")
        print("    Opening those challenges will 500. Fix with:")
        print("    UPDATE challenges SET max_attempts = 0 WHERE max_attempts IS NULL;")
        sys.exit(1)

    # 5. Self-check: attachments must be type='challenge' to show up as links.
    unlinked = run_sql(
        "SELECT COUNT(*) FROM files WHERE challenge_id IS NOT NULL AND type <> 'challenge';"
    ).strip()
    if unlinked and unlinked.splitlines()[-1].strip() not in ("0", ""):
        print(f"\n[!] ERROR: {unlinked.splitlines()[-1].strip()} challenge file(s) are not type='challenge'.")
        print("    They download by direct URL but never appear in the challenge modal. Fix with:")
        print("    UPDATE files SET type = 'challenge' WHERE challenge_id IS NOT NULL AND type <> 'challenge';")
        sys.exit(1)

    # 6. Self-check: a row's location must be `<sha1>/<filename>` of its own blob.
    #    Drift here means the board advertises a download that no longer matches
    #    the artifact on disk (the stale-PDF trap sync_challenge_files() fixes).
    drifted = run_sql(
        "SELECT COUNT(*) FROM files WHERE challenge_id IS NOT NULL "
        "AND SUBSTRING_INDEX(location, '/', 1) <> sha1sum;",
        raw=True,
    ).strip()
    if drifted and drifted.splitlines()[-1].strip() not in ("0", ""):
        print(f"\n[!] ERROR: {drifted.splitlines()[-1].strip()} challenge file row(s) point at a stale blob.")
        print("    Re-run the seeder after regenerating the artifact, then verify:")
        print("    SELECT challenge_id, location, sha1sum FROM files WHERE challenge_id IS NOT NULL;")
        sys.exit(1)

    print("\n==============================================================")
    print(f"  [SUCCESS] Successfully seeded {seeded_count} challenges into CTFd!")
    print("  Access the live board at: http://localhost (or your LAN IP)")
    print("==============================================================")


if __name__ == "__main__":
    main()
