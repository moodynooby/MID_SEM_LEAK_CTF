# Challenge Authoring & Verification Standard
## Case File: The Mid-Sem Leak — IEEE AUSB

Welcome challenge authors and testers! Every challenge in this CTF is an evidence piece in the overarching campus investigation.

---

### 1. Active Challenge Tracks (15 Challenges)

| Track | Challenge Name | Category | Difficulty (Tier: 1st solve → floor) | Target Description |
| :--- | :--- | :--- | :--- | :--- |
| **Forensics** | [Liam's Idea: Fragmented Exfiltration](fragmented_exfiltration/) | Forensics | Easy (300 → 100) | Exfiltrated video split into Base64 parts (`part*.txt`). |
| **Forensics** | [PDF Hidden Text: The Redacted Exam Paper](pdf_hidden_text/) | Forensics | Easy (300 → 100) | Leaked OOP 99 paper with white text / hidden stream. |
| **Forensics** | [Audio Spectrogram: Lab Microphone Wiretap](audio_spectrogram/) | Stego | Medium (500 → 200) | Ambient audio with visual flag synthesized into frequencies. |
| **Forensics** | [Physical Forensics: Lab 207 Terminal RAM Dump](physical_terminal_ram/) | Forensics | Medium (500 → 200) | Physical crime scene PC memory dump in Lab 207. |
| **Forensics** | [Deleted but Not Gone: Erased Draft](deleted_evidence/) | Forensics | Easy (300 → 100) | Inode / commit recovery of erased exam paper draft. |
| **Forensics** | [Email Forensics: Angry TA's Mails](email_forensics/) | Forensics | Medium (500 → 200) | Mail spool of TA Piyush's angry emails to Prof. Chelaiya. |
| **Web & AI** | [Cookie / API: Faculty Exam Vault](cookie_api/) | Web | Easy (300 → 100) | Client-side cookie tampering / hidden REST endpoint. |
| **Web & AI** | [AI Model Prompt: Proctor Bot Jailbreak](ai_prompt_injection/) | AI | Medium (500 → 200) | Adversarial prompt injection against TA proctor bot. |
| **Web & AI** | [PHP2SHELL: Insecure Faculty Upload](php2shell/) | Web | Hard (700 → 350) | File upload filter bypass to web shell execution. |
| **Reversing** | [APK Reverse Engineer: Companion App](apk_companion_reversing/) | Mobile / Rev | Medium (500 → 200) | Decompiling campus Android app in JADX. |
| **Crypto** | [Password Cracking: Faculty Vault](password_cracking/) | Crypto | Hard (700 → 350) | Cracking encrypted archive using custom campus wordlist. |
| **Reversing** | [Safe Exam Browser (SEB): Windows Kiosk Reversing](seb_binary/) | Reverse Eng | Hard (700 → 350) | Reversing stripped Windows PE64 lockdown binary (`SEB_KioskGuard.exe`) with 4-tier anti-debug & self-integrity checksum trap. |
| **Network** | [DNS / Wi-Fi Logs: 2:13 AM Auto-Sync](wifi_dns_logs/) | Network | Medium (500 → 200) | Aruba Wi-Fi log revealing professor midnight cloud sync. |
| **Network** | [Ransomware Infected: Backdoor PCAP](ransomware_pcap/) | Network | Medium (500 → 200) | Isolate malicious HTTP POST traffic & extract webshell key. |
| **Misc** | [Flag in Cheatsheet: Participant Kit Egg](cheatsheet_egg/) | Misc | Easy (300 → 100) | Stealthy Easter egg concealed in investigator cheatsheet. |

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

### 3. Difficulty-Tiered Dynamic Scoring

Every `challenge.yml` **must** declare `difficulty:` — it is the authoritative
point weight, not a free-text tag. [ops/seed_challenges.py](ops/seed_challenges.py)
maps it to a CTFd dynamic-scoring band:
| `difficulty:` | Initial (1st solve) | Decay Solves | Floor |
| :--- | :---: | :---: | :---: |
| `easy` | **300** | 20 | 100 |
| `medium` | **500** | 16 | 200 |
| `hard` | **700** | 12 | 350 |

```yaml
category: "Forensics"
difficulty: "hard"     # easy | medium | hard  -> selects the band above
value: 700             # MUST equal extra.initial
type: dynamic
extra:
  initial: 700
  decay: 12
  minimum: 350
```

Resolution order in the seeder: explicit `extra:` values in the YAML override the
tier defaults, which override the legacy flat `500/15/100`. A missing or invalid
`difficulty:` prints a warning and falls back to `500/15/100`, so **always keep
the four fields in lockstep**. `value:` is overwritten from the tier at seed time
because `challenges.value` is what the API/UI display, while CTFd prices the
first solve off `dynamic_challenge.initial`.

Because floors scale with difficulty, a hard challenge can never decay to the
same value as an easy one, and `hard > medium > easy` holds at every solve count.
Kept deliberately in mind: CTFd re-prices dynamic challenges **retroactively** (a
team's score is the sum of the *current* value of everything it solved), so
time-boxed bonuses must be paid as discrete awards — see
[ops/manage_timed_events.py](ops/manage_timed_events.py).

Existing per-challenge `extra:` overrides are allowed for hand-tuning, but they
break the tier guarantee — document the reason in the challenge `README.md`.

- **First Blood:** The first team to solve earns an automated announcement on the live scoreboard.

---

### 4. Mandatory Verification Checklist (Before 25/10/2026)
As per the event proposal, **every challenge must be solve-tested by someone other than its author**:
1. [ ] Author submits `challenge.yml`, `README.md` (with step-by-step solution), and all files.
2. [ ] Independent tester solves the challenge without looking at the solution `README.md`.
3. [ ] Time required to solve is recorded (ensure it fits the 1-hour active window).
4. [ ] Prepared hint is written with a small point cost (e.g. -25 to -50 pts).
5. [ ] Flag is tested for copy-paste whitespace sensitivity.
6. [ ] After `uv run ctf seed`, the challenge actually **opens** in the participant board. `challenge.yml` may set `max_attempts` (default `0`, unlimited); the seeder writes it explicitly because CTFd only defaults that column at the ORM layer — a `NULL` value makes `/api/v1/challenges/<id>` return 500 and the UI throw `can't access property "type_data", r is undefined`.
7. [ ] After `uv run ctf seed`, every `files:` entry shows a working **download link** in the challenge modal. Attachment rows must be `files.type='challenge'` (CTFd polymorphic inheritance); `type='standard'` rows download by direct URL but never render a link.
8. [ ] If you **regenerate** a distributed artifact (`generate.py` → `files/`), re-run `uv run ctf seed` and confirm the live download changed. Uploads are keyed by content hash, so the seeder prunes stale rows/blobs (`sync_challenge_files()`); otherwise the board keeps serving the old file under the old `/files/<sha1>/` URL. Verify with `SELECT challenge_id, location FROM files` (one row per YAML entry) and compare `sha1sum` against disk.

---

### 5. Hosted Service Challenges (`cookie_api`, `ai_prompt_injection`, `php2shell`)

These three ship an `app.py` + `Dockerfile` and run as containers on the LAN — they are **not** file-drop forensics and need an extra gate before the event:

1. [ ] `docker compose build <service>` after any `app.py` edit — `docker compose up -d` alone reuses the stale image and you will debug the old bug in production.
2. [ ] `uv run python challenges/<svc>/solve.py http://127.0.0.1:<port>` exits **0** against the live container.
3. [ ] `docker compose ps` reports `(healthy)` for all three, and `uv run ctf status` shows the service table with `200 OK`.
4. [ ] Only `challenge_php2shell` is stateful: uploads are stored as `<uuid6>_<name>` and nothing else resolves. Never re-add an un-prefixed fallback — it breaks multi-team isolation and `solve.py` asserts against it.
5. [ ] `challenge_proctor_bot` needs the host Ollama bound to the docker bridge ([conf/ollama/override.conf](../conf/ollama/override.conf)). Without it the service still answers via the deterministic fallback, so a green `solve.py` does **not** prove the model path works — check `uv run ctf status` for the Ollama warning.
