# Case File: The Mid-Sem Leak — CTF Infrastructure
## IEEE AUSB (Ahmedabad University Student Branch)
**Event Date:** 28 October 2026 | **Venues:** Computer Labs 207 & 208, GICT

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

# 2. Check container status & health
uv run ctf status

# 3. Stop containers gracefully
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
│   └── mysql/my.cnf                # MariaDB tuning (250 connections, UTF-8 MB4, buffer pools)
│
├── ctfd-theme/                     # Big-screen /scoreboard styling (applied via `uv run ctf theme`)
├── themes/                         # Declaratively mounted CTFd themes (m0xblood dark cyberpunk theme)
├── av-console/                     # Projector countdown clock & Tech Lead sound cue board
│
├── challenges/                     # Challenge Scaffolding & Active Tracks (Private)
│   ├── README.md                   # Challenge authoring and solve-testing standard
│   └── template/                   # ctfcli-compatible challenge template
│
├── ops/                            # Automation & Tech Lead Tooling (Manas, Krish)
│   ├── freeze_scoreboard.py        # 5:15 PM suspense scoreboard blackout
│   ├── unfreeze_scoreboard.py      # 5:30 PM closing ceremony scoreboard reveal
│   ├── manage_timed_events.py      # Interactive console for clue drops and timed rounds
│   └── requirements.txt            # Python dependencies (requests, python-dotenv, rich)
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

## ⏱️ Live Event Timeline Management (4:30 – 5:30 PM)

Run the live interactive event console during the competition:
```bash
uv run ctf events
```

Or trigger specific moments directly:
- **4:35 PM:** Release 15-Min Vanishing Challenge:
  ```bash
  uv run ctf events --event vanishing_start
  ```
- **4:45 PM:** Broadcast Clue Drop #1:
  ```bash
  uv run ctf events --event clue_drop_1
  ```
- **4:50 PM:** Hide Vanishing Challenge:
  ```bash
  uv run ctf events --event vanishing_end
  ```
- **5:00 PM:** Activate 10-Min Lightning Round (Double Points):
  ```bash
  uv run ctf events --event lightning_start
  ```
- **5:10 PM:** Close Lightning Round & Broadcast Clue Drop #2:
  ```bash
  uv run ctf events --event lightning_end
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
