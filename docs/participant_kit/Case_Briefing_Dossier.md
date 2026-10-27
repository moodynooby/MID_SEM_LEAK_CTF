# 📁 CONFIDENTIAL INVESTIGATION DOSSIER
## Department of Cyber Incident Response — IEEE AUSB Branch
### Case Number: 2026-OCT-28-MIDSEM
**Subject:** The Fictional Mid-Sem Exam Leak Incident  
**Classification:** RESTRICTED — AUTHORIZED INVESTIGATORS ONLY  

---

> **DISCLAIMER:**  
> This case file, all suspect profiles, server hostnames, and exam questions are **100% fictional**. No real campus systems, faculty members, or students are involved. All forensic artifacts were staged strictly inside simulated environments for educational purposes.

---

## 1. Incident Overview
On the evening of 27 October 2026 at approximately 21:14 IST, an automated alert triggered on the faculty internal file server at Ahmedabad University. The upcoming **OOP 99 (Object Oriented Programming Systems)** Mid-Semester Examination Paper, authored by **Prof. Hasmukh Chelaiya**, was illicitly downloaded and circulated.

Forensics triage revealed anomalous network scanning traffic (`nmap`), suspicious mail server activity, and tampering with the Safe Exam Browser (SEB) distribution share. Department records also noted tense disputes regarding grading in **OS 101 (Operating Systems)**.

Campus administration has assembled your team of digital forensic investigators to trace the network breadcrumbs, analyze the evidence dockets, and unmask the culprit before the paper spreads further.

```
       [Prof. Hasmukh Chelaiya's Share]
                   |
       (Nmap Recon & Auth Bypass)
                   |
       [workstation-lab-207.local]
                   |
     (Exfiltrated Mails & OOPS Logs)
                   |
   [Planted Fake Clues / Decoy Red Herrings]
                   |
    [??? WHO IS THE MASTERMIND ???]
```

---

## 2. Roster of Persons of Interest & Suspect Profiles

Cross-reference these profiles with your evidence. Forensic triage suggests several digital footprints may be decoy accounts planted to mislead investigators:

| Suspect Code | Name (Fictional) | Major & Year | Known Alias / Handle | Lab Presence Note |
| :--- | :--- | :--- | :--- | :--- |
| **Suspect A** | **Sansh Vhah** | B.Tech CSE (3rd Yr) | `@binary_breeze` | Checked into Lab 208 at 18:00; left before 20:00. |
| **Suspect B** | **Danas Moshi** | BS Computer Science (2nd Yr) | `@ghost_in_the_lab` | Spotted near Lab 207 terminal between 21:00 and 21:30. |
| **Suspect C** | **Prish Koddar** | B.Tech ICT (4th Yr) | `@root_ninja` | Remote access VPN session active between 19:30 and 20:30. |
| **Suspect D** | **Tryan Ahakkar**| B.Tech Mechanical (2nd Yr) | `@cipher_sid` | Wi-Fi device connected to Student Lounge AP until 22:00. |
| **Suspect E** | **Parsh Hatel** | BS Data Science (3rd Yr) | `@data_drifter` | Attended club meeting in AU Seminar Hall during incident. |

---

## 3. Investigation Forensic Tracks

The evidence is cataloged across four synchronized investigative tracks on the CTFd dashboard:

1. **Digital Forensics & Incident Response (DFIR):**
   - Inspect deleted git branches, reflogs, and unlinked inodes on the TA workstation (`exam_draft_repo.tar.gz`).
   - Sift through the intercepted mail spool (`leaked_incident_mail.eml`) to extract the culprit's motive and authentic confession signature.
   - Reconstruct exfiltrated artifacts and inspect physical memory dumps from the Lab 207 crime scene.
2. **Web Applications & Adversarial AI:**
   - Audit the faculty exam vault web portal cookies and inspect hidden administrative APIs (`http://<LAN_IP>:5001/`).
   - Interact with the campus AI proctor bot (`http://<LAN_IP>:5002/`) to safely bypass guardrails without triggering honeyflag traps.
   - Investigate the faculty submission portal (`http://<LAN_IP>:5003/`) for file upload filter bypasses to trace webshell deployment.
3. **Network Packet Analysis & Wireless Triage:**
   - Dissect the switch packet capture (`infected.pcap`) to uncover webshell command-and-control streams.
   - Correlate campus-wide Aruba AP logs (`campus_wifi_access.log`) and DHCP leases (`dhcp_leases.log`) to uncover the crucial 02:13 AM midnight auto-sync event.
4. **Binary Reverse Engineering & Applied Cryptography:**
   - Reverse engineer the custom sideloaded companion APK (`AU_Companion.apk`) recovered from the Lab 207 crime scene.
   - Crack the encrypted faculty vault archive (`confidential_vault.zip`) by synthesizing a targeted campus wordlist based on dossier entities.

---

## 4. Time-Sensitive Clues & Flash Intel
- Watch for the **15-Minute Vanishing Challenge** at 4:35 PM.
- Be ready for the **10-Minute Lightning Round** at 5:00 PM (Double Points).
- At 5:15 PM, the **Scoreboard Blackout** will begin — trust your investigation and push to the finish line!
