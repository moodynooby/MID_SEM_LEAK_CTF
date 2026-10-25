# EVENT.md — Event Master Dossier & Operations Plan
> **Case File: The Mid-Sem Leak** | IEEE AUSB Annual Cybersecurity CTF  
> **Date:** Wednesday, 28 October 2026 | **Time:** 2:00 PM – 6:00 PM IST  
> **Venues:** Computer Labs 207 & 208, GICT Building, Ahmedabad University  
> **Live Server:** Standalone Campus LAN (Port 80) | Hot-Standby Failover Target: `< 2 min`  

---

## 1. Executive Summary & Event Overview
**Case File: The Mid-Sem Leak** is an immersive, forensics-driven cybersecurity Capture The Flag (CTF) competition organized by the **IEEE Ahmedabad University Student Branch (IEEE AUSB)**. Designed for 20 teams (40–80 undergraduate engineering and computing students), the event drops participants into a realistic digital forensics mystery: tracing the illicit leak of the **OOP 99 (Object Oriented Programming Systems)** mid-semester examination paper drafted by **Prof. Hasmukh Chelaiya**.

Unlike conventional text-heavy or generic online CTFs, this competition is:
- **100% Offline & Campus LAN Hosted:** Operates locally on Lab port 80 with zero reliance on cloud services or external internet for the core CTFd engine and scoreboards.
- **Narrative-Driven:** 14 challenges formatted as classified digital evidence dockets (network logs, memory dumps, intercepted emails, reverse-engineered binaries, and audio wiretaps).
- **Gamified & Anti-AI Hardened:** Features an interactive live projector dashboard, sound cue board, intrusion siren alerts, a spinning prize/punishment wheel, hot-sauce lifelines, a 15-minute vanishing bonus challenge, a 10-minute double-points lightning round, and a climactic 15-minute scoreboard blackout.

---

## 2. Key Personnel & Operational Roster

| Role | Name | GitHub / Contact | Primary Responsibility |
| :--- | :--- | :--- | :--- |
| **Core Organizer & Lead** | **Vansh Shah** | Event Coordination | Overall event logistics, faculty liaison, room bookings, and participant management. |
| **Co-Tech Lead** | **Manas Doshi** | `@moodynooby` | Server infrastructure, MariaDB/Nginx configuration, CLI tooling, blackout/reveal execution. |
| **Co-Tech Lead** | **Krish** | `@Krish-452` | Hot-standby sync, timed event automations, scoreboard projector management, hint releases. |
| **Track Lead: Forensics & Stego**| **Yesha** | Reserved | Evidence split parts, audio spectrogram wiretap, redacted PDF, physical RAM dump. |
| **Track Lead: Web & AI** | **Tanish Shah** | `@tanishshahh` | Cookie/API challenges, proctor bot jailbreak, PHP web shell, intrusion siren alerts. |
| **Track Lead: Crypto & Reversing**| **Vidit** | `@viditd1-eng` | CTFd UI theme, Android APK reversing, password hash cracking, Safe Exam Browser reversing. |
| **Track Lead: Network & Logs** | **Vatsal Pandya** | `@VP1107` | Wi-Fi/DNS auto-sync logs, ransomware PCAP, deleted file recovery, angry TA emails, spin wheel app. |
| **Floor Mentors & Volunteers** | **IEEE Student Volunteers**| Labs 207 & 208 | Participant verification, LAN cable checks, dossier handouts, hot sauce administration. |

---

## 3. Minute-by-Minute Master Schedule (28 October 2026)

```
2:00 PM  ─── Setup & Hardware Staging (Tech Leads & Volunteers)
2:30 PM  ─── Participant Check-in & Team Seating (Labs 207 & 208)
3:00 PM  ─── Expert Talk & Pre-Event Technical Session
4:00 PM  ─── Case Briefing & Rules Announcement
4:30 PM  ─── 🚀 COMPETITION COMMENCES (1-Hour Active Window)
4:35 PM  ─── ⏳ 15-Min Vanishing Bonus Challenge Appears
4:45 PM  ─── 📂 Intel Clue Drop #1 & Spin Wheel Lifeline #1
4:50 PM  ─── 🔒 Vanishing Bonus Challenge Expires
5:00 PM  ─── ⚡ 10-Min Double-Points Lightning Round & Lifeline #2
5:10 PM  ─── ⚡ Lightning Round Closes & Intel Clue Drop #2
5:15 PM  ─── 🌑 SCOREBOARD BLACKOUT (Suspense Mode Triggered)
5:30 PM  ─── 🏁 COMPETITION CLOSES (Submissions Locked)
5:35 PM  ─── 🏆 Scoreboard Reveal & Fictional Culprit Unmasked
5:45 PM  ─── 🎁 Awards Ceremony, Certificates & Closing Remarks
```

### Detailed Timeline Breakdown

