#!/usr/bin/env python3
"""
solve.py — Automated Solver for 'DNS / Wi-Fi Logs: The 2:13 AM Plot Twist'
Track: Network & Forensics | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Vatsal Pandya (@VP1107)

Solve Path:
    1. Parse 'files/campus_wifi_access.log' for events occurring on the Faculty AP
       (SSID: AU-Faculty-Secure / BSSID: 00:1a:1e:f0:20:70) between 02:00 and 02:30 AM.
    2. Detect connection spike at 02:13:42 IST associated with MAC: a4:c4:94:02:13:42.
    3. Cross-reference MAC address against 'files/dhcp_leases.log' to identify
       the device hostname (prof_chelaiya_thinkpad_x1) and allocated IP (10.20.10.42).
    4. Trace SMB / file-share sync logs for confidential exam draft exfiltration.
    5. Extract and verify the true flag:
       case{chelaiya_thinkpad_auto_sync_0213}
"""

import sys
import re
from pathlib import Path

TARGET_FLAG = "case{chelaiya_thinkpad_auto_sync_0213}"
KNOWN_DECOYS = {
    "case{sansh_laptop_dhcp_lease_vlan100}",
    "case{tryan_guest_mobile_dhcp_auth_0213}",
    "case{parsh_seminar_hall_vlan200_token}",
}


def solve(wifi_path: Path, dhcp_path: Path):
    if not wifi_path.exists() or not dhcp_path.exists():
        print(f"[-] Error: Required log files missing ({wifi_path}, {dhcp_path})")
        sys.exit(1)

    print(f"[*] Analyzing Wi-Fi Access Log: {wifi_path}")
    print(f"[*] Analyzing DHCP Lease Table: {dhcp_path}\n")

    # Step 1: Scan Wi-Fi log for Faculty AP associations between 02:00 and 02:30
    faculty_bssid = "00:1a:1e:f0:20:70"
    target_mac = None
    target_time = None

    with open(wifi_path, "r", encoding="utf-8") as f:
        wifi_lines = f.readlines()

    print("[*] Filtering Wi-Fi events on Faculty AP (00:1a:1e:f0:20:70)...")
    for line in wifi_lines:
        if "02:13:" in line and (faculty_bssid in line.lower() or "faculty" in line.lower()):
            print(f"  [!] Suspicious connection spotted: {line.strip()}")
            mac_match = re.search(r"MAC=([0-9a-fA-F:]{17})", line)
            if mac_match:
                target_mac = mac_match.group(1).lower()
                target_time = "02:13:42"

    if not target_mac:
        print("[-] Failed to isolate connection event on Faculty AP at 02:13 AM.")
        sys.exit(1)

    print(f"\n[+] Isolated Target MAC Address: {target_mac} at {target_time} IST")

    # Step 2: Cross-reference MAC against DHCP lease records
    print(f"[*] Querying DHCP lease table for MAC: {target_mac}...")
    target_hostname = None
    target_ip = None
    dhcp_flag = None

    with open(dhcp_path, "r", encoding="utf-8") as f:
        for line in f:
            if target_mac in line.lower():
                print(f"  [+] DHCP Lease Match: {line.strip()}")
                ip_match = re.search(r"DHCPACK on (\d+\.\d+\.\d+\.\d+)", line)
                host_match = re.search(r"\(([^)]+)\)", line)
                flag_match = re.search(r"case\{[^}]+\}", line)

                if ip_match:
                    target_ip = ip_match.group(1)
                if host_match:
                    target_hostname = host_match.group(1)
                if flag_match:
                    dhcp_flag = flag_match.group(0)

    print(f"[+] Device Identity Confirmed: {target_hostname} ({target_ip})")

    # Step 3: Inspect Wi-Fi / DNS / Share audit logs for exfiltrated file sync
    print("\n[*] Correlating IP traffic for file transfer evidence...")
    traffic_flag = None
    for line in wifi_lines:
        if target_ip and target_ip in line and ("OOP99" in line or "sync" in line.lower()):
            print(f"  [!] Cloud Auto-Sync Evidence: {line.strip()}")
            m = re.search(r"case\{[^}]+\}", line)
            if m:
                traffic_flag = m.group(0)

    # Validate against known decoys
    for cand in [dhcp_flag, traffic_flag]:
        if cand in KNOWN_DECOYS:
            print(f"  [-] Warning: Encountered decoy honeyflag: {cand}")

    extracted_flag = traffic_flag or dhcp_flag

    print("\n" + "=" * 60)
    print("WI-FI / DNS LOG SOLVER VERIFICATION RESULTS:")
    print(f"  Isolated MAC:          {target_mac}")
    print(f"  Resolved Hostname:     {target_hostname}")
    print(f"  Assigned IP:           {target_ip}")
    print(f"  Extracted Flag:        {extracted_flag}")
    print(f"  Expected Flag:         {TARGET_FLAG}")
    print("=" * 60)

    if extracted_flag == TARGET_FLAG:
        print("[+] SUCCESS: Challenge verified cleanly! Extracted flag matches expected.")
        sys.exit(0)
    else:
        print("[-] FAILURE: Flag mismatch or extraction failure.")
        sys.exit(1)


def main():
    repo_root = Path(__file__).resolve().parent
    wifi_file = repo_root / "files" / "campus_wifi_access.log"
    dhcp_file = repo_root / "files" / "dhcp_leases.log"
    solve(wifi_file, dhcp_file)


if __name__ == "__main__":
    main()
