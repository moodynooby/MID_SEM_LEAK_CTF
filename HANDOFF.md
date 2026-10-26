# HANDOFF.md — Engineering & Operations Handoff Document
> **Case File: The Mid-Sem Leak** | IEEE AUSB CTF (28 Oct 2026, GICT Labs 207 & 208)  
> **Tech Leads:** Manas Doshi (@moodynooby) & Krish (@Krish-452) | **Core Organizer:** Vansh Shah  
> **Active Contributors:** Vidit (@viditd1-eng), Tanish (@tanishshahh), Vatsal (@VP1107), Yesha  

---

## 1. Executive Summary & Current State of the Codebase
This repository contains the complete offline-first containerized infrastructure, challenge scaffolding, live operational automation, and participant kit for **Case File: The Mid-Sem Leak**.

### Key Facts & Deployment Specs:
- **Event Date:** Wednesday, 28 October 2026 (Active Window: 4:30 PM – 5:30 PM IST).
- **Target Audience:** 20 teams (40–80 undergraduate students).
- **Core Engine:** Pinned CTFd 3.7.0 with MariaDB 10.11, Redis 7-Alpine, and custom tuned Nginx proxy on Port 80.
- **Unified Tooling:** Single cross-platform CLI runner powered by `uv`: `uv run ctf <command>`.
- **Zero Cloud LAN:** Engineered to operate completely disconnected from external internet on GICT Lab switches.
- **Failover Target:** Standby laptop synchronization mechanism with `< 2-minute` Recovery Time Objective (RTO).

---

## 2. Infrastructure & Architectural Blueprint

```
                     [ Campus LAN Switch (Port 80) ]
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │             Nginx Reverse Proxy (conf/nginx/)          │
       │    - Port 80 binding (HTTP)                            │
       │    - SSE / Websocket proxy buffering disabled          │
       │    - 100 MB client max body size (evidence uploads)    │
       └────────────────────────────┬───────────────────────────┘
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
       ┌────────────────────────┐          ┌───────────────────────┐
       │   CTFd Application     │          │  MariaDB 10.11 Engine │
       │   - Version 3.7.0      │          │  - 250 Max Conns      │
       │   - Dynamic Scoring    │◄────────►│  - UTF8MB4 Collation  │
       │   - Session Engine     │          │  - InnoDB Buffer Pool │
       └──────────┬─────────────┘          └───────────────────────┘
                  │
                  ▼
       ┌────────────────────────┐
       │  Redis 7 Cache Layer   │
       │  - Ephemeral Sessions  │
       │  - Dynamic Rate Limits │
       └────────────────────────┘
```

### Critical Volume & Persistence Quirks
1. **Database & Uploads Storage:**
   - MariaDB tables (`ctfd_db`) and file assets (`ctfd_data` at `/var/uploads`) reside in named Docker volumes.
   - `uv run ctf stop` preserves all volumes safely.
   - **WARNING:** Running `docker compose down -v` or `docker volume prune` **will permanently destroy all team accounts, theme configs, and custom markdown pages**. Always run `uv run ctf backup` before touching volume states.
2. **Theme Mounts:**
   - Custom Jinja2 themes and stylesheets are mounted declaratively via [docker-compose.yml](docker-compose.yml) (`./themes/m0xblood:/opt/CTFd/CTFd/themes/m0xblood:ro`).
   - Running `uv run ctf theme` automatically activates `m0xblood` as the primary CTFd theme via the REST API and injects big-screen scoreboard styling into `theme_header`/`theme_footer`. Never manually alter files inside the running container.

---

## 3. Challenge Track Matrix & Status (14 Challenges + Live Ops)

