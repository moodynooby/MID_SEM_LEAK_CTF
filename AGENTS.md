# AGENTS.md — Agent Governance & Operational Constitution
> **Case File: The Mid-Sem Leak** | IEEE AUSB CTF (28 Oct 2026, GICT Labs 207 & 208)  
> **Tech Leads:** Manas (@moodynooby) & Krish (@Krish-452) | **Core Organizer:** Vansh Shah  
> **Track Contributors:** Vidit (@viditd1-eng), Tanish (@tanishshahh), Vatsal (@VP1107), Yesha  

---

## 1. Operational Constraints & Hidden Quirks
- **Zero Cloud & Port 80 LAN:** Standalone local deployment on campus LAN port 80. The CTFd scoreboard, challenge endpoints, and participant access must **never** rely on external internet access or third-party cloud services.
- **Hot-Standby Target:** A secondary laptop is kept in continuous synchronization via `uv run ctf sync <IP>` for an emergency failover target of `< 2 minutes`.
- **CTFd UI Persistence Gotcha:**
  - Admin UI edits (theme configuration, custom CSS, markdown pages) write directly to MariaDB (`config`, `pages` tables) and `/var/uploads` (`ctfd_data` Docker volume).
  - Normal restarts (`uv run ctf stop && uv run ctf start`) preserve named volumes.
  - Running `docker compose down -v` **wipes all UI changes and database state**. Always run `uv run ctf backup` before touching volumes.
  - Custom Jinja2 themes and static assets must be declaratively mounted via [docker-compose.yml](docker-compose.yml), never manually edited inside a running container.
- **Cross-Platform Compatibility:** The codebase runs on Linux, macOS, and Windows (Docker Desktop WSL2). All file links and scripts must use relative repository paths and cross-platform path handling (avoid hardcoded absolute paths like `/home/...` or `C:\...`).

---

## 2. Core Engineering Pillars
1. **Declarative Configuration:** Config files ([docker-compose.yml](docker-compose.yml), [conf/](conf/), `challenges/**/challenge.yml`, [pyproject.toml](pyproject.toml), [.env.example](.env.example)) are the single source of truth. No manual GUI-only or uncommitted container hacks.
2. **Reproducibility:** A fresh clone on any computer must spin up identically via `uv run ctf start`. Pinned container tags only (`ctfd:3.7.0`, `mariadb:10.11`, `redis:7-alpine`, `nginx:alpine`).
3. **Immutability & Atomic Updates:** Updates progress in generational steps. Recreate containers cleanly via Compose; never live-patch the database without an automated snapshot generation.
4. **Risk-Free Rollbacks:** Pre-mutation snapshot via `uv run ctf backup` bundles `database.sql` and `/var/uploads` into `backups/ctfd_backup_<timestamp>.tar.gz`. The standby laptop restores instantly with `uv run ctf restore`.
5. **Zero Configuration & Documentation Drift:** Any deleted feature, modified challenge, adjusted timeline, or updated operational script must be immediately and synchronously updated across all context documents ([EVENT.md](EVENT.md), [HANDOFF.md](HANDOFF.md), [NOTES.md](NOTES.md), [README.md](README.md), [challenges/README.md](challenges/README.md)). Keep [.env.example](.env.example) in strict lockstep with `.env`.
6. **Infrastructure as Code (IaC):** Proxy routing, database engine tuning, challenge metadata, event automations, and live timeline schedules are version-controlled code.

---

## 3. Autonomous Actions (Three-Tier Rule)

### Always do:
- **Mandatory Context Ingestion (Read All Context Docs First):**
  Before proposing plans, executing code, creating challenges, or modifying configurations, agents MUST read and internalize the complete operational context:
  1. [AGENTS.md](AGENTS.md) — Operational constitution, governance, and autonomous rules.
  2. [EVENT.md](EVENT.md) — Master event timeline, venue specs, gamification rules, and schedules.
  3. [HANDOFF.md](HANDOFF.md) — Engineering handoff, live container status, track matrix, and failover runbook.
  4. [NOTES.md](NOTES.md) — Narrative canon lore, 6 anti-AI defenses, and technical infrastructure deep dive.
  5. [README.md](README.md) — Repository structure, quickstart, and environment setup.
  6. [challenges/README.md](challenges/README.md) — 5-step challenge authoring and verification standard.
  7. [docs/TECH_LEAD_RUNBOOK.md](docs/TECH_LEAD_RUNBOOK.md) — Live ops minute-by-minute playbook.
