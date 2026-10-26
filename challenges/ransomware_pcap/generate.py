#!/usr/bin/env python3
"""
generate.py — Artifact Generator for 'Ransomware Infected: Backdoor Web Shell in PCAP'
Track: Network & Forensics | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Vatsal Pandya (@VP1107)

Generates:
    challenges/ransomware_pcap/files/infected.pcap

Storyline Context:
    TA Piyush Pelaiya established an encrypted backdoor connection to a webshell
    planted in the faculty share (/assets/vendor.php). The command and exfiltrated exam
    metadata are XOR-encrypted over the HTTP POST stream using a session key passed in
    the custom HTTP header 'X-Session-Key'.

Anti-AI Defensive Layer:
    - Pure binary packet capture with realistic multi-stream TCP conversations.
    - XOR-encrypted HTTP payload; plaintext strings / regex scans will fail to locate the flag.
    - Decoy HTTP streams with plain-text decoy flags to catch naive AI solvers:
      * case{decoy_plaintext_login_honeyflag}
      * case{decoy_telemetry_post_pcap}

True Flag:
    case{pcap_webshell_exfil_key_found}
"""

import struct
import socket
from pathlib import Path

PCAP_GLOBAL_HEADER = struct.pack(
    "<IHHiIII",
    0xA1B2C3D4,  # Magic number (microseconds)
    2,           # Major version
    4,           # Minor version
    0,           # Gmt to local correction
    0,           # Accuracy of timestamps
    65535,       # Max length of captured packets
    1,           # Data link type (Ethernet)
)

TARGET_KEY = b"midsem_leaked_key_99"
TARGET_FLAG = "case{pcap_webshell_exfil_key_found}"


def checksum(data: bytes) -> int:
    if len(data) % 2:
        data += b"\x00"
    s = sum(int.from_bytes(data[i : i + 2], "big") for i in range(0, len(data), 2))
    while s >> 16:
        s = (s & 0xFFFF) + (s >> 16)
    return ~s & 0xFFFF


