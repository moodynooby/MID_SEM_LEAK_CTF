#!/usr/bin/env python3
"""
solve.py — Automated Solver for 'Memory Forensics: Lab 207 Terminal RAM Dump'
Track: Forensics & Memory | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Yesha (Forensics Track Lead)

Walkthrough Solution:
    1. CTFd Artifact Download:
       - Download `lab207_terminal_ram.raw` directly from the CTFd challenge page.
    2. Forensic Analysis:
       - Memory String Carving:
         `strings -a files/lab207_terminal_ram.raw | grep -i "case{"`
       - Volatility 3 Analysis:
         `vol -f lab207_terminal_ram.raw linux.bash.Bash`
         `vol -f lab207_terminal_ram.raw linux.envars.Envars`
       - Both methods reveal TA Piyush's environment variable:
         `EXAM_EXFIL_FLAG=case{volatility3_lab207_terminal_ram}`
"""

import re
import sys
import struct
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent
RAM_PATH = CHALLENGE_DIR / "files" / "lab207_terminal_ram.raw"
EXPECTED_FLAG = "case{volatility3_lab207_terminal_ram}"


def solve():
    print(f"[*] Solving Physical Forensics RAM Dump challenge from: {RAM_PATH}")
    if not RAM_PATH.exists():
        print(f"[-] Error: Target memory dump {RAM_PATH} does not exist!")
        return False

    raw_bytes = RAM_PATH.read_bytes()
    print(f"[+] Loaded memory dump ({len(raw_bytes)} bytes / {len(raw_bytes)/(1024*1024):.1f} MB)")

    # 1. Verify LiME header
    magic, version, start, end = struct.unpack("<IIQQ", raw_bytes[:24])
    if magic == 0x4C694D45:
        print(f"[+] Confirmed valid LiME memory format (Range: 0x{start:08x} - 0x{end:08x})")
    else:
        print("[!] Note: Raw memory dump without LiME prefix.")

    # 2. Extract bash process environment variables
    found_flag = None

    # Technique A: Regex memory scan across all pages (discovers true flag & decoys)
    flag_pattern = re.compile(rb"case\{[a-zA-Z0-9_]+\}")
    matches = set(flag_pattern.findall(raw_bytes))
    print(f"[+] Total distinct candidate flags in memory dump: {len(matches)}")
    for m in matches:
        print(f"    - Candidate flag: {m.decode('ascii')}")

    # Technique B: Volatility/Environment parser simulation (isolating culprit TA Piyush's EXAM_EXFIL_FLAG)
    env_matches = re.findall(rb"([A-Z0-9_]+)=(case\{[a-zA-Z0-9_]+\})", raw_bytes)
    for var_name, flag_val in env_matches:
        v_name = var_name.decode('ascii')
        f_val = flag_val.decode('ascii')
        print(f"[+] Process environment vector: {v_name} = {f_val}")
        if v_name == "EXAM_EXFIL_FLAG":
            found_flag = f_val
            print(f"    ==> [!] MATCH: Culprit TA Piyush exfiltration flag isolated: {found_flag}")

    # Technique C: Verify bash command history trace
    history_matches = [
        line for line in raw_bytes.split(b"\n")
        if b"curl" in line and (b"faculty.ahduni.edu.in" in line or b"faculty.gict.ac.in" in line)
    ]
    if history_matches:
        print(f"[+] Identified culprit terminal command in history buffer: {history_matches[0].strip().decode('ascii', errors='ignore')}")

    if found_flag == EXPECTED_FLAG:
        print(f"[SUCCESS] Validated Flag: {found_flag}")
        return True
    else:
        print(f"[-] Flag mismatch. Expected: '{EXPECTED_FLAG}', Found: '{found_flag}'")
        return False


if __name__ == "__main__":
    success = solve()
    sys.exit(0 if success else 1)
