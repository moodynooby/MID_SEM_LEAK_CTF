# Challenge Authoring & Verification Standard
## Case File: The Mid-Sem Leak — IEEE AUSB

Welcome challenge authors and testers! Every challenge in this CTF is an evidence piece in the overarching campus investigation.

---

### 1. The Story Arc & Acts

| Act / Stage | Challenge Name | Category | Difficulty | Target Solves | Story Relevance |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Act I** | Evidence Docket #101 (The Incident) | Forensics / Misc | Easy (100-200 pts) | ~80% of teams | Discovery of the security camera artifact or corrupted report. |
| **Act II (Route A)** | Portal Breach (Access Logs) | Forensics / Logs | Easy/Med (200-300 pts) | ~60% of teams | Syslog / Apache log analysis tracing the intruder's IP. |
| **Act II (Route B)** | Portal Breach (Web Vulnerability) | Web Security | Easy/Med (200-300 pts) | ~60% of teams | Analyzing the flawed faculty upload endpoint (dual-path to clue). |
| **Act III** | Encrypted Transmission | Cryptography | Medium (300-400 pts) | ~40% of teams | Intercepted communications between suspicious student accounts. |
| **Act IV** | The Exfiltration Payload | Reverse Eng. | Med/Hard (400-450 pts)| ~25% of teams | Dissecting the script that pulled the exam PDF from the faculty share. |
| **Act V** | Unmasking the Culprit (Final Flag)| Forensics / Web | Hard (500 pts) | ~15% of teams | The final flag naming the fictional mastermind behind the leak. |
| **Bonus 1** | The Vanishing Trace (4:35-4:50 PM)| Forensics | Bonus (250 pts) | Speed solve | Volatile memory / ephemeral cache clue available for 15 mins. |
| **Bonus 2** | Lightning Decryption (5:00-5:10 PM) | Crypto / Speed | Double Pts (300 pts) | Speed solve | Rapid cipher crack in a 10-minute speed window. |

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
