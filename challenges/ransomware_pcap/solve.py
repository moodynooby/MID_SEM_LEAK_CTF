#!/usr/bin/env python3
"""
solve.py — Automated Solver for 'Ransomware Infected: Backdoor Web Shell in PCAP'
Track: Network & Forensics | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Vatsal Pandya (@VP1107)

Solve Path:
    1. Parse raw packets from 'files/infected.pcap'.
    2. Filter for HTTP POST traffic communicating with the faculty server (10.20.0.12).
    3. Isolate the webshell conversation targeting '/assets/vendor.php'.
    4. Extract the custom XOR session key from the 'X-Session-Key' header.
    5. Decrypt the hex-encoded response payload using the extracted XOR key.
    6. Extract and verify the true flag:
       case{pcap_webshell_exfil_key_found}
"""

import sys
import struct
import re
from pathlib import Path

TARGET_FLAG = "case{pcap_webshell_exfil_key_found}"
KNOWN_DECOYS = {
    "case{decoy_plaintext_login_honeyflag}",
    "case{decoy_telemetry_post_pcap}",
}


def xor_crypt(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def parse_pcap_packets(pcap_path: Path) -> list[bytes]:
    """Parse raw link-layer frames from a standard PCAP file."""
    with open(pcap_path, "rb") as f:
        ghdr = f.read(24)
        if len(ghdr) < 24:
            return []
        magic = struct.unpack("<I", ghdr[:4])[0]
        if magic not in (0xA1B2C3D4, 0xD4C3B2A1):
            print(f"[-] Invalid PCAP magic number: {hex(magic)}")
            return []

        packets = []
        while True:
            phdr = f.read(16)
            if len(phdr) < 16:
                break
            ts_sec, ts_usec, incl_len, orig_len = struct.unpack("<IIII", phdr)
            frame = f.read(incl_len)
            packets.append(frame)
    return packets


def extract_tcp_payload(frame: bytes) -> tuple[str, str, int, int, bytes]:
    """Extract (src_ip, dst_ip, src_port, dst_port, tcp_payload)."""
    if len(frame) < 34:
        return ("", "", 0, 0, b"")
    eth_type = struct.unpack("!H", frame[12:14])[0]
    if eth_type != 0x0800:
        return ("", "", 0, 0, b"")

    ip_hdr = frame[14:]
    ihl = (ip_hdr[0] & 0x0F) * 4
    proto = ip_hdr[9]
    if proto != 6:
        return ("", "", 0, 0, b"")

    src_ip = ".".join(str(b) for b in ip_hdr[12:16])
    dst_ip = ".".join(str(b) for b in ip_hdr[16:20])

    tcp_hdr = ip_hdr[ihl:]
    data_offset = ((tcp_hdr[12] >> 4) & 0x0F) * 4
    src_port, dst_port = struct.unpack("!HH", tcp_hdr[:4])
    payload = tcp_hdr[data_offset:]
    return (src_ip, dst_ip, src_port, dst_port, payload)


def solve(pcap_file: Path):
    if not pcap_file.exists():
        print(f"[-] Target PCAP file does not exist: {pcap_file}")
        sys.exit(1)

    print(f"[*] Analyzing packet capture: {pcap_file}")
    frames = parse_pcap_packets(pcap_file)
    print(f"[+] Total packets read: {len(frames)}")

    http_messages = []
    for frame in frames:
        src_ip, dst_ip, src_p, dst_p, payload = extract_tcp_payload(frame)
        if payload.startswith(b"POST ") or payload.startswith(b"HTTP/1.1 200"):
            http_messages.append((src_ip, dst_ip, src_p, dst_p, payload))

    print(f"[+] Discovered {len(http_messages)} HTTP POST / response streams.\n")

    isolated_key = None
    target_response_payload = None

    for src_ip, dst_ip, src_p, dst_p, payload in http_messages:
        text = payload.decode("latin-1", errors="replace")

        # Check for plain text decoy flags
        for dec in KNOWN_DECOYS:
            if dec in text:
                print(f"  [-] Detected decoy honeyflag in plaintext stream: {dec}")

        # Check for Webshell interaction with /assets/vendor.php
        if "POST /assets/vendor.php" in text:
            print(f"  [!] Webshell Request Identified:")
            print(f"      Endpoint: POST /assets/vendor.php from {src_ip}:{src_p}")
            key_match = re.search(r"X-Session-Key:\s*([^\r\n]+)", text)
            if key_match:
                isolated_key = key_match.group(1).strip()
                print(f"      ==> [!] Isolated XOR Session Key: '{isolated_key}'")

        # Check for Webshell encrypted response
        if isolated_key and dst_p == 49152 and "HTTP/1.1 200 OK" in text:
            print(f"  [!] Webshell Response Identified (Server -> {dst_ip}:{dst_p})")
            parts = payload.split(b"\r\n\r\n", 1)
            if len(parts) == 2:
                target_response_payload = parts[1].strip()

    if not isolated_key:
        print("[-] Forensic triage failed: X-Session-Key not located in POST headers.")
        sys.exit(1)

    if not target_response_payload:
        print("[-] Failed to extract encrypted response payload from webshell stream.")
        sys.exit(1)

    print(f"\n[*] Decrypting response payload ({len(target_response_payload)} hex bytes)...")
    enc_bytes = bytes.fromhex(target_response_payload.decode("ascii"))
    decrypted_bytes = xor_crypt(enc_bytes, isolated_key.encode("ascii"))
    decrypted_text = decrypted_bytes.decode("utf-8", errors="replace")

    print("[*] Decrypted Stream Content:")
    for line in decrypted_text.strip().split("\n"):
        print(f"    {line}")

    flag_match = re.search(r"case\{[^}]+\}", decrypted_text)
    extracted_flag = flag_match.group(0) if flag_match else None

    print("\n" + "=" * 60)
    print("PCAP WEBSHELL SOLVER VERIFICATION RESULTS:")
    print(f"  Isolated XOR Key:   {isolated_key}")
    print(f"  Extracted Flag:     {extracted_flag}")
    print(f"  Expected Flag:      {TARGET_FLAG}")
    print("=" * 60)

    if extracted_flag == TARGET_FLAG:
        print("[+] SUCCESS: Challenge verified cleanly! Extracted flag matches expected.")
        sys.exit(0)
    else:
        print("[-] FAILURE: Flag mismatch or extraction failure.")
        sys.exit(1)


def main():
    repo_root = Path(__file__).resolve().parent
    pcap_path = repo_root / "files" / "infected.pcap"
    solve(pcap_path)


if __name__ == "__main__":
    main()
