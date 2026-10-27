# Case File: The Mid-Sem Leak — CTF Infrastructure
## IEEE AUSB (Ahmedabad University Student Branch)
**Event Date:** 28 October 2026 | **Venues:** Computer Labs 207 & 208, AU

---

## 🔍 Overview
This repository contains the complete local infrastructure, challenge scaffolding, operational automation, and participant kit for **Case File: The Mid-Sem Leak** — a forensics-driven campus mystery Capture The Flag (CTF) competition for 20 teams (40–80 students).

The entire system is designed to run locally on a lab PC / primary host laptop on the campus LAN without requiring external cloud hosting or internet access for scoreboard operations, backed by a hot-standby secondary laptop.

---

## 🐳 Docker Installation Guide

Before running the CTF stack, ensure Docker and Docker Compose are installed:

| Operating System | Recommended Installation | Official Guide / Download Link |
| :--- | :--- | :--- |
| **Windows 10 / 11** | Docker Desktop (with WSL2 backend) | [Download Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/) |
| **macOS (Intel / Apple Silicon)** | Docker Desktop | [Download Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/) |
| **Ubuntu / Debian Linux** | Docker Engine & Compose plugin | [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/) |
| **All Other Platforms** | Official Docker Hub Downloads | [Docker Get Started Guide](https://docs.docker.com/get-started/get-docker/) |

> **Linux Post-Install Tip:** To run Docker commands without `sudo`:
> ```bash
> sudo usermod -aG docker $USER && newgrp docker
> ```

---

## 🚀 Quick Start (Running CTFd)

Manage the entire event across Windows, macOS, and Linux using the unified **`uv`** runner:

```bash
# 1. Start CTFd Stack and detect your LAN IP
uv run ctf start

# 2. Complete setup: seed all challenges, flags, files & themes
uv run ctf setup

# 3. Import teams and participants from Google Form registration CSV
uv run ctf import [registration.csv]

# 4. Check container status & health
uv run ctf status

# 5. Stop containers gracefully
uv run ctf stop
```

When started, CTFd will be accessible at:
- **Local Host:** `http://localhost`
- **Participant LAN URL:** `http://<YOUR_LAN_IP>` (Port 80)

---

## 📂 Repository Structure

```
├── docker-compose.yml              # Production CTFd 3.7.0, MariaDB 10.11, Redis 7, Nginx
├── .env.example                    # Environment variable template with security keys
├── .env                            # Active configuration (pre-seeded with secure passwords)
├── .gitignore                      # Multiplatform ignore (uv, env secrets, backups, OS junk)
├── pyproject.toml / uv.lock        # Modern uv project setup (Python >= 3.10)
├── ctf.py                          # Unified cross-platform CLI runner (Linux / macOS / Windows)
├── AGENTS.md                       # Operational constitution & AI agent guidelines
├── EVENT.md                        # Master event timeline, venue specs & live operations plan
├── HANDOFF.md                      # Engineering handoff, track matrix & disaster recovery
├── NOTES.md                        # Narrative lore, 6 anti-AI defenses & technical deep-dive
│
├── conf/
│   ├── nginx/default.conf          # Nginx proxy (Port 80, SSE websocket streaming, 100MB body)
│   ├── anubis/botPolicy.yaml       # Anubis anti-bot & Proof-of-Work rules (blocks AI scrapers)
│   ├── mysql/my.cnf                # MariaDB tuning (250 connections, UTF-8 MB4, buffer pools)
│   └── gamification.json           # Live gamification rules, wheel segments, weights & decoy trap policies
│
├── tools/
│   └── spin_wheel/                 # Big-screen HTML5/Canvas Projector Spin Wheel (Issue #25)
│
├── ctfd-theme/                     # Big-screen /scoreboard styling (applied via `uv run ctf theme`)
├── themes/                         # Declaratively mounted CTFd themes (m0xblood dark cyberpunk theme)
├── av-console/                     # Projector countdown clock, soundboard & siren alert console
│
├── challenges/                     # Challenge Scaffolding & Active Tracks (Private)
│   ├── README.md                   # Challenge authoring and solve-testing standard
│   └── template/                   # ctfcli-compatible challenge template
│
├── ops/                            # Automation & Tech Lead Tooling (Manas, Krish)
│   ├── import_participants.py      # Google Forms CSV participant & team importer
│   ├── seed_challenges.py          # Offline challenge, dynamic scoring & theme seeder
│   ├── freeze_scoreboard.py        # 5:15 PM suspense scoreboard blackout
│   ├── unfreeze_scoreboard.py      # 5:30 PM closing ceremony scoreboard reveal
│   ├── manage_timed_events.py      # Interactive console for clue drops and timed rounds
│   └── siren_alert/                # Decoy honeyflag trap & intrusion monitor daemon (Issue #16 & #25)
│
└── docs/                           # Documentation, Runbook & Participant Materials
    ├── TECH_LEAD_RUNBOOK.md        # Playbook for setup, dry-run, and event execution
    ├── HOT_SAUCE_ROULETTE.md       # Volunteer station safety guide & hint lifeline protocols
    └── participant_kit/
        ├── CTF_101_CheatSheet.md   # Printable investigator toolkit for student kits
        ├── Rules_and_Guidelines.md # Fair play, dynamic scoring, first blood, tie-breakers
        ├── Case_Briefing_Dossier.md# Fictional story lore, suspect roster, and objectives
        └── Tips_and_Tricks.md      # Teamwork & speed strategy guide
```

---

## ⏱️ Live Event Timeline Management (4:30 – 5:30 PM)

Launch the **Unified Master Live Ops Cockpit** (merging countdown, canvas spin wheel, soundboard, intrusion siren, and all CLI event triggers into one secure dashboard):
```bash
uv run ctf console     # Opens /av-console/ (also aliased as: uv run ctf ui)
```

Or run the interactive CLI event console:
```bash
uv run ctf events
```

Or trigger specific moments directly:
- **4:45 PM:** Broadcast Clue Drop #1:
  ```bash
  uv run ctf events --event clue_drop_1
  ```
- **5:10 PM:** Broadcast Clue Drop #2:
  ```bash
  uv run ctf events --event clue_drop_2
  ```
- **5:15 PM:** Trigger Scoreboard Blackout (Suspense Mode):
  ```bash
  uv run ctf blackout
  ```
- **5:30 PM:** Reveal Scoreboard for the Closing Ceremony:
  ```bash
  uv run ctf reveal
  ```

---

## 🎡 Big-Screen Projector Gamification & AV Suite

- **Interactive Projector Spin Wheel (Issue #25):**
  ```bash
  uv run ctf wheel
  ```
  Accessible on LAN at `http://<LAN_IP>/spin-wheel/` or standalone at `tools/spin_wheel/index.html`. Controls: `Space` = Spin, `R` = Reset, `M` = Mute, `F` = Fullscreen.

- **Intrusion Punishments & Decoy Honeyflag Monitor (Issue #16 & #25):**
  ```bash
  # Run live monitor daemon watching CTFd submissions
  uv run ctf siren

  # Or test projector siren strobe simulation
  uv run ctf siren --test "Station 4 - HashCrashers"
  ```
  Projector alert screen: `http://<LAN_IP>/av-console/siren.html`. All rules, decoy lists, and lockout durations are configurable in [`conf/gamification.json`](conf/gamification.json).

- **Hot Sauce Roulette & Lifelines Guide:**
  See full protocols and volunteer checklists in [`docs/HOT_SAUCE_ROULETTE.md`](docs/HOT_SAUCE_ROULETTE.md).

---

## 🛡️ Backup & Contingency (Standby Laptop)

1. **Create Snapshot on Primary Server:**
   ```bash
   uv run ctf backup
   ```
2. **Push Snapshot to Standby Laptop over LAN:**
   ```bash
   uv run ctf sync <BACKUP_LAPTOP_IP> [ssh_user]
   ```
3. **Emergency Restore on Standby Laptop:**
   ```bash
   uv run ctf restore
   ```
   *Total recovery time: < 2 minutes.*
