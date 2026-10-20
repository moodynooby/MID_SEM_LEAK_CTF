# Case File: The Mid-Sem Leak — CTF Infrastructure
## IEEE AUSB (Ahmedabad University Student Branch)
**Event Date:** 28 October 2026 | **Venues:** Computer Labs 207 & 208, GICT

---

## 🔍 Overview
This repository contains the complete local infrastructure, challenge scaffolding, operational automation, and participant kit for **Case File: The Mid-Sem Leak** — a forensics-driven campus mystery Capture The Flag (CTF) competition for 20 teams (40–80 students).

The entire system is designed to run locally on a lab PC / primary host laptop on the campus LAN without requiring external cloud hosting or internet access for scoreboard operations, backed by a hot-standby secondary laptop.

---

## 🚀 Quick Start (Running CTFd)

### 1. Install Docker & Compose (If not installed)
```bash
sudo ./install_docker.sh
```

### 2. Multiplatform Launch (Linux / macOS / Windows)

You can manage the entire event using the modern **`uv`** CLI runner across all platforms:

```bash
# Start CTFd Stack and detect LAN IP
uv run ctf start

# Check container health and status
uv run ctf status

# Stop containers
uv run ctf stop
```

Alternatively, use the native scripts for your shell:
- **Linux / macOS:** `./start.sh` and `./stop.sh`
- **Windows PowerShell:** `.\start.ps1` and `.\stop.ps1`

---

## 📂 Repository Structure

```
├── docker-compose.yml              # Production CTFd 3.7.0, MariaDB 10.11, Redis 7, Nginx
├── .env.example                    # Environment variable template with security keys
├── .env                            # Active configuration (pre-seeded with secure passwords)
├── install_docker.sh               # 1-command installer for Docker & Compose on Ubuntu
├── start.sh                        # Engine-agnostic startup & LAN IP detection
├── stop.sh                         # Graceful stack shutdown
│
├── conf/
│   ├── nginx/default.conf          # Nginx proxy (Port 80, SSE websocket streaming, 100MB body)
│   └── mysql/my.cnf                # MariaDB tuning (250 connections, UTF-8 MB4, buffer pools)
│
├── challenges/                     # The 5 Story Acts & Timed Challenges
│   ├── README.md                   # Challenge authoring and solve-testing standard
│   ├── template/                   # ctfcli-compatible challenge template
│   ├── 01_act1_incident_report/    # Act I: CCTV Header Corruption (Forensics - Easy)
│   ├── 02_act2_portal_breach/      # Act II: Portal Breach (Log Analysis / Web - Easy/Med)
│   ├── 03_act3_encrypted_chat/     # Act III: Intercepted Ciphertext (Crypto - Medium)
│   ├── 04_act4_malicious_script/   # Act IV: Exfiltration Payload (Reverse Eng. - Med/Hard)
│   ├── 05_act5_final_culprit/      # Act V: Boss Mystery / Unmasking the Culprit (Hard)
│   └── bonus_timed/
│       ├── 01_vanishing_bonus/     # 15-Min Vanishing Challenge (4:35–4:50 PM)
│       └── 02_lightning_round/     # 10-Min Speed Round (5:00–5:10 PM, Double Points)
│
├── ops/                            # Automation & Tech Lead Tooling (Krish, Manas, Vansh)
│   ├── backup.sh                   # Snapshot database dump + uploaded attachments
│   ├── restore.sh                  # One-command restoration for backup laptop
│   ├── sync_to_backup_laptop.sh    # Direct LAN rsync/scp to secondary laptop
│   ├── freeze_scoreboard.py        # 5:15 PM suspense scoreboard blackout
│   ├── unfreeze_scoreboard.py      # 5:30 PM closing ceremony scoreboard reveal
│   ├── manage_timed_events.py      # Interactive console for clue drops and timed rounds
│   └── requirements.txt            # Python dependencies (requests, python-dotenv)
│
└── docs/                           # Documentation, Runbook & Participant Materials
    ├── TECH_LEAD_RUNBOOK.md        # Playbook for setup, dry-run, and event execution
    └── participant_kit/
        ├── CTF_101_CheatSheet.md   # Printable investigator toolkit for student kits
        ├── Rules_and_Guidelines.md # Fair play, dynamic scoring, first blood, tie-breakers
        ├── Case_Briefing_Dossier.md# Fictional story lore, suspect roster, and objectives
        └── Tips_and_Tricks.md      # Teamwork & speed strategy guide
```

---

## ⏱️ Live Event Management (4:30 – 5:30 PM)

Run the interactive event console during the competition:
```bash
python3 ops/manage_timed_events.py
```
This lets the tech lead trigger:
- **4:35 PM:** Release 15-Min Vanishing Challenge.
- **4:45 PM:** Broadcast Clue Drop #1.
- **4:50 PM:** Hide Vanishing Challenge.
- **5:00 PM:** Activate 10-Min Lightning Round (Double Points).
- **5:10 PM:** Close Lightning Round & Broadcast Clue Drop #2.
- **5:15 PM:** Trigger Scoreboard Blackout (Suspense Mode).
- **5:30 PM:** Reveal Scoreboard for the Closing Ceremony.

---

## 🛡️ Backup & Contingency (Standby Laptop)
1. **Periodic Snapshot on Primary:**
   ```bash
   ./ops/backup.sh
   ```
2. **Mirror to Backup Laptop over LAN:**
   ```bash
   ./ops/sync_to_backup_laptop.sh <BACKUP_LAPTOP_IP> manas
   ```
3. **Emergency Recovery on Standby Laptop:**
   ```bash
   ./ops/restore.sh
   ```
   *Total recovery time: < 2 minutes.*
