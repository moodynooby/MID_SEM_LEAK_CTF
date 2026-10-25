# AGENTS.md — Agent Governance & Operational Constitution
> **Case File: The Mid-Sem Leak** | IEEE AUSB CTF (28 Oct 2026, GICT Labs 207 & 208)  
> Tech Leads: Krish, Manas, Vansh Shah

---

## 1. Operational Constraints & Hidden Quirks
- **Zero Cloud & Port 80 LAN:** Standalone local deployment on campus LAN port 80. Scoreboard and challenge access must never rely on external internet access.
- **Hot-Standby Target:** Secondary laptop kept in continuous sync via `uv run ctf sync <IP>` for `< 2-minute` failover.
- **CTFd UI Persistence Gotcha:**
  - Admin UI edits (theme config, custom CSS, pages) write to MariaDB (`config`, `pages` tables) and `/var/uploads` (`ctfd_data` volume).
  - Normal restarts (`uv run ctf stop && uv run ctf start`) preserve volumes.
  - `docker compose down -v` **wipes all UI changes**. Always run `uv run ctf backup` before touching volumes.
  - Custom Jinja2 themes must be declaratively mounted via [docker-compose.yml](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/docker-compose.yml), not edited in-container.

---

## 2. Core Engineering Pillars
1. **Declarative Configuration:** Config files ([docker-compose.yml](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/docker-compose.yml), [conf/](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/conf), `challenges/**/challenge.yml`, [pyproject.toml](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/pyproject.toml), [.env.example](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/.env.example)) are the single source of truth. No manual GUI-only or uncommitted container hacks.
2. **Reproducibility:** A fresh clone on any computer must spin up identically via `uv run ctf start`. Pinned container tags only (`ctfd:3.7.0`, `mariadb:10.11`, `redis:7-alpine`, `nginx:alpine`).
3. **Immutability & Atomic Updates:** Updates progress in generational steps. Recreate containers cleanly via Compose; never live-patch DB without a snapshot generation.
4. **Risk-Free Rollbacks:** Pre-mutation snapshot via `uv run ctf backup` bundles `database.sql` and `/var/uploads` into `backups/ctfd_backup_<timestamp>.tar.gz`. Standby restores with `uv run ctf restore`.
5. **Zero Configuration Drift:** Any deleted feature or challenge must be pruned entirely from code and state. Keep [.env.example](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/.env.example) in lockstep with [.env](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/.env).
6. **Infrastructure as Code (IaC):** Proxy routing, DB tuning, challenge definitions, and event timings are version-controlled code.

---

## 3. Autonomous Actions (Three-Tier Rule)

### Always do:
- Run all operations via the unified CLI: `uv run ctf <command>` ([ctf.py](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/ctf.py)).
- Run `uv run ctf backup` before modifying database schemas, mass-importing challenges, or updating containers.
- Verify any non-trivial bug by creating an isolated reproducer before attempting fixes.
- Attribute AI contributions in commit messages: `Assisted-by: LLM [TOOL1] [TOOL2]`.
- Add `Fixes: <commit_id>` tag when resolving defects.
- Explicitly report limitations if a fix could not be built, tested, or verified against live containers.
- Format challenge flags strictly as `case{...}` (all lowercase prefix, ASCII alphanumeric / leetspeak).

### Ask first:
- Before running destructive operations (`down -v`, volume pruning, table truncations).
- Before modifying live production environment variables in [.env](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/.env).
- Before altering challenge dynamic scoring formulas (Default: 500 initial, 15 decay, 100 min).
- Before disclosing security flaws: classify as bug vs. vulnerability and present to Tech Leads privately.

### Never do:
- **Never add `Signed-off-by` tags.** Only human maintainers can legally certify the Developer Certificate of Origin (DCO).
- **Never commit secrets.** Production credentials in [.env](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/.env) and API tokens (`CTFD_ADMIN_TOKEN`) must remain untracked.
- **Never leak challenge solutions or flags** into participant-facing documentation in [docs/participant_kit/](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/docs/participant_kit/).
- **Never reference real staff, faculty, or real university infrastructure** in challenge lore or flags.
- **Never run raw `pip install` or unpinned dependencies.** Always use `uv`.
- **Never perform manual out-of-band mutations** directly inside running containers (`docker exec ...`) that bypass git.

---

## 4. Unified CLI Operations (`uv run ctf`)

| Command | Action | Operational Note |
| :--- | :--- | :--- |
| `uv run ctf start` | Launch stack | Auto-detects container engine and LAN IP on port 80 |
| `uv run ctf status` | Health check | Reports state of `ctfd_app`, `ctfd_proxy`, `ctfd_db`, `ctfd_cache` |
| `uv run ctf stop` | Graceful stop | Stops containers without wiping named volumes |
| `uv run ctf backup` | Snapshot state | Archives DB dump + `/var/uploads` to `backups/ctfd_backup_<timestamp>.tar.gz` |
| `uv run ctf restore`| Disaster recovery | Restores database and upload assets for instant standby failover |
| `uv run ctf sync <IP>`| Standby sync | Pushes latest snapshot over LAN to secondary laptop |
| `uv run ctf events` | Timeline console| Triggers clue drops, vanishing challenges, and lightning rounds |
| `uv run ctf blackout`| 5:15 PM freeze | Freezes live scoreboard into suspense mode |
| `uv run ctf reveal` | 5:30 PM unfreeze| Reveals final scoreboard for closing ceremony |
| `uv run ctf theme` | Apply projector theme | Pushes `ctfd-theme/` CSS/JS into CTFd's `theme_header`/`theme_footer` configs |

---

## 5. Key Subsystem References & Pre-Flight Checklist
- **Live Event Timeline & Ops (4:30–5:30 PM):** See [docs/TECH_LEAD_RUNBOOK.md](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/docs/TECH_LEAD_RUNBOOK.md) and [ops/](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/ops).
- **Big-Screen AV Experience:** See [ctfd-theme/](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/ctfd-theme) (scoreboard projector styling, applied via `uv run ctf theme`) and [av-console/](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/av-console) (countdown clock + sound cue board, served at `/av-console/`).
- **Challenge Authoring & 5-Step Verification:** See [challenges/README.md](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/challenges/README.md) and blueprint in [challenges/template/](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/challenges/template/).
- **Proxy & MariaDB Engine Tuning:** See [conf/nginx/default.conf](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/conf/nginx/default.conf) and [conf/mysql/my.cnf](file:///home/manas/Desktop/MID_SEM_LEAK_CTF/conf/mysql/my.cnf).

**Pre-Flight Verification:** [ ] Declarative? [ ] Reproducible? [ ] Backup created if stateful? [ ] Zero drift? [ ] Reproducer verified? [ ] No `Signed-off-by`?