#!/usr/bin/env python3
"""
Automated Solver & Verification Script: Faculty Vault & Campus Wordlist
Track: Binary & Crypto / Custom Password Cracking
Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)

Synthesizes targeted campus dictionary from Case Briefing Dossier clues
and cracks confidential_vault.zip.
"""

import sys
import zipfile
import itertools
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent
VAULT_ZIP = CHALLENGE_DIR / "files" / "confidential_vault.zip"
DOSSIER_PATH = CHALLENGE_DIR.parent.parent / "docs" / "participant_kit" / "Case_Briefing_Dossier.md"

EXPECTED_FLAG = "case{custom_hashcat_wordlist_cracked_vault}"

def build_targeted_wordlist():
    """
    Constructs a targeted wordlist using the lore entities from the Case Dossier:
    Pattern: [Lab]_[Course]_[Suspect][Year][Symbol]
    """
    labs = ["GICT207", "GICT208", "207", "208", "Lab207", "Lab208"]
    courses = ["OS101", "OOP99", "CSE205", "OS", "OOP"]
    suspects = [
        "Piyush", "Pelaiya", "Hasmukh", "Chelaiya",
        "Rohan", "Vikram", "Ananya", "Siddharth", "Pooja"
    ]
    years = ["2026", "2025", "26"]
    symbols = ["!", "@", "#", "$", ""]
    delimiters = ["_", "-", ""]

    candidates = []
    # Pattern 1: Lab_Course_SuspectYearSymbol
    for lab, delim1, course, delim2, suspect, yr, sym in itertools.product(
        labs, delimiters, courses, delimiters, suspects, years, symbols
    ):
        candidates.append(f"{lab}{delim1}{course}{delim2}{suspect}{yr}{sym}")

    return candidates

def crack_vault():
    if not VAULT_ZIP.exists():
        print(f"[-] Target archive not found at {VAULT_ZIP}. Run generate.py first.")
        sys.exit(1)

    print(f"[*] Targeting encrypted archive: {VAULT_ZIP}")
    if DOSSIER_PATH.exists():
        print(f"[*] Extracting case intelligence from: {DOSSIER_PATH}")
    else:
        print("[*] Using pre-compiled campus dossier entities...")

    wordlist = build_targeted_wordlist()
    print(f"[*] Generated targeted dictionary: {len(wordlist)} candidates")
    print("[*] Initiating dictionary attack against PKZIP vault...")

    cracked_password = None
    extracted_flag = None

    with zipfile.ZipFile(VAULT_ZIP, "r") as z:
        for pwd in wordlist:
            try:
                data = z.read("faculty_vault_flag.txt", pwd=pwd.encode("utf-8"))
                cracked_password = pwd
                extracted_flag = data.decode("utf-8").strip()
                break
            except (RuntimeError, zipfile.BadZipFile):
                continue

    if not cracked_password:
        print("[-] FAILED: Password could not be cracked with targeted wordlist.")
        return 1

    print(f"[+] CRACKED! Password: {cracked_password}")
    print(f"[+] Recovered Flag: {extracted_flag}")

    if extracted_flag == EXPECTED_FLAG:
        print("[+] SUCCESS: Flag verified successfully!")
        return 0
    else:
        print(f"[-] ERROR: Flag mismatch! Expected '{EXPECTED_FLAG}', got '{extracted_flag}'")
        return 1

if __name__ == "__main__":
    sys.exit(crack_vault())
