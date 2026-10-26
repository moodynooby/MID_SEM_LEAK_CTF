#!/usr/bin/env python3
"""
solve.py — Automated Solver for 'Deleted but Not Gone: Erased Exam Draft Recovery'
Track: Network & Forensics | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Vatsal Pandya (@VP1107)

Solve Path:
    1. Extract 'files/exam_draft_repo.tar.gz'.
    2. Inspect git commit history and reflog for deleted files.
    3. Identify commit adding 'OOP99_exam_draft_v1.pdf' prior to deletion commit.
    4. Carve/checkout the deleted PDF from the historical git object store.
    5. Extract and verify the true flag:
       case{git_reflog_rm_cant_hide_draft}
"""

import sys
import shutil
import subprocess
import tarfile
import re
from pathlib import Path

TARGET_FLAG = "case{git_reflog_rm_cant_hide_draft}"
KNOWN_DECOYS = {"case{decoy_git_log_superficial_commit}"}


def solve(tar_path: Path):
    if not tar_path.exists():
        print(f"[-] Missing challenge archive: {tar_path}")
        sys.exit(1)

    temp_dir = tar_path.parent / ".temp_solve_extracted"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Extracting repository archive: {tar_path}")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(temp_dir)

    repo_dir = temp_dir / "exam_draft_repo"
    if not (repo_dir / ".git").exists():
        print("[-] Error: .git directory not found in extracted archive.")
        sys.exit(1)

    print(f"[+] Git repository located at: {repo_dir}")

    # Step 1: Check active directory listing (file was deleted with rm)
    active_files = [p.name for p in repo_dir.iterdir() if p.name != ".git"]
    print(f"[*] Current active files in working tree: {active_files}")
    if "OOP99_exam_draft_v1.pdf" not in active_files:
        print("  [!] Confirmed: 'OOP99_exam_draft_v1.pdf' is deleted from the active working directory.")

    # Step 2: Query git commit history for commits touching the draft file
    log_cmd = subprocess.run(
        ["git", "log", "--full-history", "--pretty=format:%h %s", "--", "OOP99_exam_draft_v1.pdf"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    print("\n[*] Git Commits Touching 'OOP99_exam_draft_v1.pdf':")
    commits = log_cmd.stdout.strip().split("\n")
    for c in commits:
        print(f"    {c}")

    # Step 3: Identify the commit that introduced the draft file
    find_add_cmd = subprocess.run(
        ["git", "log", "--diff-filter=A", "--pretty=format:%h", "--", "OOP99_exam_draft_v1.pdf"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    add_commit = find_add_cmd.stdout.strip()
    print(f"\n[+] Commit introducing deleted draft: {add_commit}")

    # Step 4: Carve the deleted file object using git show
    carve_cmd = subprocess.run(
        ["git", "show", f"{add_commit}:OOP99_exam_draft_v1.pdf"],
        cwd=repo_dir,
        capture_output=True,
        check=True,
    )
    carved_bytes = carve_cmd.stdout
    print(f"[+] Carved deleted PDF binary ({len(carved_bytes)} bytes, starts with {carved_bytes[:8]})")

    # Step 5: Extract and verify the flag from the carved PDF stream
    pdf_text = carved_bytes.decode("latin-1", errors="replace")
    flag_match = re.search(r"case\{[^}]+\}", pdf_text)
    extracted_flag = flag_match.group(0) if flag_match else None

    # Clean up temp files
    shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("GIT FORENSIC SOLVER VERIFICATION RESULTS:")
    print(f"  Target Flag:    {TARGET_FLAG}")
    print(f"  Extracted Flag: {extracted_flag}")
    print("=" * 60)

    if extracted_flag == TARGET_FLAG:
        print("[+] SUCCESS: Challenge verified cleanly! Extracted flag matches expected.")
        sys.exit(0)
    else:
        print("[-] FAILURE: Flag mismatch or extraction failure.")
        sys.exit(1)


def main():
    repo_root = Path(__file__).resolve().parent
    tar_path = repo_root / "files" / "exam_draft_repo.tar.gz"
    solve(tar_path)


if __name__ == "__main__":
    main()