| Issue # | Challenge Name | Category | Difficulty | Assignee | Target Directory | Status |
| :---: | :--- | :--- | :---: | :--- | :--- | :---: |
| **#9** | Liam's Idea: Fragmented Exfiltration | Forensics | Easy | Yesha | `challenges/liams_idea/` | Scaffolding |
| **#10** | PDF Hidden Text: The Redacted Exam Paper | Forensics | Easy | Yesha | `challenges/pdf_hidden_text/` | Scaffolding |
| **#11** | Audio Spectrogram: Lab Microphone Wiretap | Stego | Medium | Yesha | `challenges/audio_spectrogram/` | Scaffolding |
| **#12** | Physical Forensics: Lab 207 Terminal | Forensics | Medium | Yesha | `challenges/physical_terminal/` | Scaffolding |
| **#13** | Cookie / API: Faculty Exam Vault | Web | Easy | @tanishshahh | `challenges/cookie_api/` | Completed (Verified) |
| **#14** | AI Model Prompt: Proctor Bot Jailbreak | AI | Easy/Med | @tanishshahh | `challenges/ai_prompt_injection/` | Completed (Verified) |
| **#15** | PHP2SHELL: Faculty Upload Bypass | Web | Hard | @tanishshahh | `challenges/php2shell/` | Completed (Verified) |
| **#16** | Intrusion Punishments & Siren Alerts | Live Ops | — | @tanishshahh | `ops/siren_alert/` | Scaffolding |
| **#17** | APK Reverse Engineer: Suspect's App | Reversing | Medium | @viditd1-eng | `challenges/apk_reversing/` | Scaffolding |
| **#18** | Password Cracking: Faculty Vault | Crypto | Hard | @viditd1-eng | `challenges/password_cracking/` | Scaffolding |
| **#19** | Safe Exam Browser (SEB) Reversing | Reversing | Hard | @viditd1-eng | `challenges/seb_binary/` | Scaffolding |
| **#20** | DNS / Wi-Fi Logs: 2:13 AM Auto-Sync | Network | Medium | @VP1107 | `challenges/wifi_dns_logs/` | Completed (Verified) |
| **#21** | Ransomware Infected: Web Shell PCAP | Network | Medium | @VP1107 | `challenges/ransomware_pcap/` | Completed (Verified) |
| **#22** | Deleted but Not Gone: Erased Exam Draft | Forensics | Easy | @VP1107 | `challenges/deleted_evidence/` | Completed (Verified) |
| **#23** | Flag in Cheatsheet: Participant Kit Egg | Forensics | Easy | @VP1107 | `challenges/cheatsheet_egg/` | Completed (Verified) |
| **#24** | Email Forensics: Angry TA's Leaked Mails| Forensics | Medium | @VP1107 | `challenges/email_forensics/` | Completed (Verified) |
| **#25** | Projector Spin Wheel & Hot Sauce App | Live Ops | — | @VP1107, @tanishshahh | `tools/spin_wheel/` | In Flight |
| **#1** | CTFd Theme: Cyber-Forensic Dark Mode | UI/UX | — | @viditd1-eng | `themes/midsem_leak/` | In Flight |
| **#2** | Big-Screen Projector & Sound Cue Board | AV/Ops | — | @tanishshahh | `ops/soundboard/` | In Flight |
| **#4** | Case Dossier Print Kit & Slide Deck | Design | — | Open | `docs/participant_kit/` | In Flight |

---

## 4. Canon Storyline & Lore Blueprint

### The Core Incident
- **The Victim:** **Prof. Hasmukh Chelaiya** (Faculty teaching **OS 101** and author of the leaked **OOP 99** Mid-Sem Exam).
- **The Culprit:** **TA Piyush Pelaiya** (Graduate teaching assistant who received failing/unfair grades from Prof. Chelaiya in OS 101, prompting a revenge-driven exfiltration of the OOP 99 exam paper).
- **The Decoys & Framed Students:**
  - *Rohan Sharma* (`@binary_breeze`): Lab 208 check-in decoy.
  - *Vikram Patel* (`@ghost_in_the_lab`): Terminal footprint decoy.
  - *Ananya Iyer* (`@root_ninja`): Active VPN session decoy.
  - *Siddharth Mehta* (`@cipher_sid`): Student Lounge Wi-Fi decoy.
  - *Pooja Nair* (`@data_drifter`): Seminar Hall club meeting decoy.
