# Challenge Authoring & Verification Standard
## Case File: The Mid-Sem Leak — IEEE AUSB

Welcome challenge authors and testers! Every challenge in this CTF is an evidence piece in the overarching campus investigation.

---

### 1. Active Challenge Tracks (14 Challenges)

| Track | Challenge Name | Category | Difficulty | Target Description |
| :--- | :--- | :--- | :--- | :--- |
| **Forensics** | Liam's Idea: Fragmented Exfiltration | Forensics | Easy (100-200) | Exfiltrated video split into Base64 parts (`part*.txt`). |
| **Forensics** | PDF Hidden Text: Redacted Exam | Forensics | Easy (100-200) | Leaked OOP 99 paper with white text / hidden stream. |
| **Forensics** | Audio Spectrogram: Lab Wiretap | Stego | Medium (300-400) | Ambient audio with visual flag synthesized into frequencies. |
| **Forensics** | Physical Forensics: Lab 207 Terminal | Forensics | Medium (300-400) | Physical crime scene PC memory dump in Lab 207. |
| **Web & AI** | Cookie / API: Faculty Exam Vault | Web | Easy (100-200) | Client-side cookie tampering / hidden REST endpoint. |
| **Web & AI** | AI Model Prompt: Proctor Bot Jailbreak | AI | Easy/Med (200-300) | Adversarial prompt injection against TA proctor bot. |
| **Web & AI** | PHP2SHELL: Insecure Faculty Upload | Web | Hard (500) | File upload filter bypass to web shell execution. |
| **Reversing** | APK Reverse Engineer: Companion App | Mobile / Rev | Medium (300-400) | Decompiling campus Android app in JADX. |
| **Crypto** | Password Cracking: Faculty Vault | Crypto | Hard (500) | Cracking encrypted archive using custom campus wordlist. |
| **Reversing** | Safe Exam Browser (SEB) Reversing | Reverse Eng | Hard (500) | Reversing stripped C/C++ lockdown binary in Ghidra. |
| **Network** | DNS / Wi-Fi Logs: 2:13 AM Auto-Sync | Network | Medium (300-400) | Aruba Wi-Fi log revealing professor midnight cloud sync. |
| **Network** | Ransomware Infected: Backdoor PCAP | Network | Medium (300-400) | Isolate malicious HTTP POST traffic & extract webshell key. |
| **Forensics** | Deleted but Not Gone: Erased Draft | Forensics | Easy (100-200) | Inode / commit recovery of erased exam paper draft. |
| **Forensics** | [Email Forensics: Angry TA's Mails](email_forensics/) | Forensics | Medium (300-400) | Mail spool of TA Piyush's angry emails to Prof. Chelaiya. |

---

### 2. Flag Format Guidelines
- **Format:** `case{...}` (all lowercase prefix, ASCII characters, underscores or leetspeak).
- **Examples:**
  - `case{cctv_t1mestamp_c0rrupted_f0und}`
  - `case{sql1_p0rtal_adm1n_byp4ss}`
  - `case{vigenere_k3y_w4s_midsem2026}`
  - `case{culprit_is_fictional_suspect_alex_chen}`
- **Notice:** Flags **must never** reference real university staff, actual faculty members, or real systems.

---

### 3. Dynamic Scoring Formula
In CTFd, configure challenges as **Dynamic**:
- **Initial Points:** 500
- **Decay Solves:** 15 (points drop smoothly as more teams solve)
- **Minimum Points:** 100
- **First Blood:** The first team to solve earns an automated announcement on the live scoreboard.

---

### 4. Mandatory Verification Checklist (Before 25/10/2026)
As per the event proposal, **every challenge must be solve-tested by someone other than its author**:
1. [ ] Author submits `challenge.yml`, `README.md` (with step-by-step solution), and all files.
2. [ ] Independent tester solves the challenge without looking at the solution `README.md`.
3. [ ] Time required to solve is recorded (ensure it fits the 1-hour active window).
4. [ ] Prepared hint is written with a small point cost (e.g. -25 to -50 pts).
5. [ ] Flag is tested for copy-paste whitespace sensitivity.
