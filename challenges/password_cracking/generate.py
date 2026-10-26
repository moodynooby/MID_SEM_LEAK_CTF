#!/usr/bin/env python3
"""
Challenge Artifact Generator: Faculty Vault & Campus Wordlist
Track: Binary & Crypto / Custom Password Cracking
Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)

Generates confidential_vault.zip encrypted with campus lore entity password:
'GICT207_OS101_Piyush2026!'
"""

import os
import sys
import shutil
import zipfile
import tempfile
import subprocess
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent
DIST_DIR = CHALLENGE_DIR / "files"
OUTPUT_ZIP = DIST_DIR / "confidential_vault.zip"

PASSWORD = "GICT207_OS101_Piyush2026!"
FLAG = "case{custom_hashcat_wordlist_cracked_vault}"

EXAM_CONTENT = """================================================================================
AHMEDABAD UNIVERSITY - SCHOOL OF ENGINEERING AND APPLIED SCIENCE
DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING
MID-SEMESTER EXAMINATION - OCTOBER 2026
COURSE: OOP 99 (OBJECT ORIENTED PROGRAMMING SYSTEMS)
INSTRUCTOR: PROF. HASMUKH CHELAIYA
VENUE: GICT LAB 207 / 208
TIME ALLOWED: 2 HOURS                                          MAX MARKS: 50
================================================================================

CONFIDENTIAL FACULTY MASTER COPY - DO NOT CIRCULATE OR REPRODUCE
AUTHORIZATION HASH: SHA256(chelaiya_oop99_master_2026)

--------------------------------------------------------------------------------
SECTION A: MEMORY MODELS, VIRTUAL TABLES & INHERITANCE [20 MARKS]
--------------------------------------------------------------------------------
Q1. (10 Marks)
Consider the following polymorphic class hierarchy in C++:

    class Base {
    public:
        virtual void render() { std::cout << "Base::render" << std::endl; }
        virtual ~Base() {}
    };

    class Derived : public Base {
    public:
        void render() override { std::cout << "Derived::render" << std::endl; }
    };

Trace the layout of the virtual method table pointer (_vptr) across 64-bit Linux
GCC execution. If a rogue TA overrides the vtable entry at runtime via memory
corruption, explain how control flow integrity (CFI) can detect the diversion.

Q2. (10 Marks)
Explain why multiple inheritance with virtual base classes requires diamond
resolution offset pointers in the object layout. Provide the memory diagram for:
    class PoweredDevice { int powerRating; };
    class Scanner : virtual public PoweredDevice { ... };
    class Printer : virtual public PoweredDevice { ... };
    class Copier : public Scanner, public Printer { ... };

--------------------------------------------------------------------------------
SECTION B: CONCURRENCY HAZARDS & GRADING PENALTIES [15 MARKS]
--------------------------------------------------------------------------------
Q3. (15 Marks)
A teaching assistant implements an automated assignment grading queue using a
lock-free ring buffer. Due to memory reordering on weakly-ordered architectures
(ARM64), student submissions suffer race conditions.

Prof. Chelaiya noted: "Any TA submitting flawed concurrency logic will receive
a non-negotiable deduction in OS 101." Identify the required std::memory_order
fences to eliminate the race condition.

--------------------------------------------------------------------------------
SECTION C: EXAM MASTER AUDIT TOKEN [15 MARKS]
--------------------------------------------------------------------------------
Q4. (15 Marks)
Verify the master exam release token recorded in faculty_vault_flag.txt.
"""

NOTE_CONTENT = """[!] SECURITY AUDIT ADVISORY - GICT LAB 207
TO: Prof. Hasmukh Chelaiya
FROM: TA Piyush Pelaiya
DATE: 27-Oct-2026 21:14 IST

Prof. Chelaiya,
You harshly penalized my OS 101 assignment for minor threading discrepancies,
claiming 'attention to detail is mandatory for system administrators'.

Yet, you secured your master OOP 99 exam vault using a predictable pattern:
[Lab Number]_[Course Code]_[Suspect Name][Year]!

Perhaps next semester you will re-evaluate who lacks attention to detail.
- Piyush
"""

def generate_vault():
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        exam_file = tmp_path / "OOP99_Exam_Master_CONFIDENTIAL.txt"
        exam_file.write_text(EXAM_CONTENT, encoding="utf-8")

        flag_file = tmp_path / "faculty_vault_flag.txt"
        flag_file.write_text(f"{FLAG}\n", encoding="utf-8")

        note_file = tmp_path / "piyush_exfiltration_note.txt"
        note_file.write_text(NOTE_CONTENT, encoding="utf-8")

        # Create password protected zip
        # Using zip CLI for standard PKZIP compatible encryption
        if OUTPUT_ZIP.exists():
            OUTPUT_ZIP.unlink()

        cmd = [
            "zip",
            "-P", PASSWORD,
            "-j",
            str(OUTPUT_ZIP),
            str(exam_file),
            str(flag_file),
            str(note_file),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[-] zip command failed: {res.stderr}")
            sys.exit(1)

    # Test decryption with zipfile
    with zipfile.ZipFile(OUTPUT_ZIP, "r") as z:
        extracted = z.read("faculty_vault_flag.txt", pwd=PASSWORD.encode()).decode().strip()
        assert extracted == FLAG, f"Decryption check failed! Got {extracted}"

    print(f"[+] Successfully generated: {OUTPUT_ZIP}")
    print(f"[+] Password verified: {PASSWORD}")
    print(f"[+] Flag inside: {FLAG}")
    print(f"[+] Archive size: {OUTPUT_ZIP.stat().st_size} bytes")

if __name__ == "__main__":
    generate_vault()