- **The Master Plot Twist (Challenge #20):**
  - Wi-Fi logs indicate that at **02:13:42 IST**, device `prof_deshmukh_thinkpad_x1` synced the mid-sem draft to a shared directory, which TA Piyush hijacked via an unprotected session!

---

## 5. Operations & Unified CLI Cheat Sheet (`uv run ctf`)

All tasks must be invoked via `ctf.py`:

```bash
# === LIFECYCLE COMMANDS ===
uv run ctf start          # Spin up Nginx, CTFd, MariaDB, Redis; prints LAN IP
uv run ctf status         # Verify health status of all 4 containers
uv run ctf stop           # Clean shutdown preserving Docker volumes

# === BACKUP, DISASTER RECOVERY & STANDBY SYNC ===
uv run ctf backup         # Dump DB + uploads into backups/ctfd_backup_<timestamp>.tar.gz
uv run ctf sync <IP>      # Push backup archive to secondary laptop over LAN (SCP/SSH)
uv run ctf restore        # Restore DB and uploads from latest backup archive

# === LIVE EVENT MILESTONES (28 OCT) ===
uv run ctf events                    # Open interactive CLI control panel
uv run ctf events --event vanishing_start   # 4:35 PM: Release 15-min bonus challenge
uv run ctf events --event clue_drop_1       # 4:45 PM: Broadcast Intel Clue #1
uv run ctf events --event vanishing_end     # 4:50 PM: Hide vanishing challenge
uv run ctf events --event lightning_start   # 5:00 PM: Unlock 10-min Lightning Round (2x pts)
uv run ctf events --event lightning_end     # 5:10 PM: Lock Lightning Round
uv run ctf events --event clue_drop_2       # 5:10 PM: Broadcast Intel Clue #2
uv run ctf blackout                         # 5:15 PM: Freeze scoreboard into suspense mode
uv run ctf reveal                           # 5:30 PM: Unfreeze scoreboard for ceremony
```

---

## 6. Hot-Standby Failover Protocol (Recovery in `< 2 Minutes`)

In the event of total hardware, power, or kernel failure on the Primary Server:

```mermaid
flowchart TD
    A[Primary Server Host Fails] -->|Step 1| B[Disconnect Primary LAN Cable]
    B -->|Step 2| C[Assign Primary Static LAN IP to Standby Laptop]
    C -->|Step 3| D[Run 'uv run ctf restore' on Standby Laptop]
    D -->|Step 4| E[Verify CTFd Containers 'uv run ctf status']
    E -->|Step 5| F[Switch HDMI Projector Cable to Standby Laptop]
    F -->|Result| G[Live Event Resumed with Zero Data Loss]
```

---

## 7. Immediate Priority Punchlist (Before 27 Oct Dry Run)

1. **Challenge Scaffolding Completion:**
   - Ensure every challenge directory contains `challenge.yml`, `README.md` (solution), `generate.py` / `Dockerfile`, and `solve.py`.
2. **Anti-AI Quality Assurance:**
   - Execute the 5-step verification protocol for all 14 challenges.
   - Run prompt-injection solver against Issue #14 (`proctor_bot.py`) to confirm honeyflag triggering.
   - Check audio spectrogram visualization in Audacity/Sonic Visualiser for Issue #11.
3. **Live Gamification Staging:**
   - Stand up the HTML5 canvas Spin Wheel in `tools/spin_wheel/` (Issue #25).
   - Test audio soundboard cues on Lab 207 & 208 speakers (Issue #2).
4. **Print Asset Verification:**
   - Export printable PDF for `Case_Briefing_Dossier.md` and team scratchcards (Issue #4).
5. **Dry Run in Lab 207/208 (27 Oct 2026):**
   - Test LAN switch port forwarding, IP allocation, projector HDMI resolution, and failover restore.

---

## 8. Governance & Contribution Rules
- **Mandatory Context Reading & Updates:** Every contributor and agent MUST read all operational context docs ([AGENTS.md](AGENTS.md), [EVENT.md](EVENT.md), [HANDOFF.md](HANDOFF.md), [NOTES.md](NOTES.md), [README.md](README.md), [challenges/README.md](challenges/README.md), and [docs/TECH_LEAD_RUNBOOK.md](docs/TECH_LEAD_RUNBOOK.md)) before taking action, and synchronously update all corresponding context docs whenever modifications are made.
- Always refer to [AGENTS.md](AGENTS.md) for strict rules regarding AI contributions (`Assisted-by` attribution), secret hygiene, dynamic scoring formulas, and DCO restrictions (no `Signed-off-by`).
- Keep `.env.example` strictly synchronized with `.env`.
- Link all PRs and commits to relevant issue IDs (`Fixes: #<id>`).