def xor_crypt(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def build_ip_header(src_ip: str, dst_ip: str, payload_len: int, proto=6, ident=54321) -> bytes:
    version_ihl = (4 << 4) | 5
    tos = 0
    total_len = 20 + payload_len
    flags_offset = 0x4000  # Don't fragment
    ttl = 64
    src_bytes = socket.inet_aton(src_ip)
    dst_bytes = socket.inet_aton(dst_ip)
    hdr_without_cksum = struct.pack(
        "!BBHHHBBH4s4s",
        version_ihl,
        tos,
        total_len,
        ident,
        flags_offset,
        ttl,
        proto,
        0,
        src_bytes,
        dst_bytes,
    )
    cksum = checksum(hdr_without_cksum)
    return struct.pack(
        "!BBHHHBBH4s4s",
        version_ihl,
        tos,
        total_len,
        ident,
        flags_offset,
        ttl,
        proto,
        cksum,
        src_bytes,
        dst_bytes,
    )


def build_tcp_packet(
    src_mac: bytes,
    dst_mac: bytes,
    src_ip: str,
    dst_ip: str,
    src_port: int,
    dst_port: int,
    seq: int,
    ack: int,
    flags: int,
    payload: bytes = b"",
    ts_sec: int = 1793155500,
    ts_usec: int = 0,
) -> bytes:
    eth_hdr = dst_mac + src_mac + struct.pack("!H", 0x0800)
    tcp_len = 20 + len(payload)
    offset_reserved = (5 << 4)
    window = 64240

    # Pseudo-header for TCP checksum
    pseudo = (
        socket.inet_aton(src_ip)
        + socket.inet_aton(dst_ip)
        + struct.pack("!BBH", 0, 6, tcp_len)
    )
    tcp_hdr_no_cksum = struct.pack(
        "!HHIIBBHHH",
        src_port,
        dst_port,
        seq,
        ack,
        offset_reserved,
        flags,
        window,
        0,
        0,
    )
    tcp_cksum = checksum(pseudo + tcp_hdr_no_cksum + payload)
    tcp_hdr = struct.pack(
        "!HHIIBBHHH",
        src_port,
        dst_port,
        seq,
        ack,
        offset_reserved,
        flags,
        window,
        tcp_cksum,
        0,
    )

    ip_hdr = build_ip_header(src_ip, dst_ip, tcp_len, proto=6, ident=(seq & 0xFFFF))
    frame = eth_hdr + ip_hdr + tcp_hdr + payload

    pcap_rec_hdr = struct.pack("<IIII", ts_sec, ts_usec, len(frame), len(frame))
    return pcap_rec_hdr + frame


def generate_tcp_conversation(
    client_mac: bytes,
    server_mac: bytes,
    client_ip: str,
    server_ip: str,
    client_port: int,
    server_port: int,
    request_data: bytes,
    response_data: bytes,
    base_ts: int,
) -> list[bytes]:
    packets = []
    c_seq = 1000000 + client_port * 10
    s_seq = 5000000 + client_port * 10
    us = 100000

    # 1. SYN
    packets.append(
        build_tcp_packet(
            client_mac, server_mac, client_ip, server_ip, client_port, server_port,
            c_seq, 0, 0x02, b"", base_ts, us
        )
    )
    c_seq += 1
    us += 1500

    # 2. SYN-ACK
    packets.append(
        build_tcp_packet(
            server_mac, client_mac, server_ip, client_ip, server_port, client_port,
            s_seq, c_seq, 0x12, b"", base_ts, us
        )
    )
    s_seq += 1
    us += 1200

    # 3. ACK
    packets.append(
        build_tcp_packet(
            client_mac, server_mac, client_ip, server_ip, client_port, server_port,
            c_seq, s_seq, 0x10, b"", base_ts, us
        )
    )
    us += 3000

    # 4. HTTP Request (PSH-ACK)
    packets.append(
        build_tcp_packet(
            client_mac, server_mac, client_ip, server_ip, client_port, server_port,
            c_seq, s_seq, 0x18, request_data, base_ts, us
        )
    )
    c_seq += len(request_data)
    us += 15000

    # 5. HTTP Response (PSH-ACK)
    packets.append(
        build_tcp_packet(
            server_mac, client_mac, server_ip, client_ip, server_port, client_port,
            s_seq, c_seq, 0x18, response_data, base_ts, us
        )
    )
    s_seq += len(response_data)
    us += 2000

    # 6. Final ACK
    packets.append(
        build_tcp_packet(
            client_mac, server_mac, client_ip, server_ip, client_port, server_port,
            c_seq, s_seq, 0x10, b"", base_ts, us
        )
    )
    return packets


def build_pcap(output_path: Path):
    client_mac = b"\x00\x50\x56\xc0\x00\x27"
    server_mac = b"\x00\x1a\x1e\xf0\x20\x70"
    decoy_mac1 = b"\x3c\x52\x82\x11\x22\x33"
    decoy_mac2 = b"\x70\x85\xc2\x77\x88\x99"

    packets = [PCAP_GLOBAL_HEADER]
    base_time = 1793155500  # Oct 28 2026, approx 02:45:00 IST

    # Conversation 1: Decoy student login (Plaintext Honeyflag)
    req1 = (
        b"POST /auth/login.php HTTP/1.1\r\n"
        b"Host: portal.gict.internal\r\n"
        b"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n"
        b"Content-Type: application/x-www-form-urlencoded\r\n"
        b"Content-Length: 72\r\n\r\n"
        b"user=student_rohan&token=case{decoy_plaintext_login_honeyflag}&action=login"
    )
    res1 = (
        b"HTTP/1.1 200 OK\r\n"
        b"Server: Apache/2.4.52\r\n"
        b"Content-Type: text/html\r\n"
        b"Content-Length: 43\r\n\r\n"
        b"<html><body>Login successful</body></html>\n"
    )
    packets.extend(
        generate_tcp_conversation(
            decoy_mac1, server_mac, "10.100.14.22", "10.20.0.12", 51201, 80, req1, res1, base_time
        )
    )

    # Conversation 2: Background normal GET traffic
    req2 = (
        b"GET /assets/style.css HTTP/1.1\r\n"
        b"Host: portal.gict.internal\r\n"
        b"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n"
        b"\r\n"
    )
    res2 = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/css\r\n"
        b"Content-Length: 48\r\n\r\n"
        b"body { background: #0a0e17; color: #00ffcc; }\n"
    )
    packets.extend(
        generate_tcp_conversation(
            decoy_mac2, server_mac, "10.100.18.91", "10.20.0.12", 51202, 80, req2, res2, base_time + 4
        )
    )

    # Conversation 3: Decoy telemetry post
    req3 = (
        b"POST /api/telemetry HTTP/1.1\r\n"
        b"Host: portal.gict.internal\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: 62\r\n\r\n"
        b'{"audit": "metric", "decoy_flag": "case{decoy_telemetry_post_pcap}"}'
    )
    res3 = b"HTTP/1.1 200 OK\r\nContent-Length: 15\r\n\r\n{\"status\":\"ok\"}\n"
    packets.extend(
        generate_tcp_conversation(
            decoy_mac1, server_mac, "10.100.14.22", "10.20.0.12", 51203, 80, req3, res3, base_time + 8
        )
    )

    # Conversation 4: THE GENUINE MALICIOUS WEBSHELL EXFILTRATION SESSION
    # Attacker: TA Piyush Pelaiya (10.207.42.19)
    # Target: Faculty File Server Web Shell (/assets/vendor.php)
    plain_cmd = b"cmd=dump_vault&target=/faculty/vault/OOP99_MidSem_FinalDraft.pdf"
    enc_cmd = xor_crypt(plain_cmd, TARGET_KEY).hex().encode("ascii")

    header_str = (
        "POST /assets/vendor.php HTTP/1.1\r\n"
        "Host: faculty.ahduni.internal\r\n"
        "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0\r\n"
        "Content-Type: application/x-www-form-urlencoded\r\n"
        "X-Session-Key: midsem_leaked_key_99\r\n"
        "X-Requested-With: XMLHttpRequest\r\n"
        f"Content-Length: {len(enc_cmd) + 5}\r\n\r\n"
        "data="
    )
    req4 = header_str.encode("ascii") + enc_cmd

    plain_res = (
        f"EXFILTRATION_SUCCESS\n"
        f"TARGET: OOP99_MidSem_FinalDraft.pdf (SHA256: 8f9b42...)\n"
        f"CONFIRMATION_KEY: {TARGET_FLAG}\n"
        f"STAGING_BUFFER: /tmp/.piyush_exfil_vault/\n"
    ).encode("utf-8")
    enc_res = xor_crypt(plain_res, TARGET_KEY).hex().encode("ascii")

    res_header_str = (
        "HTTP/1.1 200 OK\r\n"
        "Date: Tue, 28 Oct 2026 02:45:12 GMT\r\n"
        "Server: Apache/2.4.52 (Ubuntu)\r\n"
        "X-Powered-By: PHP/8.1.2\r\n"
        "Content-Type: text/plain; charset=UTF-8\r\n"
        f"Content-Length: {len(enc_res)}\r\n\r\n"
    )
    res4 = res_header_str.encode("ascii") + enc_res
    packets.extend(
        generate_tcp_conversation(
            client_mac, server_mac, "10.207.42.19", "10.20.0.12", 49152, 80, req4, res4, base_time + 12
        )
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for p in packets:
            f.write(p)


def main():
    repo_root = Path(__file__).resolve().parent
    out_file = repo_root / "files" / "infected.pcap"
    print(f"[*] Building challenge PCAP: {out_file}")
    build_pcap(out_file)
    print(f"[+] Successfully generated: {out_file} ({out_file.stat().st_size} bytes)")
    print(f"[+] Target Webshell Endpoint: POST /assets/vendor.php")
    print(f"[+] XOR Decryption Key: {TARGET_KEY.decode('ascii')}")
    print(f"[+] Verified True Flag: {TARGET_FLAG}")


if __name__ == "__main__":
    main()
