# 📋 Competition Rules & Guidelines
## Case File: The Mid-Sem Leak — IEEE AUSB

Welcome investigators! Please read the rules carefully before the competition begins.

---

### 1. General Structure & Schedule
- **Competition Window:** 4:30 PM – 5:30 PM (1 Hour of active investigation).
- **Format:** Jeopardy-style story mystery across 5 Acts and timed bonus rounds.
- **Teams:** 2 to 4 members per team with designated team accounts on CTFd.
- **Flag Format:** `case{...}` (all lowercase prefix, ASCII characters).

---

### 2. Scoring System
1. **Difficulty-Tiered Dynamic Scoring:**
   - Every challenge is tagged **Easy**, **Medium**, or **Hard** — that tag sets its points.
   - Starts at **300 pts** (Easy), **500 pts** (Medium), or **700 pts** (Hard).
   - As more teams solve a challenge, its value decays toward a floor: **100 / 200 / 350** respectively.
   - Because the floor scales with difficulty too, **a hard challenge is always worth more than a medium one, and a medium more than an easy one** — even when everyone has solved it.
   - Your score is always the *current* live value of the challenges you have solved, so early solves pay more than late ones.
2. **First-Blood Bonus:**
   - The first team to solve any challenge receives a special live shout-out and first-blood bonus displayed on the projector!
3. **Double-Points Lightning Round (5:00 – 5:10 PM):**
   - For 10 minutes, any challenge you solve earns its points a **second time** as a separate bonus award.
   - Bonus points are credited to the scoreboard automatically when the round closes at 5:10 PM.
4. **Tie-Breaker Rule:**
   - If two teams tie on total points, the tie is broken in favor of the team that submitted their last scoring flag earliest.

---

### 3. In-Game Hints Policy
- Hints are available on CTFd for each challenge.
- Unlocking a hint incurs a small point deduction (-20 to -50 points).
- If no team has solved a specific challenge by a certain time, organizers may broadcast a free hint to the entire room.
- Floor volunteers are stationed throughout Labs 207 and 208 to give in-character nudges if your team gets completely stuck!

---

### 4. Code of Conduct & Fair Play (Strictly Enforced ⚠️)
The spirit of this event is learning, detective work, and ethical cyber security.

1. **DO NOT Attack the Infrastructure:**
   - Never attack or run automated vulnerability scanners (e.g., sqlmap, gobuster, nikto) against the CTFd server, the database, or the Ahmedabad University campus network.
   - All challenges are solvable using manual analysis or provided scripts.
2. **DO NOT Attack Other Teams:**
   - Jamming Wi-Fi, ARP spoofing, packet sniffing other teams' laptops, or tampering with rival workstations will result in **immediate disqualification**.
3. **DO NOT Brute-Force Flag Submissions:**
   - CTFd enforces rate limits on submissions. Automated flag submission scripts are prohibited.
4. **NO Flag Sharing / Collusion:**
   - Every team must solve their own challenges. Sharing flags between teams results in disqualification for both teams.
5. **Decisions Are Final:**
   - Organizer and faculty mentor decisions are final in all disputes.