- **Synchronously Update Context Docs on Any Modification:**
  Whenever modifying the codebase—adding or editing challenges, tweaking infrastructure configs, updating canon storylines, adjusting event dynamics, or creating CLI commands—agents MUST immediately update all affected context documents ([EVENT.md](EVENT.md), [HANDOFF.md](HANDOFF.md), [NOTES.md](NOTES.md), [README.md](README.md)) within the same commit or pull request. No orphan or lagging documentation is permitted.
- Run all administrative and lifecycle operations via the unified CLI: `uv run ctf <command>` ([ctf.py](ctf.py)).
- Run `uv run ctf backup` before modifying database schemas, mass-importing challenges, or updating container versions.
- Verify any non-trivial bug by creating an isolated reproducer before attempting fixes.
- Attribute AI contributions in git commit messages: `Assisted-by: LLM [TOOL1] [TOOL2]`.
- Add `Fixes: #<issue_id>` or `Fixes: <commit_id>` tag when resolving defects or closing deliverables.
- Explicitly report operational limitations if a fix could not be built, executed, or tested against live local containers.
- Format challenge flags strictly as `case{...}` (all lowercase prefix, ASCII characters, underscores or leetspeak).
- Follow the canon storyline: TA Piyush Pelaiya leaked Prof. Hasmukh Chelaiya's OOP 99 mid-sem exam paper in revenge for harsh grading in OS 101.

### Ask first:
- Before running destructive operations (`down -v`, volume pruning, database table truncations).
- Before modifying live production environment variables in `.env`.
- Before altering challenge dynamic scoring formulas (Default: 500 initial, 15 decay, 100 min).
- Before disclosing security flaws: classify as bug vs. vulnerability and present to Tech Leads privately.

### Never do:
- **Never add `Signed-off-by` tags.** Only human maintainers can legally certify the Developer Certificate of Origin (DCO).
- **Never commit secrets.** Production credentials in `.env` and API tokens (`CTFD_ADMIN_TOKEN`) must remain untracked in `.gitignore`.
- **Never leak challenge solutions, flags, or solve paths** into participant-facing documentation in [docs/participant_kit/](docs/participant_kit/).
- **Never reference real university staff, actual faculty members, or real campus infrastructure** in challenge lore or flags. All names and systems must remain 100% fictional.
- **Never run raw `pip install` or unpinned dependencies.** Always use `uv` and pin dependencies in `pyproject.toml` / `uv.lock`.
- **Never perform manual out-of-band mutations** directly inside running containers (`docker exec ...`) that bypass git tracking.

---

## 4. Challenge Authoring & Anti-AI Standards

All 14 challenges must adhere to the 5-step authoring standard defined in [challenges/README.md](challenges/README.md):
1. **Directory Structure:** Placed in `challenges/<challenge_name>/` containing:
   - `challenge.yml` (ctfcli-compliant specification).
   - `README.md` (Step-by-step authoring rationale and full walkthrough solution).
   - `generate.py` / generator assets (scripts used to compile the evidence artifact).
   - `solve.py` / solver script (automated reproducer and flag extractor).
   - `files/` or `dist/` (clean files distributed to participants).
