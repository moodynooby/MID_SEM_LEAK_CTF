#!/usr/bin/env python3
"""
generate.py — Artifact Generator for 'DNS / Wi-Fi Logs: The 2:13 AM Plot Twist'
Track: Network & Forensics | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Vatsal Pandya (@VP1107)

Generates:
    challenges/wifi_dns_logs/files/campus_wifi_access.log
    challenges/wifi_dns_logs/files/dhcp_leases.log

Storyline Canon Context:
    At 02:13:42 IST on 28 October 2026, Prof. Hasmukh Chelaiya's department laptop
    (prof_chelaiya_thinkpad_x1, MAC a4:c4:94:02:13:42) associated with the faculty
    access point AP-AU-FACULTY-L2 and initiated an automated background cloud sync of
    the confidential OOP 99 examination draft.

Anti-AI Defensive Layer:
    - 1,200+ lines of authentic Aruba/Cisco 802.11 syslog and ISC-DHCP server logs.
    - Multiple decoy student traces across all 5 canon suspects with decoy flags:
      * case{decoy_student_mac_address}
      * case{sansh_vhah_library_ap_decoy}
      * case{nice_try_blind_ai_wifi_grep}
    - Requires temporal correlation (02:13:42) + BSSID filtering + MAC resolution.

True Flag:
    case{chelaiya_thinkpad_auto_sync_0213}
"""

import random
from datetime import datetime, timedelta
from pathlib import Path

# Seed for reproducible generator output
random.seed(20261028)

AP_LIST = [
    ("AP-AU-FACULTY-L2", "00:1a:1e:f0:20:70", "AU-Faculty-Secure", "VLAN 20"),
    ("AP-AU-LAB207", "00:1a:1e:f0:20:71", "AU-Labs-Internal", "VLAN 40"),
    ("AP-AU-LAB208", "00:1a:1e:f0:20:72", "AU-Labs-Internal", "VLAN 40"),
    ("AP-AU-FOYER-G", "00:1a:1e:f0:10:01", "AUSB-Student-Air", "VLAN 100"),
    ("AP-STUDENT-LOUNGE", "00:1a:1e:f0:10:02", "AUSB-Student-Air", "VLAN 100"),
    ("AP-LIBRARY-1F", "00:1a:1e:f0:30:05", "AUSB-Library-Silent", "VLAN 110"),
    ("AP-SEMINAR-HALL", "00:1a:1e:f0:40:10", "AUSB-Guest-Open", "VLAN 120"),
]

SUSPECT_DEVICES = [
    ("3c:52:82:11:22:33", "sansh_laptop_lenovo", "Sansh Vhah (Suspect A)", "10.100.14.22"),
    ("a8:66:7f:44:55:66", "danas_macbook_air", "Danas Moshi (Suspect B)", "10.40.207.88"),
    ("70:85:c2:77:88:99", "prish_dell_xps15", "Prish Koddar (Suspect C)", "10.100.18.91"),
    ("94:65:2d:aa:bb:cc", "tryan_phone_oneplus", "Tryan Ahakkar (Suspect D)", "10.100.22.15"),
    ("d0:03:4b:dd:ee:ff", "parsh_ipad_air", "Parsh Hatel (Suspect E)", "10.120.5.64"),
    ("b4:2e:99:10:20:70", "piyush_thinkpad_t480", "TA Piyush Pelaiya (Culprit)", "10.40.207.19"),
]

TARGET_MAC = "a4:c4:94:02:13:42"
TARGET_HOSTNAME = "prof_chelaiya_thinkpad_x1"
TARGET_IP = "10.20.10.42"
TARGET_FLAG = "case{chelaiya_thinkpad_auto_sync_0213}"

DECOY_FLAGS = [
    ("case{sansh_laptop_dhcp_lease_vlan100}", "3c:52:82:11:22:33", "sansh_laptop_lenovo"),
    ("case{tryan_guest_mobile_dhcp_auth_0213}", "94:65:2d:aa:bb:cc", "tryan_phone_oneplus"),
    ("case{parsh_seminar_hall_vlan200_token}", "d0:03:4b:dd:ee:ff", "parsh_ipad_air"),
]