#### Phase I: Pre-Event Staging & Arrival (2:00 PM – 3:00 PM)
- **2:00 PM – Lab Access & Infrastructure Boot:**
  - Power up the **Primary Server Host** in Lab 207 and the **Standby Host** in Lab 208.
  - Connect hosts to Gigabit Lab Switches. Verify LAN IP binding (`ip -4 addr show` / `Get-NetIPAddress`).
  - Execute `uv run ctf start` and verify container health via `uv run ctf status`.
  - Connect HDMI feeds to Lab 207 and Lab 208 ceiling projectors; open `http://localhost/scoreboard` in Fullscreen (`F11`).
- **2:30 PM – Participant Ingress & Team Check-in:**
  - Floor volunteers check team tickets at Lab entrances.
  - Teams are directed to assigned lab terminals (2–4 members per team, 20 total teams).
  - Distribute physical **Classified Incident Briefing Dossiers** and printed scratchpads.

#### Phase II: Speaker Session & Briefing (3:00 PM – 4:30 PM)
- **3:00 PM – 4:00 PM – Expert Talk / Pre-Event Session:**
  - Guest speaker / faculty session on modern cyber forensics, network incident response, and ethical hacking.
  - While participants listen, Tech Leads verify all 20 team accounts in CTFd and test snapshot synchronization:
    ```bash
    uv run ctf backup
    uv run ctf sync <STANDBY_LAPTOP_IP>
    ```
- **4:00 PM – 4:30 PM – Briefing, Lore Reveal & Rules Review:**
  - Organizer Vansh Shah introduces the case premise: The OOP 99 exam paper has leaked, and the investigation begins now.
  - Review rules: flag format (`case{...}`), dynamic scoring formula, strict prohibition of network attacks against CTFd.
  - Floor volunteers verify all teams can successfully log in at `http://<LAN_IP>`.

#### Phase III: Active Competition Window (4:30 PM – 5:30 PM)
- **4:30 PM – Competition Commences:**
  - Tech Leads trigger the opening fanfare audio cue; CTFd scoreboard activates.
  - First Blood alerts active for all 14 challenges.
- **4:35 PM – Vanishing Bonus Challenge Unlocked (15-Min Window):**
  - CLI: `uv run ctf events --event vanishing_start`.
  - Temporary volatile evidence docket appears in CTFd.
- **4:45 PM – Clue Drop #1 & Spin Wheel Round 1:**
  - CLI: `uv run ctf events --event clue_drop_1`.
  - The live Projector Spin Wheel activates! Teams that have not scored may spin the wheel or take a Hot Sauce shot for a free unpenalized hint.
- **4:50 PM – Vanishing Challenge Expiration:**
  - CLI: `uv run ctf events --event vanishing_end`.
  - Unsolved vanishing evidence disappears from CTFd.
- **5:00 PM – 10-Minute Lightning Round (Double Points) & Clue Drop #2:**
  - CLI: `uv run ctf events --event lightning_start`.
  - High-intensity speed puzzle unlocked; solves within the next 10 minutes earn 2x points!
- **5:10 PM – Lightning Round Closes:**
  - CLI: `uv run ctf events --event lightning_end` then `uv run ctf events --event clue_drop_2`.
- **5:15 PM – Scoreboard Blackout (The Final 15 Minutes):**
  - CLI: `uv run ctf blackout`.
  - MariaDB freezes public score calculations. Projectors switch to a high-tension glitch graphic: **"LOCKDOWN ACTIVE — SCOREBOARD FROZEN"**.
  - All solves continue to be logged silently on the backend.
- **5:30 PM – Competition Concludes:**
  - Siren sounds; all flag submissions locked in CTFd.

#### Phase IV: Closing Ceremony & Awards (5:30 PM – 6:00 PM)
- **5:35 PM – Live Scoreboard Reveal:**
  - CLI: `uv run ctf reveal`.
  - Unfreeze the public scoreboard; reveal the final rankings from 20th place down to 1st place!
  - Unmask the fictional culprit (TA Piyush Pelaiya) and present the narrative resolution.
- **5:45 PM – Prize Distribution & Certificates:**
  - Trophies, cash vouchers/prizes, and certificates awarded to Top 3 teams + First Blood Champion.
  - Group photo and closing vote of thanks by IEEE AUSB.

---

## 4. Live Gamification & Projector Mechanics

### A. The Big-Screen Projector Experience
- **Scoreboard Auto-Refresh:** Dedicated fullscreen `/scoreboard` view displaying real-time team ranking, points, solve counts, and dynamic flag badges.
- **First-Blood Ticker:** When a team secures the first solve on any challenge, a neon banner and sound chime trigger across both labs.
- **Visual Countdown Clock:** A synchronized digital clock on the secondary display counting down to 5:30 PM.