2. **Anti-AI Engineering Principles:**
   - LLMs can easily solve generic textbook CTF challenges. Every challenge in this CTF **must** incorporate at least one anti-AI defensive layer:
     - **Multimodal / Frequency Stego:** Visual flags synthesized in audio spectrograms or layered images that text-only LLMs cannot process.
     - **Fragmented Non-Standard Encodings:** Splitting chunks across custom boundaries so public writeup scrapers fail.
     - **Physical / Volatile Presence:** Requiring interaction with the physical Lab 207 terminal or memory dumps.
     - **Contextual Adversarial Traps:** Proctor bot prompt-injection challenges with honeyflags (`case{nice_try_chatgpt_prompt_injection_failed}`).
     - **Custom Campus Corpus:** Password hashes cracking requiring wordlists constructed from [Case_Briefing_Dossier.md](docs/participant_kit/Case_Briefing_Dossier.md) lore rather than standard `rockyou.txt`.
     - **Stripped / Custom Binaries:** Reversing binaries with non-standard XOR keys and stripped symbols.
3. **5-Step Verification Protocol:**
   - Every challenge must be independently solve-tested by an uninitiated team member without reading `README.md`.
   - Verified that solving time fits comfortably within the 1-hour active window.
   - Flag strings verified for exact case and whitespace trimming.

---

## 5. Unified CLI Operations (`uv run ctf`)

| Command | Action | Operational Note |
| :--- | :--- | :--- |
| `uv run ctf start` | Launch stack | Auto-detects container engine and LAN IP on port 80 |
| `uv run ctf status` | Health check | Reports state of `ctfd_app`, `ctfd_proxy`, `ctfd_db`, `ctfd_cache` |
| `uv run ctf stop` | Graceful stop | Stops containers without wiping named volumes |
| `uv run ctf backup` | Snapshot state | Archives DB dump + `/var/uploads` to `backups/ctfd_backup_<timestamp>.tar.gz` |
| `uv run ctf restore`| Disaster recovery | Restores database and upload assets for instant standby failover |
| `uv run ctf sync <IP>`| Standby sync | Pushes latest snapshot over LAN to secondary laptop via SSH/SCP |
| `uv run ctf events` | Timeline console| Interactive menu for clue drops, vanishing challenges, and lightning rounds |
| `uv run ctf blackout`| 5:15 PM freeze | Freezes live scoreboard into suspense mode |
| `uv run ctf reveal` | 5:30 PM unfreeze| Reveals final scoreboard for closing ceremony |
| `uv run ctf theme` | Apply theme & projector | Activates primary theme (`m0xblood`) and pushes `ctfd-theme/` projector styling |
| `uv run ctf seed` | Seed challenges | Idempotently populates challenges, flags, files, and dynamic scoring |
| `uv run ctf setup` | Full auto-setup | One-shot stack bootstrap, challenge seeder, theme & API bindings |

---

## 6. Subsystem References & Pre-Flight Checklist
- **Live Event Master Dossier & Operations Plan:** See [EVENT.md](EVENT.md).
- **Live Event Timeline & Ops Playbook (4:30–5:30 PM):** See [docs/TECH_LEAD_RUNBOOK.md](docs/TECH_LEAD_RUNBOOK.md) and [ops/](ops/).
- **Big-Screen AV Experience:** See [ctfd-theme/](ctfd-theme/) (scoreboard projector styling, applied via `uv run ctf theme`) and [av-console/](av-console/) (countdown clock + sound cue board, served at `/av-console/`).
- **Challenge Authoring & Scaffolding:** See [challenges/README.md](challenges/README.md) and template in [challenges/template/](challenges/template/).
- **Proxy & MariaDB Engine Tuning:** See [conf/nginx/default.conf](conf/nginx/default.conf) and [conf/mysql/my.cnf](conf/mysql/my.cnf).
- **Handoff Documentation:** See [HANDOFF.md](HANDOFF.md).
- **Technical & Lore Notebook:** See [NOTES.md](NOTES.md).

**Pre-Flight Verification Checklist:**
`[ ] All context docs read?`  
`[ ] Context docs updated alongside changes?`  
`[ ] Declarative?`  
`[ ] Reproducible?`  
`[ ] Backup created if stateful?`  
`[ ] Zero drift?`  
`[ ] Reproducer verified?`  
`[ ] Anti-AI layer validated?`  
`[ ] No Signed-off-by?`
