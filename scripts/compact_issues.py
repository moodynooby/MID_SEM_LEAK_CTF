#!/usr/bin/env python3
"""
Compacts GitHub issues on moodynooby/MID_SEM_LEAK_CTF.
Re-opens and updates Track issues #5, #6, #7, #8, updates #25,
and closes micro-issues #9 through #24 with reference comments.
"""

import subprocess
import sys

def run_cmd(args):
    print(f"Running: {' '.join(args[:4])} ...")
    res = subprocess.run(args, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error: {res.stderr}")
    else:
        print(f"Success: {res.stdout.strip()}")
    return res.returncode == 0

# 1. Update Track Issue #5 (Vatsal)
body_5 = """### 🎯 Track Overview
**Lead Developer:** @VP1107 (Vatsal Pandya)  
**Technical Reviewers:** @moodynooby (Manas) & @Krish-452 (Krish)  

Build the network forensics, exfiltration traces, and leaked communications evidence chain for *Case File: The Mid-Sem Leak*.

---

### 📖 Storyline Canon Context
- **Victim:** Prof. Hasmukh Chelaiya (GICT faculty)
- **Culprit:** TA Piyush Pelaiya
- **Motive:** Got low marks in **OS 101** from Prof. Chelaiya $\\rightarrow$ furious/vengeful $\\rightarrow$ targeted and leaked Prof. Chelaiya's upcoming **OOP 99** mid-semester exam paper.
- **Evidence Trail:** Nmap / Kali recon against faculty AP, exfiltrated emails, deleted draft recovery, and webshell traffic.

---

### 📋 Assigned Challenges (5 Challenges)

#### 1. DNS / Wi-Fi Logs: The 2:13 AM Plot Twist (Med Network)
- **Concept:** `campus_wifi_access.log` (800+ lines of student traffic). At 02:13:42 IST, device `prof_chelaiya_thinkpad_x1` connects to faculty AP and auto-syncs the exam paper to cloud storage.
- **Anti-AI Rule:** Require cross-referencing MAC addresses with DHCP lease tables and seating logs. Include decoy student traffic and fake flags.
- **Flag Format:** `case{chelaiya_thinkpad_auto_sync_0213}`
- **Directory:** `challenges/wifi_dns_logs/`

#### 2. Ransomware Infected: Backdoor Web Shell in PCAP (Med Network)
- **Concept:** Network packet capture (`.pcapng`) containing malicious HTTP POST stream interacting with a backdoor webshell.
- **Anti-AI Rule:** Encrypted payload over POST stream; XOR key hidden in user-agent header or handshake packet. Cannot be extracted with basic plaintext string search.
- **Flag Format:** `case{pcap_webshell_exfil_key_found}`
- **Directory:** `challenges/ransomware_pcap/`

#### 3. Deleted but Not Gone: Erased Exam Draft Recovery (Easy Forensics)
- **Concept:** Raw ext4 partition fragment or corrupted git commit where `OOP99_exam_draft_v1.pdf` was deleted with `rm`.
- **Anti-AI Rule:** Inode metadata altered; players must use `ext4magic`, `foremost`, or inspect deleted git tree objects.
- **Flag Format:** `case{git_reflog_rm_cant_hide_draft}`
- **Directory:** `challenges/deleted_exam_recovery/`

#### 4. Flag in Cheatsheet: Participant Kit Easter Egg (Easy Misc)
- **Concept:** Hidden inside the printed/PDF participant cheat sheet using zero-width unicode characters, micro-font footer, or PDF comment metadata.
- **Flag Format:** `case{always_read_the_cheat_sheet_first}`
- **Directory:** `challenges/cheatsheet_flag/`

#### 5. Email Forensics: The Angry TA's Leaked Mails (Med Forensics)
- **Concept:** `.eml` / mbox dump of department emails. TA Piyush furiously complaining about low marks in OS 101 from Prof. Hasmukh Chelaiya, referencing the upcoming OOP 99 paper leak.
- **Anti-AI Rule:** Embedded base64 attachments, forged headers, spoofed sender IPs.
- **Flag Format:** `case{piyush_angry_ta_os101_revenge}`
- **Directory:** `challenges/email_forensics/`

---

### 🛡️ Anti-AI Engineering Directives
- **No vanilla public templates:** Modify all payloads, timestamps, filenames, and headers.
- **Multi-hop synthesis:** Require synthesizing logs across different files.
- **Decoys:** Plant honeypot flags (e.g. `case{decoy_fake_traffic}`) to penalize blind copy-pasters.

### ✅ Acceptance Criteria
- [ ] Each challenge directory created under `challenges/<name>/` with `challenge.yml`, `README.md`, and solution script.
- [ ] Tested end-to-end via `ctf.py`."""

run_cmd(["gh", "issue", "edit", "5",
         "--title", "[Track: Network & Forensics] Network Forensics, Exam Recovery & Angry TA Mails",
         "--body", body_5,
         "--add-assignee", "VP1107"])


# 2. Update Track Issue #6 (Tanish)
body_6 = """### 🎯 Track Overview
**Lead Developer:** @tanishshahh (Tanish Shah)  
**Technical Reviewers:** @moodynooby (Manas) & @Krish-452 (Krish)  

Build the web exploitation and AI prompt jailbreak challenges for *Case File: The Mid-Sem Leak*.

---

### 📖 Storyline Canon Context
- **Victim:** Prof. Hasmukh Chelaiya (GICT faculty)
- **Culprit:** TA Piyush Pelaiya
- **Motive:** Got low marks in **OS 101** from Prof. Chelaiya $\\rightarrow$ furious/vengeful $\\rightarrow$ targeted and leaked Prof. Chelaiya's upcoming **OOP 99** mid-semester exam paper.
- **Evidence Trail:** Web infiltration against faculty upload portal, cookie privilege escalation, and jailbreaking automated exam proctors.

---

### 📋 Assigned Challenges (3 Challenges)

#### 1. Cookie / API: Faculty Exam Vault Inspection (Easy Web)
- **Concept:** Faculty exam portal with cookie/session tampering or hidden API endpoint `/api/v1/faculty/drafts/oop99`.
- **Anti-AI Rule:** Role parameter is signed or obfuscated (e.g., base64 JWT payload requiring `role: faculty_coordinator`), plus honeypot endpoint `/api/v1/admin/secret` that gives decoy flag `case{fake_decoy_bot}`.
- **Flag Format:** `case{cookie_role_tamper_faculty_access}`
- **Directory:** `challenges/cookie_api_vault/`

#### 2. AI Model Prompt: The Proctor Bot Jailbreak (Easy/Med AI)
- **Concept:** Simulated TA proctor chatbot (`proctor_bot.py`) guarding the exam answers with system instructions not to disclose confidential material.
- **Anti-AI Rule:** Layered system prompts that reject simple phrases ("ignore previous instructions"); requires multi-turn roleplay or hypothetical translation framing.
- **Flag Format:** `case{jailbreak_proctor_ta_bypass_prompt}`
- **Directory:** `challenges/ai_proctor_jailbreak/`

#### 3. PHP2SHELL: Faculty Upload Portal Bypass (Hard Web)
- **Concept:** Faculty file upload portal (`upload.php`) rejecting `.php` extensions. Bypassed via extension tricks (`.phtml`, `.php5`), null byte, or double extension, leading to webshell execution.
- **Anti-AI Rule:** Content-Type MIME check + file signature (magic bytes) verification required in addition to extension bypass.
- **Flag Format:** `case{php_webshell_rce_faculty_portal}`
- **Directory:** `challenges/php2shell_upload/`

---

### 🛡️ Anti-AI Engineering Directives
- **No vanilla public templates:** Custom code and realistic GICT faculty branding.
- **Honeypots:** Add decoy endpoints returning trap flags.

### ✅ Acceptance Criteria
- [ ] Each challenge directory created under `challenges/<name>/` with `challenge.yml`, `README.md`, Docker container (if applicable), and solve script.
- [ ] Tested end-to-end via `ctf.py`."""

run_cmd(["gh", "issue", "edit", "6",
         "--title", "[Track: Web & AI] Web Exploitation, AI Prompt Jailbreak & Faculty Portal",
         "--body", body_6,
         "--add-assignee", "tanishshahh"])


# 3. Update Track Issue #7 (Vidit)
body_7 = """### 🎯 Track Overview
**Lead Developer:** @viditd1-eng (Vidit)  
**Technical Reviewers:** @moodynooby (Manas) & @Krish-452 (Krish)  

Build the reverse engineering, binary lockdown, and cryptography challenges for *Case File: The Mid-Sem Leak*.

---

### 📖 Storyline Canon Context
- **Victim:** Prof. Hasmukh Chelaiya (GICT faculty)
- **Culprit:** TA Piyush Pelaiya
- **Motive:** Got low marks in **OS 101** from Prof. Chelaiya $\\rightarrow$ furious/vengeful $\\rightarrow$ targeted and leaked Prof. Chelaiya's upcoming **OOP 99** mid-semester exam paper.
- **Evidence Trail:** Tampered Safe Exam Browser (SEB) distribution binary, suspect's companion Android app, and encrypted faculty archives.

---

### 📋 Assigned Challenges (3 Challenges)

#### 1. APK Reverse Engineer: Suspect's Companion App (Med Mobile/Rev)
- **Concept:** Android APK (`GICT_Companion.apk`) used by students/TAs. Reverse engineer decompiled Java bytecode using JADX or apktool.
- **Anti-AI Rule:** Native `.so` library check or custom string XOR cipher instead of plain plaintext in `strings.xml`.
- **Flag Format:** `case{apk_decompiled_jadx_secret_extracted}`
- **Directory:** `challenges/apk_companion_reversing/`

#### 2. Password Cracking: Faculty Vault & Campus Wordlist (Hard Crypto)
- **Concept:** Password-protected ZIP/7z archive containing the leaked OOP 99 exam draft.
- **Anti-AI Rule:** Standard `rockyou.txt` will NOT work. The password combines campus lore terms (`GICT207_OS101_Piyush2026!`). Teams must generate a custom targeted wordlist based on dossier clues.
- **Flag Format:** `case{custom_hashcat_wordlist_cracked_vault}`
- **Directory:** `challenges/password_cracking/`

#### 3. Safe Exam Browser (SEB): Binary Lockdown Reversing (Hard Rev)
- **Concept:** Tampered SEB binary or Windows PE executable (`SEB_Client_Tampered.exe`). Reverse engineer using Ghidra or x64dbg.
- **Anti-AI Rule:** Anti-debugging checks (`IsDebuggerPresent`) and binary patch requirement (patching conditional jump `jne` to `je` or dumping decrypted memory buffer).
- **Flag Format:** `case{seb_lockdown_integrity_check_patched}`
- **Directory:** `challenges/seb_binary_lockdown/`

---

### 🛡️ Anti-AI Engineering Directives
- **Compiled binaries with custom symbols:** Ensure Ghidra decompilation requires manual analysis.
- **Custom key derivation:** Avoid default dictionary words.

### ✅ Acceptance Criteria
- [ ] Each challenge directory created under `challenges/<name>/` with `challenge.yml`, `README.md`, binaries, and writeup.
- [ ] Tested end-to-end via `ctf.py`."""

run_cmd(["gh", "issue", "edit", "7",
         "--title", "[Track: Binary & Crypto] Reverse Engineering, SEB Lockdown & Custom Cryptography",
         "--body", body_7,
         "--add-assignee", "viditd1-eng"])


# 4. Update Track Issue #8 (Yesha)
body_8 = """### 🎯 Track Overview
**Lead Developer:** Yesha (Reserved — to be assigned upon repo invitation acceptance)  
**Technical Reviewers:** @moodynooby (Manas) & @Krish-452 (Krish)  

Build the digital forensics, steganography, and physical crime scene challenges for *Case File: The Mid-Sem Leak*.

---

### 📖 Storyline Canon Context
- **Victim:** Prof. Hasmukh Chelaiya (GICT faculty)
- **Culprit:** TA Piyush Pelaiya
- **Motive:** Got low marks in **OS 101** from Prof. Chelaiya $\\rightarrow$ furious/vengeful $\\rightarrow$ targeted and leaked Prof. Chelaiya's upcoming **OOP 99** mid-semester exam paper.
- **Evidence Trail:** Physical terminal in Lab 207, ambient microphone recording, redacted exam PDF, and chunked video exfiltration.

---

### 📋 Assigned Challenges (4 Challenges)

#### 1. Liam's Idea: Fragmented Exfiltration (Parts Split) (Easy Forensics)
- **Concept:** Exfiltrated surveillance video split into chunks (`part1.txt`, `part2.txt`, `part3.txt`, `part4.txt`) encoded in Base64.
- **Anti-AI Rule:** Chunks are out of sequence and require reordering via checksum header and stripping padding characters before decoding.
- **Flag Format:** `case{reconstructed_exfil_chunk_assembly}`
- **Directory:** `challenges/fragmented_exfiltration/`

#### 2. PDF Hidden Text: The Redacted Exam Paper (Easy Forensics)
- **Concept:** Leaked PDF of Prof. Hasmukh Chelaiya's OOP 99 exam paper with black redaction bars or white text on white background (`#FFFFFF`).
- **Anti-AI Rule:** Embedded PDF object stream corruption or layered vector paths requiring `pdfminer` / `qpdf` stream extraction rather than basic copy-paste.
- **Flag Format:** `case{redacted_pdf_layer_text_exposed}`
- **Directory:** `challenges/pdf_hidden_text/`

#### 3. Audio Spectrogram: Lab Microphone Wiretap (Med Stego)
- **Concept:** A `.wav` ambient recording of GICT Lab 207 containing hallway chatter and background noise. Visual flag embedded in high-frequency spectrogram (16kHz–20kHz).
- **Anti-AI Rule:** Purely visual stego in the acoustic domain; automated text LLMs cannot solve without spectrogram rendering tools (Audacity / Sonic Visualiser).
- **Flag Format:** `case{spectrogram_lab207_wiretap_audio}`
- **Directory:** `challenges/audio_spectrogram/`

#### 4. Physical Forensics: Lab 207 Evidence Terminal (RAM Dump) (Med Forensics)
- **Concept:** Memory dump (`memdump.raw`) from the physical workstation in Lab 207 where TA Piyush sat.
- **Anti-AI Rule:** Volatility 3 profile analysis requiring finding active bash process, dumped command history, and injected environment variables.
- **Flag Format:** `case{volatility3_lab207_terminal_ram}`
- **Directory:** `challenges/physical_terminal_ram/`

---

### 🛡️ Anti-AI Engineering Directives
- **Multi-modal data:** Audio waveforms and raw memory dumps prevent direct LLM copy-paste.

### ✅ Acceptance Criteria
- [ ] Each challenge directory created under `challenges/<name>/` with `challenge.yml`, `README.md`, artifacts, and writeup.
- [ ] Tested end-to-end via `ctf.py`."""

run_cmd(["gh", "issue", "edit", "8",
         "--title", "[Track: Forensics & Physical] Digital Forensics, Audio Stego & Physical Crime Scene",
         "--body", body_8])


# 5. Update Issue #25 (Live Gamification)
body_25 = """### 🎯 Event Overview
**Lead Developers:** @tanishshahh & @VP1107  
**Technical Reviewers:** @moodynooby (Manas) & @Krish-452 (Krish)  

Build and deploy the live event gamification suite running on the Lab 207/208 big-screen projectors during the competition (4:30–5:30 PM).

---

### 🎮 Event Mechanics & Live Pillars

#### 1. Hot Sauce Roulette 🌶️ (15-Minute Lifeline)
- Every 15 minutes, any team completely stuck on a challenge can elect to have a teammate consume a spoonful of spicy hot sauce.
- In return, Tech Leads hand over an official sealed clue envelope for their chosen challenge track.

#### 2. Big-Screen Projector Spin Wheel 🎡
- Standalone browser web app projected onto the main screen in Lab 207.
- Wheel slices:
  - 🌶️ *Hot Sauce Shot*
  - 💡 *Direct Intel / Clue Drop*
  - ⭐ *+50 Bonus Points*
  - 🚨 *-25 Points Intrusion Penalty*
  - 🧊 *3-Minute Terminal Lockout*
- Sound effects: Tension ticking sound on spin, celebration chime on bonus, loud siren on penalty.

#### 3. Timed Intrusion Punishments & Sudden Lockdowns 🚨
- Integrated with CTFd webhook or manual trigger from Tech Lead console:
  - Brute-force flag penalty: 5+ failed attempts triggers 3-minute submit lockout.
  - Periodic sudden random campus lockdown sirens alerting all teams to an active intrusion.

#### 4. 5:15 PM Scoreboard Blackout 🌑
- Triggered via `uv run ctf blackout`.
- Scoreboard freezes into suspense mode with dramatic 15-minute countdown clock to the 5:30 PM closing ceremony and culprit reveal.

---

### ✅ Acceptance Criteria
- [ ] Standalone HTML5 / Tailwind / JS Spin Wheel app in `ops/gamification/wheel/`.
- [ ] Tested on projector resolution (1920x1080) with audio triggers.
- [ ] Integration with `uv run ctf events` and `ops/manage_timed_events.py`."""

run_cmd(["gh", "issue", "edit", "25",
         "--title", "[Live Ops & Gamification] Interactive Spin Wheel, Hot Sauce Roulette & Timed Events 🎡🌶️",
         "--body", body_25])


# 6. Close redundant micro-issues (#9 to #24) with redirection comments
closures = [
    # Forensics (Yesha) -> Issue #8
    (9, 8, "[Track: Forensics & Physical]"),
    (10, 8, "[Track: Forensics & Physical]"),
    (11, 8, "[Track: Forensics & Physical]"),
    (12, 8, "[Track: Forensics & Physical]"),
    # Web & AI (Tanish) -> Issue #6
    (13, 6, "[Track: Web & AI]"),
    (14, 6, "[Track: Web & AI]"),
    (15, 6, "[Track: Web & AI]"),
    # Intrusion Event -> Issue #25
    (16, 25, "[Live Ops & Gamification]"),
    # Binary & Crypto (Vidit) -> Issue #7
    (17, 7, "[Track: Binary & Crypto]"),
    (18, 7, "[Track: Binary & Crypto]"),
    (19, 7, "[Track: Binary & Crypto]"),
    # Network & Forensics (Vatsal) -> Issue #5
    (20, 5, "[Track: Network & Forensics]"),
    (21, 5, "[Track: Network & Forensics]"),
    (22, 5, "[Track: Network & Forensics]"),
    (23, 5, "[Track: Network & Forensics]"),
    (24, 5, "[Track: Network & Forensics]"),
]

for micro_id, parent_id, parent_name in closures:
    comment = f"Consolidated into master {parent_name} issue #{parent_id}. Closing this individual ticket to keep the tracker compact and organized."
    run_cmd(["gh", "issue", "comment", str(micro_id), "--body", comment])
    run_cmd(["gh", "issue", "close", str(micro_id)])

print("\n--- Compaction Finished Successfully ---")
