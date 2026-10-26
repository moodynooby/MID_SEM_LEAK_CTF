#!/usr/bin/env python3
"""
solve.py — Automated Solver for 'PDF Hidden Text: The Redacted Exam Paper'
Track: Forensics & Stego | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Yesha (Forensics Track Lead)

Walkthrough Solution:
    1. The distributed PDF (OOP99_Exam_Paper_REDACTED.pdf) visually obscures Section C
       with a solid black rectangle.
    2. However, the redaction is purely cosmetic and the underlying text stream was not
       sanitized or flattened.
    3. The flag can be extracted using any of the following standard techniques:
       a) Shell one-liner:
          pdftotext OOP99_Exam_Paper_REDACTED.pdf - | grep "case{"
       b) Strings extraction:
          strings OOP99_Exam_Paper_REDACTED.pdf | grep "case{"
       c) Highlight and copy text directly inside any modern PDF reader (Chrome, Preview, Evince).
       d) Python PDF stream decompression / parsing.
"""

import re
import sys
import zlib
import subprocess
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent
PDF_PATH = CHALLENGE_DIR / "files" / "OOP99_Exam_Paper_REDACTED.pdf"
EXPECTED_FLAG = "case{redacted_pdf_layer_text_exposed}"


def solve():
    print(f"[*] Solving PDF Hidden Text challenge from: {PDF_PATH}")
    if not PDF_PATH.exists():
        print(f"[-] Error: Target PDF file {PDF_PATH} does not exist!")
        return False

    pdf_bytes = PDF_PATH.read_bytes()
    flag_pattern = re.compile(r"case\{[a-zA-Z0-9_]+\}")

    found_flag = None

    # Technique 1: Direct stream search (uncompressed or raw content stream)
    matches = flag_pattern.findall(pdf_bytes.decode("latin1", errors="ignore"))
    if matches:
        found_flag = matches[0]
        print(f"[+] Recovered flag via direct PDF content stream inspection: {found_flag}")

    # Technique 2: pdftotext extraction
    if not found_flag:
        try:
            res = subprocess.run(["pdftotext", str(PDF_PATH), "-"], capture_output=True, text=True)
            matches = flag_pattern.findall(res.stdout)
            if matches:
                found_flag = matches[0]
                print(f"[+] Recovered flag via pdftotext extraction: {found_flag}")
        except Exception as e:
            print(f"[-] pdftotext fallback unavailable: {e}")

    # Technique 3: Deflate/FlateDecode stream inspection
    if not found_flag:
        stream_matches = re.findall(rb"stream[\r\n]+(.*?)[\r\n]+endstream", pdf_bytes, re.DOTALL)
        for st in stream_matches:
            # Try raw
            m = flag_pattern.findall(st.decode("latin1", errors="ignore"))
            if m:
                found_flag = m[0]
                break
            # Try zlib inflate
            try:
                decomp = zlib.decompress(st)
                m = flag_pattern.findall(decomp.decode("latin1", errors="ignore"))
                if m:
                    found_flag = m[0]
                    break
            except Exception:
                continue

    if found_flag == EXPECTED_FLAG:
        print(f"[SUCCESS] Validated Flag: {found_flag}")
        return True
    else:
        print(f"[-] Failed to validate expected flag. Found: {found_flag}")
        return False


if __name__ == "__main__":
    success = solve()
    sys.exit(0 if success else 1)
