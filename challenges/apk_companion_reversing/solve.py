#!/usr/bin/env python3
"""
Automated Solver & Verification Script: Suspect's Companion App
Track: Binary & Crypto / Mobile Reversing
Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)

Reverses the dynamic XOR key schedule in SecurityVerification.class
recovered from AU_Companion.apk.
"""

import sys
import zipfile
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent
APK_PATH = CHALLENGE_DIR / "files" / "AU_Companion.apk"
EXPECTED_FLAG = "case{apk_decompiled_jadx_secret_extracted}"

def solve():
    if not APK_PATH.exists():
        fallback_apk = CHALLENGE_DIR / "files" / "GICT_Companion.apk"
        if fallback_apk.exists():
            target_apk = fallback_apk
        else:
            print(f"[-] APK file not found at {APK_PATH}. Run generate.py first.")
            sys.exit(1)
    else:
        target_apk = APK_PATH

    print(f"[*] Analyzing Android package: {target_apk}")
    with zipfile.ZipFile(target_apk, "r") as z:
        if "classes.dex" not in z.namelist():
            print("[-] classes.dex not found in APK!")
            sys.exit(1)
        dex_bytes = z.read("classes.dex")

    # Locate known salt string in Dalvik bytecode string pool
    if b"AU_2026_AUTH_KEY_AUSB" in dex_bytes:
        auth_salt = b"AU_2026_AUTH_KEY_AUSB"
    elif b"GICT_2026_AUTH_KEY_AUSB" in dex_bytes:
        auth_salt = b"GICT_2026_AUTH_KEY_AUSB"
    else:
        print("[-] Auth salt not found in DEX string table!")
        sys.exit(1)

    # In SecurityVerification.java, ENC_PAYLOAD has length 42.
    # Searching for known encoded byte sequence in DEX
    # Target flag length = 42
    enc_payload = None
    known_header = bytes([184, 222, 96, 155])
    pos = dex_bytes.find(known_header)
    if pos != -1 and pos + 42 <= len(dex_bytes):
        enc_payload = dex_bytes[pos:pos + 42]
    else:
        # Fallback to searching byte arrays in dex
        for i in range(len(dex_bytes) - 42):
            candidate = dex_bytes[i:i + 42]
            # Try decrypting candidate
            buf = bytearray()
            for idx, b in enumerate(candidate):
                k = auth_salt[idx % len(auth_salt)]
                mask = (0x5a * (idx + 1) + 0x42) & 0xff
                buf.append(b ^ mask ^ k)
            if buf.startswith(b"case{") and buf.endswith(b"}"):
                enc_payload = candidate
                break

    if not enc_payload:
        print("[-] Could not locate ENC_PAYLOAD in classes.dex!")
        sys.exit(1)

    print(f"[*] Found encrypted token payload ({len(enc_payload)} bytes)")
    print(f"[*] Reversing dynamic XOR schedule from SecurityVerification.getMasterKey()...")

    schedule_salt = 0x5a
    decrypted = bytearray()
    for i, b in enumerate(enc_payload):
        k = auth_salt[i % len(auth_salt)]
        mask = (schedule_salt * (i + 1) + 0x42) & 0xff
        decrypted.append(b ^ mask ^ k)

    recovered_flag = decrypted.decode("utf-8", errors="replace")
    print(f"[+] Recovered Token / Flag: {recovered_flag}")

    if recovered_flag == EXPECTED_FLAG:
        print("[+] SUCCESS: Flag verified successfully!")
        return 0
    else:
        print(f"[-] ERROR: Flag mismatch! Expected '{EXPECTED_FLAG}', got '{recovered_flag}'")
        return 1

if __name__ == "__main__":
    sys.exit(solve())
