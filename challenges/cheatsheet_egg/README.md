# Flag in Cheatsheet: Participant Kit Easter Egg
## Challenge Writeup & Author Rationale

- **Author:** Vatsal Pandya (`@VP1107`)
- **Track:** Network & Forensics (Issue #5 / Challenge #4)
- **Category:** Misc
- **Estimated Difficulty:** Easy (Dynamic initial: 500, decay: 15, minimum: 100)
- **Tester / Solve-Verified By:** Krish Poddar (`@Krish-452`) / Manas Doshi (`@moodynooby`)
- **True Flag:** `case{always_read_the_cheat_sheet_first}`
- **Decoy Honeyflags:**
  - `case{decoy_superficial_html_comment}`

---

## 1. Challenge Concept & Lore

In *Case File: The Mid-Sem Leak*, every participant team receives an introductory investigator's kit containing the case dossier, tournament rules, and `CTF_101_CheatSheet.md`. 

To reward thorough teams who inspect the provided materials thoroughly before launching heavy automated tools, a hidden Easter egg flag is concealed within the markdown source structure.

---

## 2. Anti-AI Defensive Architecture

1. **HTML Comment Concealment:**
   Rendered markdown views (such as GitHub preview, VS Code preview, or HTML renders) hide comments (`<!-- ... -->`). Superficial browser skimming will miss the token.

2. **Decoy Developer Comments:**
   The file includes a decoy developer comment with a honeyflag (`case{decoy_superficial_html_comment}`) near the top to catch naive top-down regex parsers.

3. **True Easter Egg Block:**
   The true token is embedded in the dedicated footer comment block:
   ```markdown
   <!-- ================================================================= -->
   <!-- IEEE AUSB CTF 2026 OFFICIAL CHEATSHEET EASTER EGG                 -->
   <!-- The observant investigator reads the manual before touching tools. -->
   <!-- REWARD FLAG: case{always_read_the_cheat_sheet_first}              -->
   <!-- ================================================================= -->
   ```

---

## 3. Walkthrough & Official Solution

### Step 1: Open the Raw Markdown Source
Open `docs/participant_kit/CTF_101_CheatSheet.md` or `files/CTF_101_CheatSheet.md` in a raw text editor, or inspect via terminal:

```bash
cat files/CTF_101_CheatSheet.md
```

### Step 2: Search for HTML Comments
```bash
grep -n "case{" files/CTF_101_CheatSheet.md
```

Observe the footer comment block:
```text
REWARD FLAG: case{always_read_the_cheat_sheet_first}
```

The flag is:
`case{always_read_the_cheat_sheet_first}`

---

## 4. Hints & Cost Strategy

- **Hint 1 (-10 pts):** "Have you viewed the raw markdown source code of the cheat sheet? Check the HTML comment tags."

---

## 5. Solve-Test Verification Log

- **Date Tested:** 26/10/2026
- **Automated Verification:** `uv run python challenges/cheatsheet_egg/solve.py` $\rightarrow$ Exit code 0.
- **Estimated Human Solve Time:** 2–5 minutes.
- **Verification Summary:**
  - HTML comments cleanly parsed across raw markdown.
  - Decoy comments verified and isolated.
  - Target flag verified with exact casing.