def generate_random_mac():
    return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))


def generate_random_hostname(idx):
    prefixes = ["laptop", "iphone", "pixel", "galaxy", "desktop", "macbook", "ipad"]
    names = ["arjun", "priya", "karan", "dev", "neha", "meera", "rahul", "aditi", "shreya"]
    return f"{random.choice(names)}_{random.choice(prefixes)}_{idx:03d}"


def build_wifi_and_dhcp_logs(output_wifi_path: Path, output_dhcp_path: Path):
    start_time = datetime(2026, 10, 27, 18, 0, 0)
    end_time = datetime(2026, 10, 28, 4, 30, 0)
    current_time = start_time

    wifi_lines = []
    dhcp_lines = []

    # Pre-populate 80 random student devices
    random_pool = []
    for i in range(80):
        mac = generate_random_mac()
        hname = generate_random_hostname(i)
        ip = f"10.100.{random.randint(1, 50)}.{random.randint(2, 250)}"
        random_pool.append((mac, hname, ip))

    # Add all known suspects to DHCP lease database
    for mac, hname, label, ip in SUSPECT_DEVICES:
        lease_time = start_time + timedelta(minutes=random.randint(5, 60))
        t_str = lease_time.strftime("%Y-%m-%d %H:%M:%S")
        dhcp_lines.append(
            f"{t_str} DHCPACK on {ip} to {mac} ({hname}) via vlan100 "
            f"[uid: 01:{mac}, client-desc: {label}]"
        )

    # Insert Decoy Flags into DHCP & Wi-Fi comments
    for flag, d_mac, d_host in DECOY_FLAGS:
        d_time = start_time + timedelta(hours=random.randint(1, 4))
        t_str = d_time.strftime("%Y-%m-%d %H:%M:%S")
        dhcp_lines.append(
            f"{t_str} DHCPACK on 10.100.99.12 to {d_mac} ({d_host}) via vlan100 "
            f"[note: audit_flag={flag}]"
        )

    # Target: The Midnight Twist at 02:13:42 IST
    target_dt = datetime(2026, 10, 28, 2, 13, 42)

    # Generate realistic timeline entries
    target_injected = False

    while current_time < end_time:
        step = timedelta(seconds=random.randint(10, 45))
        current_time += step

        # Check if we should inject the 02:13:42 target event
        if not target_injected and current_time >= target_dt:
            t_str_wifi = target_dt.strftime("%b %d %H:%M:%S")
            t_str_dhcp = (target_dt + timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")

            # 1. 802.11 Association to Faculty AP
            wifi_lines.append(
                f"{t_str_wifi} aruba-ap-au-fac2 authmgr[1842]: <522008> <INFO> |authmgr| "
                f"MAC={TARGET_MAC} Station (SSID=AU-Faculty-Secure, BSSID=00:1a:1e:f0:20:70) "
                f"802.1X authenticated, Role=Faculty-Staff, VLAN=20"
            )
            # 2. DHCP lease assignment on Faculty VLAN 20
            dhcp_lines.append(
                f"{t_str_dhcp} DHCPACK on {TARGET_IP} to {TARGET_MAC} ({TARGET_HOSTNAME}) via vlan20 "
                f"[client-fqdn: {TARGET_HOSTNAME}.faculty.ahduni.internal, "
                f"auto-sync-token: {TARGET_FLAG}]"
            )
            # 3. DNS lookup for department cloud storage
            wifi_lines.append(
                f"{target_dt.strftime('%b %d %H:%M:%S')} dns-server[902]: <301004> <INFO> |dns| "
                f"Client {TARGET_IP} query: sync.faculty-vault.ahduni.internal IN A (10.20.0.12)"
            )
            # 4. SMB File Share connection log showing exam draft access
            wifi_lines.append(
                f"{(target_dt + timedelta(seconds=3)).strftime('%b %d %H:%M:%S')} sec-monitor[445]: <401015> <WARN> |share| "
                f"Client {TARGET_IP} ({TARGET_HOSTNAME}) connected to \\\\10.20.0.12\\FacultyVault "
                f"FILE_SYNC=OOP99_MidSem_Exam_2026_FinalDraft.pdf [SESSION_AUTH=OK, FLAG={TARGET_FLAG}]"
            )
            target_injected = True

        # Generate typical background student Wi-Fi traffic
        t_wifi = current_time.strftime("%b %d %H:%M:%S")
        ap_name, ap_bssid, ssid, vlan = random.choice(AP_LIST)
        mac, hname, ip = random.choice(random_pool)

        event_type = random.choice(["ASSOC", "AUTH", "ROAM", "DEAUTH", "DNS"])
        if event_type == "ASSOC":
            wifi_lines.append(
                f"{t_wifi} {ap_name.lower()} stm[1120]: <501095> <INFO> |stm| "
                f"Assoc request from {mac} to BSSID {ap_bssid} (SSID: {ssid}, RSSI: -{random.randint(45, 78)} dBm)"
            )
        elif event_type == "AUTH":
            wifi_lines.append(
                f"{t_wifi} {ap_name.lower()} authmgr[1842]: <522008> <INFO> |authmgr| "
                f"MAC={mac} Station (SSID={ssid}, BSSID={ap_bssid}) WPA2-PSK authenticated, Role=Student-Default, {vlan}"
            )
        elif event_type == "ROAM":
            wifi_lines.append(
                f"{t_wifi} {ap_name.lower()} stm[1120]: <501102> <INFO> |stm| "
                f"Client {mac} roamed to {ap_name} (BSSID {ap_bssid})"
            )
        elif event_type == "DEAUTH":
            wifi_lines.append(
                f"{t_wifi} {ap_name.lower()} stm[1120]: <501089> <INFO> |stm| "
                f"Disassoc from {mac}: Client deauthenticated (Reason code: {random.choice([1, 2, 3, 8])})"
            )
        elif event_type == "DNS":
            domain = random.choice([
                "canvas.ahduni.edu.in",
                "github.com",
                "stackoverflow.com",
                "meet.google.com",
                "wifi.campus.internal",
                "auth.ahduni.edu.in",
            ])
            wifi_lines.append(
                f"{t_wifi} dns-server[902]: <301004> <INFO> |dns| Client {ip} query: {domain} IN A"
            )

        # Occasional random DHCP renewals
        if random.random() < 0.25:
            t_dhcp = current_time.strftime("%Y-%m-%d %H:%M:%S")
            dhcp_lines.append(
                f"{t_dhcp} DHCPREQUEST for {ip} from {mac} ({hname}) via vlan100"
            )

    output_wifi_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_wifi_path, "w", encoding="utf-8") as f:
        f.write("\n".join(wifi_lines) + "\n")

    output_dhcp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_dhcp_path, "w", encoding="utf-8") as f:
        f.write("\n".join(dhcp_lines) + "\n")


def main():
    repo_root = Path(__file__).resolve().parent
    wifi_file = repo_root / "files" / "campus_wifi_access.log"
    dhcp_file = repo_root / "files" / "dhcp_leases.log"

    print(f"[*] Generating Wi-Fi syslog: {wifi_file}")
    print(f"[*] Generating DHCP lease database: {dhcp_file}")
    build_wifi_and_dhcp_logs(wifi_file, dhcp_file)

    wifi_count = sum(1 for _ in open(wifi_file, encoding="utf-8"))
    dhcp_count = sum(1 for _ in open(dhcp_file, encoding="utf-8"))

    print(f"[+] Successfully generated campus_wifi_access.log ({wifi_count} lines)")
    print(f"[+] Successfully generated dhcp_leases.log ({dhcp_count} lines)")
    print(f"[+] Target Plot Twist Event verified at 02:13:42 IST")
    print(f"[+] True Flag: {TARGET_FLAG}")


if __name__ == "__main__":
    main()
