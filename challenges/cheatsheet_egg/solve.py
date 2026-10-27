#!/usr/bin/env python3
"""
solve.py — Automated Solver for 'Flag in Cheatsheet: Participant Kit Easter Egg'
Track: Network & Forensics | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Vatsal Pandya (@VP1107)

Solve Path:
    1. Read 'files/CTF_101_CheatSheet.md'.
    2. Extract all hidden HTML comments.
    3. Filter out decoy developer comments.
    4. Extract and verify the true easter egg flag:
       case{always_read_the_cheat_sheet_first}
"""

import sys
import re
from pathlib import Path

TARGET_FLAG = "case{always_read_the_cheat_sheet_first}"
KNOWN_DECOYS = {"case{staging_lab207_workstation_setup_key}"}


def solve(file_path: Path):
    if not file_path.exists():
        print(f"[-] Missing target file: {file_path}")
        sys.exit(1)

    print(f"[*] Inspecting participant cheatsheet: {file_path}")
    content = file_path.read_text(encoding="utf-8")

    comments = re.findall(r"<!--(.*?)-->", content, re.DOTALL)
    print(f"[+] Total hidden HTML comments discovered: {len(comments)}")

    extracted_flag = None
    for comment in comments:
        flags = re.findall(r"case\{[^}]+\}", comment)
        for fl in flags:
            if fl in KNOWN_DECOYS:
                print(f"  [-] Encountered decoy comment flag: {fl}")
            elif fl == TARGET_FLAG:
                print(f"  [+] OFFICIAL EASTER EGG FLAG DISCOVERED: {fl}")
                extracted_flag = fl

    print("\n" + "=" * 60)
    print("CHEATSHEET EASTER EGG SOLVER RESULTS:")
    print(f"  Target Flag:    {TARGET_FLAG}")
    print(f"  Extracted Flag: {extracted_flag}")
    print("=" * 60)

    if extracted_flag == TARGET_FLAG:
        print("[+] SUCCESS: Challenge verified cleanly! Extracted flag matches expected.")
        sys.exit(0)
    else:
        print("[-] FAILURE: Flag mismatch or extraction failure.")
        sys.exit(1)


def main():
    repo_root = Path(__file__).resolve().parent
    target_file = repo_root / "files" / "CTF_101_CheatSheet.md"
    solve(target_file)


if __name__ == "__main__":
    main()
