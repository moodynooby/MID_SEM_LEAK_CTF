# DNS / Wi-Fi Logs: The 2:13 AM Auto-Sync
## Challenge Writeup & Author Rationale

- **Author:** Vatsal Pandya (`@VP1107`)
- **Track:** Network & Forensics (Issue #5 / Challenge #1)
- **Category:** Network
- **Estimated Difficulty:** Medium — 500 → 200 pts (decay 16 solves)  
- **Tester / Solve-Verified By:** Krish Poddar (`@Krish-452`) / Manas Doshi (`@moodynooby`)
- **True Flag:** `case{chelaiya_thinkpad_auto_sync_0213}`
- **Decoy Honeyflags:**
  - `case{decoy_student_mac_address}`
  - `case{sansh_vhah_library_ap_decoy}`
  - `case{nice_try_blind_ai_wifi_grep}`

---

## 1. Challenge Concept & Lore

In *Case File: The Mid-Sem Leak*, campus authorities initially suspected a direct physical breach into AU Lab 207 or an external intrusion. 

However, wireless network forensics provides the **master plot twist** of the investigation:
At **02:13:42 IST** on 28 October 2026, Prof. ManMishra Chelaiya’s departmental laptop (`prof_chelaiya_thinkpad_x1`, MAC `a4:c4:94:02:13:42`) connected to the dedicated faculty access point (`AP-AU-FACULTY-L2`) and executed an automated synchronization task with the department file server (`\\10.20.0.12\FacultyVault`). During this sync, the final draft of `OOP99_MidSem_Exam_2026_FinalDraft.pdf` was staged on an internal department share with permissive read permissions. 

TA Piyush Pelaiya, who had persistent network monitoring in Lab 207, hijacked this unencrypted synchronization stream to grab the exam paper that he later leaked via email.

---

## 2. Anti-AI Defensive Architecture

1. **High Volume Realistic Log Stream (1,700+ lines across files):**
   Syslog contains realistic 802.11 association, WPA2/802.1X authentication, 802.11 roaming, and deauthentication events alongside ISC-DHCP lease histories. Feeding the raw log dump into standard AI context windows results in truncation or hallucinated MAC matches.

2. **Cross-Referencing & Temporal Correlation:**
   Solving requires a two-step forensic correlation:
   - Identify the timestamp `02:13:42` on the Faculty AP BSSID (`00:1a:1e:f0:20:70`).
   - Cross-reference the identified MAC address (`a4:c4:94:02:13:42`) against the separate DHCP lease table `dhcp_leases.log`.

3. **Multiple Decoy Student Traces & Honeyflags:**
   The logs contain traces of all 5 fictional student suspects from the case dossier (Sansh, Danas, Prish, Tryan, Parsh) plus decoy honeyflags:
   - `case{sansh_laptop_dhcp_lease_vlan100}`
   - `case{tryan_guest_mobile_dhcp_auth_0213}`
   - `case{parsh_seminar_hall_vlan200_token}`
   A blind `grep -i "case{"` or AI regex scrape will trap these decoy tokens.

---

## 3. Walkthrough & Official Solution

### Step 1: Filter Traffic on the Faculty AP
Examine `campus_wifi_access.log` for connections on the faculty network between 02:00 AM and 02:30 AM:

```bash
grep "02:13" files/campus_wifi_access.log | grep -i "faculty"
```

Output:
```text
Oct 28 02:13:42 aruba-ap-au-fac2 authmgr[1842]: <522008> <INFO> |authmgr| MAC=a4:c4:94:02:13:42 Station (SSID=AU-Faculty-Secure, BSSID=00:1a:1e:f0:20:70) 802.1X authenticated, Role=Faculty-Staff, VLAN=20
```

### Step 2: Cross-Reference MAC against DHCP Leases
Search `files/dhcp_leases.log` for the client MAC `a4:c4:94:02:13:42`:

```bash
grep -i "a4:c4:94:02:13:42" files/dhcp_leases.log
```

Output:
```text
2026-10-28 02:13:43 DHCPACK on 10.20.10.42 to a4:c4:94:02:13:42 (prof_chelaiya_thinkpad_x1) via vlan20 [client-fqdn: prof_chelaiya_thinkpad_x1.faculty.ahduni.internal, auto-sync-token: case{chelaiya_thinkpad_auto_sync_0213}]
```

### Step 3: Verify the File Synchronization Traffic
Inspect the network audit stream for the assigned IP `10.20.10.42`:

```bash
grep "10.20.10.42" files/campus_wifi_access.log
```

Output:
```text
Oct 28 02:13:42 dns-server[902]: <301004> <INFO> |dns| Client 10.20.10.42 query: sync.faculty-vault.ahduni.internal IN A (10.20.0.12)
Oct 28 02:13:45 sec-monitor[445]: <401015> <WARN> |share| Client 10.20.10.42 (prof_chelaiya_thinkpad_x1) connected to \\10.20.0.12\FacultyVault FILE_SYNC=OOP99_MidSem_Exam_2026_FinalDraft.pdf [SESSION_AUTH=OK, FLAG=case{chelaiya_thinkpad_auto_sync_0213}]
```

The flag is:
`case{chelaiya_thinkpad_auto_sync_0213}`

---

## 4. Hints & Cost Strategy

- **Hint 1 (-25 pts):** "Focus on the traffic spikes between 02:00 and 02:30 AM on the Faculty AP (BSSID 00:1a:1e:f0:20:70)."
- **Hint 2 (-50 pts):** "Correlate the client MAC address connecting at 02:13:42 with the DHCP lease table to resolve the hostname and session sync token."

---

## 5. Solve-Test Verification Log

- **Date Tested:** 26/10/2026
- **Automated Verification:** `uv run python challenges/wifi_dns_logs/solve.py` $\rightarrow$ Exit code 0.
- **Estimated Human Solve Time:** 7–12 minutes.
- **Verification Summary:**
  - Syslog parsing cleanly isolates 02:13:42 spike from 1,400+ noisy log lines.
  - MAC resolution across DHCP records reliably identifies Prof. Chelaiya's ThinkPad.
  - Decoy honeyflags verified and isolated.
