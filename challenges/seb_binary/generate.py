#!/usr/bin/env python3
"""
generate.py — Build pipeline for SEB_KioskGuard.exe CTF challenge.

Compile once with sentinel placeholders, then binary-patch the EXE.
CIPHERTEXT (0xBB*44) and EXPECTED_TEXT_HASH (0xDEADBEEF) live in .rdata
thanks to `volatile`, so patching them leaves .text untouched.
"""

import struct
import subprocess
import sys
import os
import shutil

FLAG = b"case{seb_win_pe_lockdown_integrity_bypassed}"
FLAG_LEN = 44
assert len(FLAG) == FLAG_LEN

K_BASE = bytes([
    0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE,
    0x13, 0x37, 0x42, 0x00, 0xF0, 0x0D, 0xC0, 0xDE
])

SBOX = [
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
]

CT_SENTINEL = b'\xBB' * FLAG_LEN
HASH_SENTINEL = struct.pack("<I", 0xDEADBEEF)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(SCRIPT_DIR, "src", "seb_guard.c")
OUT_DIR = os.path.join(SCRIPT_DIR, "files")
OUT_EXE = os.path.join(OUT_DIR, "SEB_KioskGuard.exe")


def find_compiler():
    for cc in ["x86_64-w64-mingw32-gcc", "gcc"]:
        if shutil.which(cc):
            return cc
    print("ERROR: No compiler found.", file=sys.stderr)
    sys.exit(1)


def compile_exe(src, out, cc):
    cmd = [cc, "-O2", "-s", "-o", out, src, "-lkernel32", "-luser32", "-ladvapi32"]
    print(f"  {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"Compilation failed:\n{r.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"  -> {out} ({os.path.getsize(out)} bytes)")


def get_section_info(data):
    """Return dict of section name -> (file_offset, raw_size) for all PE sections."""
    assert data[:2] == b"MZ"
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[e_lfanew:e_lfanew+4] == b"PE\x00\x00"
    num_sec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
    opt_sz = struct.unpack_from("<H", data, e_lfanew + 20)[0]
    sec_start = e_lfanew + 24 + opt_sz
    sections = {}
    for i in range(num_sec):
        off = sec_start + i * 40
        name = data[off:off+8].rstrip(b"\x00").decode("ascii", errors="replace")
        raw_size = struct.unpack_from("<I", data, off + 16)[0]
        raw_ptr = struct.unpack_from("<I", data, off + 20)[0]
        sections[name] = (raw_ptr, raw_size)
    return sections


def fnv1a_32(data_bytes):
    h = 0x811c9dc5
    for b in data_bytes:
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def encrypt_flag(flag_bytes, h_text):
    ct = bytearray(len(flag_bytes))
    for i in range(len(flag_bytes)):
        step1 = flag_bytes[i] ^ K_BASE[(i + h_text) % 16]
        step2 = (step1 + SBOX[(i * 7) % 256]) & 0xFF
        ct[i] = step2
    return bytes(ct)


def decrypt_flag(ct_bytes, h_text):
    pt = bytearray(len(ct_bytes))
    for i in range(len(ct_bytes)):
        step1 = (ct_bytes[i] - SBOX[(i * 7) % 256]) & 0xFF
        step2 = step1 ^ K_BASE[(i + h_text) % 16]
        pt[i] = step2
    return bytes(pt)


def find_in_section(data, sections, sec_name, pattern, label):
    """Find pattern within a specific PE section. Return file offset."""
    if sec_name not in sections:
        raise ValueError(f"Section {sec_name} not found")
    sec_off, sec_size = sections[sec_name]
    sec_data = data[sec_off:sec_off + sec_size]
    idx = sec_data.find(pattern)
    if idx == -1:
        raise ValueError(f"{label} sentinel not found in {sec_name}")
    # Verify uniqueness
    if sec_data.find(pattern, idx + 1) != -1:
        raise ValueError(f"{label} sentinel is not unique in {sec_name}")
    return sec_off + idx


def main():
    print("=" * 60)
    print("  SEB_KioskGuard.exe — Challenge Build Pipeline")
    print("=" * 60)

    cc = find_compiler()
    print(f"\n[1/5] Compiler: {cc}")
    os.makedirs(OUT_DIR, exist_ok=True)

    print("\n[2/5] Compiling with sentinel values...")
    compile_exe(SRC_PATH, OUT_EXE, cc)

    print("\n[3/5] Analyzing PE sections...")
    with open(OUT_EXE, "rb") as f:
        exe_data = bytearray(f.read())

    sections = get_section_info(exe_data)
    for name, (off, sz) in sections.items():
        print(f"  {name:8s}  offset=0x{off:04x}  size={sz}")

    # Compute .text hash
    text_off, text_size = sections[".text"]
    text_bytes = exe_data[text_off:text_off + text_size]
    h_text = fnv1a_32(text_bytes)
    print(f"\n  .text FNV-1a hash: 0x{h_text:08x}")

    # Find sentinels — check .rdata first, fall back to scanning whole file
    rdata_name = ".rdata" if ".rdata" in sections else ".data"
    print(f"\n  Searching for sentinels in {rdata_name}...")

    ct_offset = find_in_section(exe_data, sections, rdata_name, CT_SENTINEL, "CIPHERTEXT")
    print(f"  CIPHERTEXT sentinel at file offset 0x{ct_offset:04x}")

    hash_offset = find_in_section(exe_data, sections, rdata_name, HASH_SENTINEL, "HASH")
    print(f"  HASH sentinel at file offset 0x{hash_offset:04x}")

    # Verify sentinels are NOT in .text
    assert not (text_off <= ct_offset < text_off + text_size), "CIPHERTEXT is in .text!"
    assert not (text_off <= hash_offset < text_off + text_size), "HASH is in .text!"
    print("  Both sentinels confirmed outside .text")

    print("\n[4/5] Encrypting flag...")
    ciphertext = encrypt_flag(FLAG, h_text)
    print(f"  Ciphertext: {ciphertext.hex()}")
    assert decrypt_flag(ciphertext, h_text) == FLAG
    print("  Round-trip: PASSED")

    print("\n[5/5] Binary-patching EXE...")
    exe_data[ct_offset:ct_offset + FLAG_LEN] = ciphertext
    print("  Ciphertext patched.")

    hash_bytes = struct.pack("<I", h_text)
    exe_data[hash_offset:hash_offset + 4] = hash_bytes
    print(f"  Hash patched: 0x{h_text:08x}")

    # Verify .text unchanged
    text_bytes2 = exe_data[text_off:text_off + text_size]
    h_verify = fnv1a_32(text_bytes2)
    assert h_verify == h_text, f".text changed! 0x{h_text:08x} -> 0x{h_verify:08x}"
    print("  .text integrity: PRESERVED")

    with open(OUT_EXE, "wb") as f:
        f.write(exe_data)

    dec = decrypt_flag(ciphertext, h_text)
    print(f"\n  Flag: {dec.decode()}")
    print(f"  Output: {OUT_EXE} ({len(exe_data)} bytes)")
    print("\n" + "=" * 60)
    print("  BUILD SUCCESSFUL")
    print("=" * 60)


if __name__ == "__main__":
    main()
