#!/usr/bin/env python3
"""
solve.py — Automated Solver for "Liam's Idea: Fragmented Exfiltration"
Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
"""

import os
import sys
import base64
import re
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent
FILES_DIR = CHALLENGE_DIR / "files"
TARGET_FLAG = "case{reconstructed_exfil_chunk_assembly}"


def solve():
    print("[*] Reassembling fragmented exfiltration chunks from files/...")
    parts = sorted(FILES_DIR.glob("part*.txt"))
    if not parts:
        print("[-] Error: No part*.txt files found!")
        sys.exit(1)

    print(f"[+] Found {len(parts)} chunk files to assemble.")

    b64_stream = ""
    for p in parts:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line.startswith("#"):
                    b64_stream += line

    print(f"[+] Concatenated clean Base64 stream ({len(b64_stream)} chars)")

    try:
        raw_bytes = base64.b64decode(b64_stream)
        print(f"[+] Successfully decoded binary video container ({len(raw_bytes)} bytes)")
    except Exception as e:
        print(f"[-] Base64 decoding failed: {e}")
        sys.exit(1)

    # Search for flag in binary stream
    matches = re.findall(rb"case\{[a-zA-Z0-9_]+\}", raw_bytes)
    found_flags = [m.decode("ascii") for m in matches]

    if TARGET_FLAG in found_flags:
        print(f"[+] SUCCESS: Extracted flag: {TARGET_FLAG}")
        return True
    elif found_flags:
        print(f"[+] Extracted flag from container: {found_flags[0]}")
        return True
    else:
        # Check if text strings match
        text_matches = re.findall(r"case\{[a-zA-Z0-9_]+\}", raw_bytes.decode("latin1", errors="ignore"))
        if TARGET_FLAG in text_matches:
            print(f"[+] SUCCESS: Extracted flag: {TARGET_FLAG}")
            return True

    print("[-] Flag not found in reconstructed video payload!")
    sys.exit(1)


if __name__ == "__main__":
    solve()
