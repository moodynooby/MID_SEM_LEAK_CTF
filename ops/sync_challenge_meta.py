#!/usr/bin/env python3
"""
README -> challenge.yml Scoring Sync
====================================
Single source of truth for a challenge's point weight is a fenced block at the
top of its own ``README.md``::

    ```yaml canonical
    difficulty: hard
    value: 700
    extra:
      initial: 700
      decay: 12
      minimum: 350
    ```

The block must agree with the difficulty band in ``ops/seed_challenges.py``
(``SCORING_TIERS``), so a typo can never silently downgrade a hard challenge.

Usage::

    uv run python ops/sync_challenge_meta.py --check          # CI / preflight gate
    uv run python ops/sync_challenge_meta.py --fix            # rewrite YAML scoring keys
    uv run python ops/sync_challenge_meta.py --check challenges/password_cracking

``--fix`` only rewrites the ``difficulty:`` / ``value:`` / ``extra:`` lines; it
never regenerates the YAML, so comments, hints, tags and ordering survive.

``--init`` bootstraps the block from an existing ``challenge.yml`` (the only
allowed YAML -> README direction). After that the README is authoritative.

Exit codes: 0 = in sync (or skipped), 1 = drift found in ``--check``, 2 = error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
CHALLENGES_DIR = ROOT_DIR / "challenges"

# Reuse the seeder's band table instead of keeping a seventh copy of the numbers.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_challenges import DIFFICULTY_ALIASES, SCORING_TIERS  # noqa: E402

BLOCK_RE = re.compile(r"^```ya?ml[ \t]+canonical[ \t]*\r?\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)

FIELDS = ("difficulty", "value", "initial", "decay", "minimum")
SCORING_KEYS = ("difficulty", "value", "extra")


class DriftError(Exception):
    pass


def normalize_difficulty(raw) -> str:
    text = str(raw or "").strip().strip("\"'").lower()
    return DIFFICULTY_ALIASES.get(text, text)


def read_canonical_block(readme: Path) -> dict | None:
    match = BLOCK_RE.search(readme.read_text(encoding="utf-8"))
    if not match:
        return None
    block = yaml.safe_load(match.group(1)) or {}
    if not isinstance(block, dict):
        raise DriftError(f"{readme}: canonical block is not a mapping")
    return block


BLOCK_COMMENT = (
    "<!-- Canonical scoring block — source of truth for challenge.yml.\n"
    "     Sync with `uv run python ops/sync_challenge_meta.py --fix`.\n"
    "     Band values live in ops/seed_challenges.py SCORING_TIERS. -->"
)


def expected_values(block: dict, readme: Path) -> dict:
    """Resolve the canonical block against the authoritative scoring tier."""
    difficulty = normalize_difficulty(block.get("difficulty"))
    if not difficulty:
        raise DriftError(f"{readme}: canonical block is missing `difficulty:`")
    if difficulty not in SCORING_TIERS:
        raise DriftError(
            f"{readme}: unknown difficulty {difficulty!r} (expected one of {sorted(SCORING_TIERS)})"
        )
    tier = SCORING_TIERS[difficulty]
    expected = {"difficulty": difficulty, "value": tier["initial"], **tier}

    for key in ("value", "initial", "decay", "minimum"):
        if key not in block:
            continue
        try:
            declared = int(block[key])
        except (TypeError, ValueError):
            raise DriftError(f"{readme}: `{key}: {block[key]!r}` is not an integer")
        if declared != expected[key]:
            raise DriftError(
                f"{readme}: canonical `{key}: {declared}` contradicts the {difficulty} "
                f"band value {expected[key]} (see ops/seed_challenges.py SCORING_TIERS)"
            )

    extra = block.get("extra") or {}
    if not isinstance(extra, dict):
        raise DriftError(f"{readme}: `extra:` must be a mapping")
    for key in ("initial", "decay", "minimum"):
        if key not in extra:
            continue
        try:
            declared = int(extra[key])
        except (TypeError, ValueError):
            raise DriftError(f"{readme}: `extra.{key}: {extra[key]!r}` is not an integer")
        if declared != expected[key]:
            raise DriftError(
                f"{readme}: canonical `extra.{key}: {declared}` contradicts the {difficulty} "
                f"band value {expected[key]}"
            )

    return expected


def actual_values(yml: dict) -> dict:
    extra = yml.get("extra") if isinstance(yml.get("extra"), dict) else {}
    return {
        "difficulty": normalize_difficulty(yml.get("difficulty")),
        "value": yml.get("value"),
        "initial": extra.get("initial"),
        "decay": extra.get("decay"),
        "minimum": extra.get("minimum"),
    }


def _replace_scalar(text: str, key: str, new_value, indent: str = "") -> str:
    """Replace ``<indent><key>: value`` keeping trailing comments and quoting style."""
    pattern = re.compile(
        rf"^({re.escape(indent)}{re.escape(key)}:[ \t]*)([\"']?)([^\"'#\r\n]*?)(\2)([ \t]*(?:#.*)?)$",
        re.MULTILINE,
    )

    def repl(match: re.Match) -> str:
        quote_open, quote_close = match.group(2), match.group(4)
        return f"{match.group(1)}{quote_open}{new_value}{quote_close}{match.group(5)}"

    new_text, count = pattern.subn(repl, text, count=1)
    if count == 0:
        # Key absent: append it (extra: block handled by caller).
        if indent:
            raise DriftError(f"could not find `{indent}{key}:` to update")
        new_text = text.rstrip("\n") + f"\n{key}: {new_value}\n"
    return new_text


def _ensure_extra_block(text: str, expected: dict) -> str:
    """Rewrite (or create) the `extra:` mapping with initial/decay/minimum."""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if re.match(r"^extra:[ \t]*$", line)), None)
    rendered = [
        "extra:",
        f"  initial: {expected['initial']}",
        f"  decay: {expected['decay']}",
        f"  minimum: {expected['minimum']}",
    ]

    if start is None:
        body = "\n".join(rendered)
        if re.search(r"^value:.*$", text, re.MULTILINE):
            return re.sub(r"(^value:.*$)", lambda m: f"{m.group(1)}\n{body}", text, count=1, flags=re.MULTILINE)
        return text.rstrip("\n") + f"\n{body}\n"

    end = start + 1
    while end < len(lines) and (not lines[end].strip() or lines[end].startswith((" ", "\t"))):
        end += 1
    return "\n".join(lines[:start] + rendered + lines[end:]) + "\n"


def apply_fix(yml_path: Path, expected: dict) -> None:
    original = yml_path.read_text(encoding="utf-8")
    text = _replace_scalar(original, "difficulty", expected["difficulty"])
    text = _replace_scalar(text, "value", expected["value"])
    text = _ensure_extra_block(text, expected)
    if text == original:
        return
    yml_path.write_text(text, encoding="utf-8")
    # Fail loudly rather than emiting a corrupt YAML.
    reloaded = yaml.safe_load(yml_path.read_text(encoding="utf-8"))
    if actual_values(reloaded) != {k: expected[k] for k in FIELDS}:
        yml_path.write_text(original, encoding="utf-8")
        raise DriftError(f"{yml_path}: automatic fix did not converge, original restored")


def check_challenge(challenge_dir: Path, fix: bool) -> tuple[str, list[str]]:
    readme = challenge_dir / "README.md"
    yml_path = challenge_dir / "challenge.yml"
    if not readme.exists() or not yml_path.exists():
        return "skip", []

    block = read_canonical_block(readme)
    if block is None:
        return "no-block", []

    expected = expected_values(block, readme)
    yml = yaml.safe_load(yml_path.read_text(encoding="utf-8")) or {}
    actual = actual_values(yml)

    drift = [
        f"{field}: README={expected[field]!r} challenge.yml={actual.get(field)!r}"
        for field in FIELDS
        if actual.get(field) != expected[field]
    ]
    if not drift:
        return "ok", []

    if fix:
        apply_fix(yml_path, expected)
        return "fixed", drift
    return "drift", drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Keep challenge.yml scoring fields in lockstep with each README's canonical block."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="report drift and exit 1 (default)")
    mode.add_argument("--fix", action="store_true", help="rewrite drifted challenge.yml scoring keys")
    parser.add_argument(
        "targets",
        nargs="*",
        type=Path,
        help="challenge directories (default: every directory under challenges/)",
    )
    args = parser.parse_args(argv)
    fix = args.fix

    if args.targets:
        targets = [t if t.is_absolute() else (ROOT_DIR / t) for t in args.targets]
    else:
        targets = sorted(p for p in CHALLENGES_DIR.iterdir() if p.is_dir() and not p.name.startswith("."))

    failures = 0
    checked = 0
    for challenge_dir in targets:
        try:
            status, drift = check_challenge(challenge_dir, fix)
        except DriftError as exc:
            print(f"[FAIL] {challenge_dir.name}: {exc}")
            failures += 1
            continue

        if status in ("ok", "fixed"):
            checked += 1
        if status == "ok":
            print(f"[ OK ] {challenge_dir.name}")
        elif status == "fixed":
            print(f"[FIXED] {challenge_dir.name}")
            for line in drift:
                print(f"        - {line}")
        elif status == "drift":
            print(f"[DRIFT] {challenge_dir.name}")
            for line in drift:
                print(f"        - {line}")
            failures += 1
        elif status == "no-block":
            print(f"[SKIP] {challenge_dir.name}: no ```yaml canonical block in README.md")

    print(f"\n{checked} challenge(s) in sync, {failures} problem(s) found.")
    if failures:
        print("Run with --fix to rewrite challenge.yml from the README canonical block.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
