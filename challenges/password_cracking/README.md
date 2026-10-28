# Password Cracking: Faculty Vault & Campus Wordlist
## Case File: The Mid-Sem Leak — IEEE AUSB CTF 2026

**Track:** Binary & Crypto / Custom Cryptography  
**Difficulty:** Hard — 700 → 350 pts (decay 12 solves)  
**Author:** Vidit (@viditd1-eng)  
**Target File:** `files/confidential_vault.zip`  
**Flag:** `case{custom_hashcat_wordlist_cracked_vault}`  
**Password:** `AU207_OS101_Piyush2026!`  

---

### 1. Narrative & Canon Lore
In Act II of the incident, responders isolated an encrypted archive (`confidential_vault.zip`) from the faculty network share on `workstation-lab-207.local`. The archive contains Prof. Chelaiya's master draft for the confidential **OOP 99 (Object Oriented Programming Systems)** examination along with a taunting advisory note left by the intruder.

The file is encrypted with PKZIP traditional stream encryption. When interviewed, lab assistants revealed that faculty and staff frequently construct passphrases by stringing together laboratory locations, course codes, and department names.

---

### 2. Anti-AI Defensive Layer
- **Immunity to Standard Dictionaries:** Standard wordlists like `rockyou.txt` or general online Rainbow tables will completely fail because the password `AU207_OS101_Piyush2026!` is unique to this campus scenario.
- **Contextual Synthesis Required:** Generic LLMs prompted with the zip file or hash cannot crack it without synthesizing combinations derived from the **Case Briefing Dossier** (`docs/participant_kit/Case_Briefing_Dossier.md`).
- **Entity Correlation:** Participants must combine:
  - Lab: `AU207` / `AU208`
  - Course: `OS101` / `OOP99`
  - Primary Suspect: `Piyush`
  - Year: `2026`
  - Suffix: `!`

---

### 3. Step-by-Step Walkthrough Solution

#### Step 1: Extract Archive Hash
Using `zip2john` (packaged with John the Ripper):
```bash
zip2john files/confidential_vault.zip > vault_hash.txt
```

#### Step 2: Generate Targeted Wordlist
Create a custom dictionary generator script (`generate_wordlist.py`):
```python
import itertools

labs = ["AU207", "AU208", "207", "208"]
courses = ["OS101", "OOP99"]
suspects = ["Piyush", "Pelaiya", "ManMishra", "Chelaiya", "Sansh", "Danas", "Prish", "Tryan", "Parsh"]
years = ["2026", "2025"]
symbols = ["!", "@", "#", "$"]

with open("campus_wordlist.txt", "w") as out:
    for lab, course, suspect, yr, sym in itertools.product(labs, courses, suspects, years, symbols):
        out.write(f"{lab}_{course}_{suspect}{yr}{sym}\n")
```
Run the generator to produce `campus_wordlist.txt` (approx. 288–1,500 targeted candidates).

#### Step 3: Crack with John the Ripper or Hashcat

**Using John the Ripper:**
```bash
john --wordlist=campus_wordlist.txt vault_hash.txt
```
Output:
```
Loaded 1 password hash (PKZIP [32/64])
AU207_OS101_Piyush2026! (files/confidential_vault.zip)
```

**Using Hashcat:**
```bash
hashcat -m 17200 vault_hash.txt campus_wordlist.txt
```

#### Step 4: Extract Archive & Read Flag
Extract the archive using the cracked password:
```bash
unzip -P "AU207_OS101_Piyush2026!" files/confidential_vault.zip
cat faculty_vault_flag.txt
```
Output:
```
case{custom_hashcat_wordlist_cracked_vault}
```

---

### 4. Automated Solver Verification
Execute the automated solver:
```bash
python3 solve.py
```
Exit code `0` confirms the dictionary generator cracks the archive and verifies the flag.
