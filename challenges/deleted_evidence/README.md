# Deleted but Not Gone: Erased Exam Draft Recovery
## Challenge Writeup & Author Rationale

- **Author:** Vatsal Pandya (`@VP1107`)
- **Track:** Network & Forensics (Issue #5 / Challenge #3)
- **Category:** Forensics
- **Estimated Difficulty:** Easy — 300 → 100 pts (decay 20 solves)  
- **Tester / Solve-Verified By:** Krish Poddar (`@Krish-452`) / Manas Doshi (`@moodynooby`)
- **True Flag:** `case{git_reflog_rm_cant_hide_draft}`
- **Decoy Honeyflags:**
  - `case{decoy_git_log_superficial_commit}`

---

## 1. Challenge Concept & Lore

In *Case File: The Mid-Sem Leak*, before transmitting the final leaked PDF via email, **TA Piyush Pelaiya** staged initial draft sections of the upcoming **OOP 99** examination in a local git repository on the Lab 207 workstation.

Upon hearing lab technicians entering Lab 207, Piyush hurriedly ran `rm -f OOP99_exam_draft_v1.pdf` and committed the deletion (`cleanup: remove temporary scratch files`), hoping to hide his possession of the exam draft. However, Git is an immutable append-only content-addressable object store: deleting a file and committing the removal leaves the previous commit and blob fully intact in the `.git/objects/` database.

---

## 2. Anti-AI Defensive Architecture

1. **Active Working Tree Deletion:**
   Extracting the archive and performing standard `ls` or browsing the filesystem reveals no draft PDF, preventing superficial AI directory scrapers from extracting the file directly.

2. **Decoy Plaintext Commit Honeyflags:**
   The active working directory contains a grading rubric with a decoy token (`case{decoy_git_log_superficial_commit}`) that traps blind regex scrapers.

3. **Git Object History Carving:**
   The solver must interrogate the git object model using `git log --full-history`, `git log --diff-filter=A`, or `git show <commit>:<file>` to reconstruct the deleted file.

---

## 3. Walkthrough & Official Solution

### Step 1: Extract the Archive
```bash
tar -xzf files/exam_draft_repo.tar.gz
cd exam_draft_repo
```

Verify that `OOP99_exam_draft_v1.pdf` is absent from the working directory:
```bash
ls -la
```

### Step 2: Query Historical Commits for the Deleted File
```bash
git log --full-history --oneline -- OOP99_exam_draft_v1.pdf
```

Output:
```text
13eeb57 cleanup: remove temporary scratch files
0d19299 feat: stage preliminary OOP99 midsem draft v1
```

### Step 3: Carve the Deleted PDF from Commit `0d19299`
```bash
git show 0d19299:OOP99_exam_draft_v1.pdf > recovered_draft.pdf
```

### Step 4: Extract the Verification Token
Open `recovered_draft.pdf` in a PDF viewer or inspect strings:
```bash
strings recovered_draft.pdf | grep "case{"
```

Output:
```text
case{git_reflog_rm_cant_hide_draft}
```

---

## 4. Hints & Cost Strategy

- **Hint 1 (-25 pts):** "In git, deleting a file with rm does not purge historical commits or tree blobs. Inspect git log with --full-history or check git reflog."

---

## 5. Solve-Test Verification Log

- **Date Tested:** 26/10/2026
- **Automated Verification:** `uv run python challenges/deleted_evidence/solve.py` $\rightarrow$ Exit code 0.
- **Estimated Human Solve Time:** 4–8 minutes.
- **Verification Summary:**
  - Git repository extraction verified across platforms.
  - Historical commit resolution correctly targets commit introducing the deleted draft.
  - Carved PDF confirmed valid with exact flag match.
