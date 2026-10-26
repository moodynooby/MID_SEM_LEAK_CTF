#!/usr/bin/env python3
"""
generate.py — Artifact Generator for 'Physical Forensics: Lab 207 Terminal RAM Dump'
Track: Forensics & Physical | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Yesha (Forensics Track Lead)

Generates:
    challenges/physical_terminal_ram/files/lab207_terminal_ram.raw

Storyline Context:
    At 02:14 AM on 28 October 2026, campus security quarantined Workstation PC-04 in
    GICT Lab 207 after TA Piyush Pelaiya fled the room. To prevent loss of volatile
    artifacts before power-off, a memory snapshot of the active terminal session was
    dumped to `/dev/shm/lab207_terminal_ram.raw`.

Anti-AI Defensive Layer:
    - Real memory capture structure containing process page tables, memory maps,
      Linux glibc heap chunks, environment arrays, and bash history ring buffers.
    - Decoy environment variables and decoy shell history lines across multiple users.
    - Requires memory forensics triage tools: Volatility 3 (linux.bash.Bash,
      linux.envars.Envars), strings memory carving, or GDB.

Flag:
    case{volatility3_lab207_terminal_ram}
"""

import os
import sys
import struct
import random
from pathlib import Path

FLAG = "case{volatility3_lab207_terminal_ram}"

CHALLENGE_DIR = Path(__file__).resolve().parent
FILES_DIR = CHALLENGE_DIR / "files"
OUTPUT_RAW = FILES_DIR / "lab207_terminal_ram.raw"

PAGE_SIZE = 4096


def generate_memory_dump():
    print(f"[*] Generating authentic Linux RAM dump artifact for flag: {FLAG}")
    random.seed(1337)

    # LiME (Linux Memory Extractor) Header structure
    # Magic: 0x4c694d45 ('EMiL' in little-endian / 'LiME')
    # Version: 1
    # Physical Start: 0x00000000
    # Physical End:   0x00800000 (8 MB memory slice)
    lime_magic = 0x4C694D45
    lime_version = 1
    start_addr = 0x10000000  # Physical address 256MB
    total_pages = 2048       # 2048 pages * 4096 = 8,388,608 bytes (8 MB)
    end_addr = start_addr + (total_pages * PAGE_SIZE) - 1

    lime_header = struct.pack("<IIQQ", lime_magic, lime_version, start_addr, end_addr)
    # Reserve 32 bytes for LiME header
    lime_header = lime_header.ljust(32, b"\x00")

    pages = []

    # 1. Background kernel & OS memory pages (page table entries, zeros, randomized heap fragments)
    for p_idx in range(total_pages):
        # 70% zero pages (sparse RAM), 30% fragmented memory noise
        if random.random() < 0.70:
            page = b"\x00" * PAGE_SIZE
        else:
            # Low entropy realistic glibc memory fragments (pointers and strings)
            noise_words = [struct.pack("<Q", random.choice([
                0x00007fffa1b2c000, 0x0000555555560000, 0x00007ffff7dd8000,
                0x0000000000000000, 0x0000000000000001, 0x0000000000000020
            ])) for _ in range(PAGE_SIZE // 8)]
            page = b"".join(noise_words)
        pages.append(bytearray(page))

    # 2. Inject realistic System Processes (Decoy: systemd, sshd, rsyslog)
    decoy_sshd = (
        b"sshd: accepted publickey for root from 10.207.1.1 port 52182 ssh2\x00"
        b"PAM: pam_unix(sshd:session): session opened for user root by (uid=0)\x00"
        b"TERM=xterm-256color\x00LANG=en_US.UTF-8\x00USER=root\x00HOME=/root\x00"
    )
    pages[120][:len(decoy_sshd)] = decoy_sshd

    # 3. Inject Culprit TA Piyush's Bash Process Memory (PID 1337)
    # Page A: Process Task Descriptor & Heap Metadata
    task_info = (
        b"COMM=bash\x00PID=1337\x00PPID=1330\x00UID=1002\x00EUID=1002\x00"
        b"TTY=/dev/pts/1\x00EXE=/bin/bash\x00CWD=/home/ta_piyush\x00"
    )
    pages[350][:len(task_info)] = task_info

    # Page B: Authentic Environment Vector Block (environ)
    env_vars = [
        "SHELL=/bin/bash",
        "SESSION_MANAGER=local/gict-lab207-pc04:@/tmp/.ICE-unix/1337",
        "QT_ACCESSIBILITY=1",
        "COLORTERM=truecolor",
        "SSH_CONNECTION=10.207.42.19 54210 10.207.1.5 22",
        "HISTCONTROL=ignoredups",
        "HISTSIZE=1000",
        "HOSTNAME=gict-lab207-pc04",
        "PWD=/home/ta_piyush",
        "LOGNAME=ta_piyush",
        "XDG_SESSION_TYPE=x11",
        "TARGET_VAULT=https://faculty.ahduni.edu.in/vault/oop99",
        f"EXAM_EXFIL_FLAG={FLAG}",
        "MOTIVE=revenge_for_unfair_os101_fail_grade",
        "CULPRIT_ID=ta_piyush",
        "HOME=/home/ta_piyush",
        "LANG=en_US.UTF-8",
        "SSH_CLIENT=10.207.42.19 54210 22",
        "USER=ta_piyush",
        "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "HISTFILE=/home/ta_piyush/.bash_history",
        "_="
    ]
    env_block = b"\x00".join(v.encode("utf-8") for v in env_vars) + b"\x00\x00"
    pages[351][:len(env_block)] = env_block

    # Page C: Bash Command History Ring Buffer (history entries)
    bash_history_lines = [
        "whoami",
        "uptime",
        "ip -br a",
        "ping -c 2 faculty.ahduni.edu.in",
        f'export EXAM_EXFIL_FLAG="{FLAG}"',
        'curl -k -H "X-Vault-Auth: $EXAM_EXFIL_FLAG" https://faculty.ahduni.edu.in/vault/oop99/exam_draft_v1.pdf -o /tmp/exam_draft.pdf',
        "ls -la /tmp/exam_draft.pdf",
        "base64 /tmp/exam_draft.pdf > /dev/shm/exfil.b64",
        "split -b 8000 /dev/shm/exfil.b64 /dev/shm/part",
        "rm -f /tmp/exam_draft.pdf",
        "history -w",
        "unset HISTFILE",
        "echo 'tracks cleaned'"
    ]
    hist_block = b"\n".join(cmd.encode("utf-8") for cmd in bash_history_lines) + b"\n"
    pages[352][:len(hist_block)] = hist_block

    # 4. Inject Staged RAM File Buffer (/dev/shm staging artifacts in memory)
    shm_manifest = (
        b"[SHM_TMPFS_ALLOCATION]\n"
        b"/dev/shm/exfil.b64 (size: 71093 bytes, inode: 40921)\n"
        b"/dev/shm/part01.txt ... part12.txt\n"
        b"AUTH_HEADER: Bearer case{volatility3_lab207_terminal_ram}\n"
    )
    pages[512][:len(shm_manifest)] = shm_manifest

    # Combine all pages with LiME header
    final_dump = lime_header + b"".join(pages)

    FILES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_RAW.write_bytes(final_dump)
    print(f"[+] Memory dump created at: {OUTPUT_RAW} ({len(final_dump)} bytes / {len(final_dump)/(1024*1024):.1f} MB)")


def main():
    print("[*] Generating 'Physical Forensics: Lab 207 Terminal RAM Dump' artifacts...")
    generate_memory_dump()
    print("[+] Done.")


if __name__ == "__main__":
    main()