### B. Projector Spin Wheel & Hot Sauce Lifelines (Issue #25)
To prevent teams from getting discouraged during the 1-hour active window, an interactive HTML5 Spin Wheel is projected on the presentation screen during designated windows (4:45 PM and 5:00 PM):
1. **The 8 Wheel Segments:**
   - 🌶️ **Hot Sauce Shot:** Teammate eats a spoonful of spicy hot sauce $\rightarrow$ earns 1 free, unpenalized investigative hint from the Tech Leads!
   - 💡 **Public Intel Drop:** Organizers broadcast a 1-sentence clue on the screen for the entire room.
   - ⚡ **5-Min Speed Window:** Next challenge solved by the team within 5 minutes earns +50 bonus points.
   - 🛑 **2-Min Keyboard Freeze:** The spinning team must step away from their keyboards for 2 minutes.
   - 🎭 **Eliminate a Decoy:** The host officially crosses off one innocent student suspect from the dossier.
   - 🔄 **Teammate Role Swap:** Teammates must swap computers and roles.
   - 🍬 **Sweet Relief:** Candy / chocolate snack delivered to the team.
   - 🚨 **Sound the Alarm:** Blaring alarm siren sounds across the lab speakers for 5 seconds.

### C. Intrusion Punishments & Siren Alerts (Issue #16)
- **Automated Anti-Bruteforce Strobe:** If a team submits **5 incorrect flags consecutively**, CTFd enforces a 60-second submission lockout.
- **Visual Strobe:** A red warning strobe and audio alert flash on the projector screen targeting their terminal station to simulate an incident response intrusion detection system!

---

## 5. Scoring Rules & Flag Format

1. **Flag Format:**
   - Every flag follows the strict canonical syntax: `case{...}`
   - All lowercase prefix, ASCII characters, numbers, and underscores (e.g., `case{ta_piyush_angry_leaked_oop99_mail}`).
   - Case-insensitive trimming applied on submit.
2. **Dynamic Scoring Engine:**
   - **Initial Score:** 500 points.
   - **Decay Solves:** 15 teams (points decrease smoothly with each solve).
   - **Minimum Floor:** 100 points.
   - **Formula:** 
     $$\text{Points} = \max\left(\text{Min}, \text{Round}\left(\left(\frac{\text{Min} - \text{Initial}}{(\text{Decay})^2}\right) \times (\text{Solves} - 1)^2 + \text{Initial}\right)\right)$$
3. **Tie-Breaker Rule:**
   - If two teams tie on total points, ranking is determined by the timestamp of their last accepted flag submission (earliest timestamp wins).
4. **Hint Penalties:**
   - In-platform hints incur a nominal point deduction (-20 to -50 points).
   - Hot Sauce lifelines grant hints **without** point deductions.

---

## 6. Code of Conduct & Fair Play Rules

1. **No Infrastructure Tampering:**
   - Participants must not run automated denial-of-service, mass fuzzing (`dirbuster`, `gobuster`, `sqlmap`), or brute-force scripts against the CTFd port 80 host or lab switches.
2. **No Inter-Team Collusion or Tampering:**
   - Sharing flags, ARP spoofing, Wi-Fi jamming, shoulder surfing, or modifying other teams' workstations is grounds for immediate disqualification.
3. **Decisions Are Final:**
   - The IEEE AUSB organizing committee and faculty mentors hold final discretion on all rule interpretations and scoring validations.

---

## 7. Technical Infrastructure & Venue Requirements

### Hardware & Network Setup
- **Primary Server:** High-performance laptop/desktop running CTFd stack on Docker Desktop WSL2 / Linux.
- **Secondary Server:** Hot-standby laptop with identical cloned repository and Docker daemon ready.
- **Network:** Campus LAN Gigabit Switch connecting Labs 207 & 208. Primary host bound to static LAN IP.
- **Displays:** Dual 1080p ceiling projectors in Labs 207 & 208 connected via HDMI.
- **Audio:** PA system / lab speakers connected to Tech Lead AV console for fanfares, timers, and siren cues.

### Disaster Contingency (Failover in `< 2 Minutes`)
1. If the Primary Host experiences power failure, hardware freeze, or kernel panic:
2. Unplug the Primary LAN cable.
3. Set the Secondary Laptop to the Primary LAN IP (or broadcast new IP to room).
4. Run `uv run ctf restore` on the Secondary Laptop.
5. Swap HDMI projector cable to the Secondary Laptop.
6. Resume competition immediately. Total recovery target: **< 120 seconds**.

---

## 8. Emergency Contacts & Communication Tree

| Contact | Phone / Discord | Role |
| :--- | :--- | :--- |
| **Vansh Shah** | Event Desk / Lab 207 | Core Organizer & Logistics Escalations |
| **Manas Doshi** | Tech Desk Lab 207 | Server, MariaDB, Docker & Network Infrastructure |
| **Krish** | Tech Desk Lab 208 | Standby Server, Projector AV & Timeline Triggers |
| **Lab Administrator**| GICT Facilities Office | Power, Lab Switches & Air Conditioning |
