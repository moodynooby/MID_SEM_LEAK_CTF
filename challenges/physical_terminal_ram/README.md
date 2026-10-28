# Physical Forensics: Lab 207 Terminal RAM Dump

**Track:** Forensics & Physical Evidence  
**Difficulty:** Medium — 500 → 200 pts (decay 16 solves)  
**Author:** Yesha (Forensics Track Lead)  
**Flag:** `case{volatility3_lab207_terminal_ram}`

---

## 1. Challenge Overview & Canon Storyline
At 02:14 AM on 28 October 2026, campus security quarantined Workstation PC-04 in AU Lab 207 after TA Piyush Pelaiya fled the room. To prevent loss of volatile artifacts before power-off, first responders dumped the active memory of the machine to `/dev/shm/lab207_terminal_ram.raw`.

---

## 2. Anti-AI Defensive Principle
- **Physical Venue Interaction + Real Memory Dump:** Pure web-based LLMs cannot plug into a physical PC or parse 8 MB binary memory structures without code execution.
- **Realistic Linux Memory Structures:** The dump contains authentic LiME memory headers (`0x4c694d45`), glibc heap chunks, process task descriptors, process `environ` vector blocks, and command history rings.
- **Decoy Framed Student Honeyflags:** Blind `strings` carving yields 3 distinct candidate flags (`case{sansh_lab208_checkin_token}`, `case{danas_terminal_footprint_auth}`, and `case{volatility3_lab207_terminal_ram}`). Naive submissions are trapped by CTFd; participants must trace the culprit TA Piyush (PID 1337) and his specific exfiltration command (`EXAM_EXFIL_FLAG`).

---

## 3. Workstation Staging Protocol (Tech Lead Setup)
Before the event starts in Lab 207:
1. Tech Leads execute `stage_workstation.sh` on physical machine **PC-04**:
   ```bash
   chmod +x stage_workstation.sh
   ./stage_workstation.sh
   ```
2. The script copies `lab207_terminal_ram.raw` into volatile memory (`/dev/shm/lab207_terminal_ram.raw`) and displays the Crime Scene terminal banner.
3. Participants can walk up to the machine with a USB flash drive to copy the raw memory snapshot.
4. As a failover precaution against PC reboots or congestion, the exact same memory dump is downloadable directly from the CTFd challenge page.

---

## 4. Step-by-Step Solution Walkthrough

### Method A: Forensic Strings Carving (Fastest)
```bash
strings -a files/lab207_terminal_ram.raw | grep -i "case{"
```
Output:
```text
EXAM_EXFIL_FLAG=case{volatility3_lab207_terminal_ram}
AUTH_HEADER: Bearer case{volatility3_lab207_terminal_ram}
export EXAM_EXFIL_FLAG="case{volatility3_lab207_terminal_ram}"
```

### Method B: Volatility 3 Linux Memory Analysis
Using Volatility 3:
1. Inspect bash history buffer:
   ```bash
   vol -f files/lab207_terminal_ram.raw linux.bash.Bash
   ```
   Output lists the commands typed into terminal PC-04:
   ```text
   export EXAM_EXFIL_FLAG="case{volatility3_lab207_terminal_ram}"
   curl -k -H "X-Vault-Auth: $EXAM_EXFIL_FLAG" https://faculty.ahduni.edu.in/vault/oop99/exam_draft_v1.pdf -o /tmp/exam_draft.pdf
   base64 /tmp/exam_draft.pdf > /dev/shm/exfil.b64
   ```

2. Inspect process environment variables:
   ```bash
   vol -f files/lab207_terminal_ram.raw linux.envars.Envars
   ```
   Identifies PID 1337 (`bash` owned by `ta_piyush`) with `EXAM_EXFIL_FLAG=case{volatility3_lab207_terminal_ram}`.

### Method C: Automated Repository Solver
```bash
uv run python challenges/physical_terminal_ram/solve.py
```
Output:
```text
[*] Solving Physical Forensics RAM Dump challenge from: .../lab207_terminal_ram.raw
[+] Loaded memory dump (8388640 bytes / 8.0 MB)
[+] Confirmed valid LiME memory format (Range: 0x10000000 - 0x107fffff)
[+] Recovered flag via memory carving: case{volatility3_lab207_terminal_ram}
[+] Found process environment vector: EXAM_EXFIL_FLAG = case{volatility3_lab207_terminal_ram}
[SUCCESS] Validated Flag: case{volatility3_lab207_terminal_ram}
```

---

## 5. Verification Protocol
1. [x] Authentic 8.0 MB memory dump generated at `files/lab207_terminal_ram.raw`.
2. [x] Physical workstation setup script (`stage_workstation.sh`) tested and operational.
3. [x] LiME memory format header validated.
4. [x] Solver (`solve.py`) verifies flag and process memory structures.
5. [x] Challenge configuration (`challenge.yml`) is valid.
