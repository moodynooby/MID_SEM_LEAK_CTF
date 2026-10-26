#!/usr/bin/env python3
"""
generate.py — Artifact Generator for 'Deleted but Not Gone: Erased Exam Draft Recovery'
Track: Network & Forensics | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Vatsal Pandya (@VP1107)

Generates:
    challenges/deleted_evidence/files/exam_draft_repo.tar.gz

Storyline Context:
    Before exfiltrating the final exam PDF, TA Piyush Pelaiya staged early draft files
    in a local git repository on the Lab 207 terminal. Realizing he might get caught,
    he attempted to wipe his tracks by executing 'rm -f OOP99_exam_draft_v1.pdf' and
    committing the deletion. However, in git, deleting a file with rm does not purge
    dangling blobs and historical tree objects from the Git object store.

Anti-AI Defensive Layer:
    - Working tree contains no active exam files.
    - Decoy commits with decoy flags (case{decoy_git_log_superficial_commit}).
    - True draft PDF is preserved in git reflog / object database requiring
      'git log -g', 'git reflog', or 'git fsck --lost-found' carving.

True Flag:
    case{git_reflog_rm_cant_hide_draft}
"""

import os
import shutil
import subprocess
import tarfile
from pathlib import Path


def create_minimal_pdf(title: str, lines: list[str]) -> bytes:
    content_stream = "BT\n/F1 12 Tf\n50 740 Td\n16 TL\n"
    escaped_title = title.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content_stream += f"/F1 14 Tf\n({escaped_title}) '\n/F1 10 Tf\n() '\n"
    for line in lines:
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content_stream += f"({escaped}) '\n"
    content_stream += "ET\n"
    stream_bytes = content_stream.encode("latin-1")

    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n")
    xref = []

    xref.append(len(pdf))
    pdf.extend(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    xref.append(len(pdf))
    pdf.extend(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")

    xref.append(len(pdf))
    pdf.extend(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )

    xref.append(len(pdf))
    pdf.extend(f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin-1"))
    pdf.extend(stream_bytes)
    pdf.extend(b"\nendstream\nendobj\n")

    xref.append(len(pdf))
    pdf.extend(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj\n")

    xref_pos = len(pdf)
    pdf.extend(b"xref\n0 6\n0000000000 65535 f \n")
    for offset in xref:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("latin-1"))
    return bytes(pdf)


def build_repo(temp_repo_dir: Path, output_tar: Path):
    if temp_repo_dir.exists():
        shutil.rmtree(temp_repo_dir)
    temp_repo_dir.mkdir(parents=True, exist_ok=True)

    # Initialize git repo
    subprocess.run(["git", "init", "-b", "main"], cwd=temp_repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Piyush Pelaiya"], cwd=temp_repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "piyush.pelaiya@gict.ac.in"], cwd=temp_repo_dir, check=True)

    # Commit 1: Initial course syllabus
    (temp_repo_dir / "README.md").write_text(
        "# OOP 99 & OS 101 Teaching Assistant Workspace\n\n"
        "Internal staging repository for Lab 207 evaluation scripts.\n",
        encoding="utf-8",
    )
    (temp_repo_dir / "grading_rubric.txt").write_text(
        "OS 101 Assignment Grading Notes:\n"
        "- Mutex ordering must be strictly verified.\n"
        "- Decoy Flag Check: case{decoy_git_log_superficial_commit}\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=temp_repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit: TA workspace scaffolding"], cwd=temp_repo_dir, check=True)

    # Commit 2: Add the confidential exam draft PDF
    draft_pdf = create_minimal_pdf(
        "AHMEDABAD UNIVERSITY - OOP 99 MIDSEM DRAFT (CONFIDENTIAL)",
        [
            "COURSE: OOP 99 (Autumn 2026) - EARLY DRAFT V1",
            "INSTRUCTOR: PROF. HASMUKH CHELAIYA",
            "----------------------------------------------------------------",
            "CONFIDENTIAL: STAGED FROM PROFESSOR WORKSTATION SHARE",
            "",
            "QUESTION 1: Virtual Inheritance and Virtual Base Table Offset",
            "QUESTION 2: Concurrent Lock Management & RAII Wrappers",
            "QUESTION 3: Deadlock Analysis & Banker's Algorithm",
            "",
            "[LEAKER RECOVERY TOKEN]:",
            "case{git_reflog_rm_cant_hide_draft}",
            "----------------------------------------------------------------",
        ],
    )
    (temp_repo_dir / "OOP99_exam_draft_v1.pdf").write_bytes(draft_pdf)
    subprocess.run(["git", "add", "OOP99_exam_draft_v1.pdf"], cwd=temp_repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "feat: stage preliminary OOP99 midsem draft v1"], cwd=temp_repo_dir, check=True)

    # Commit 3: TA Piyush panics and deletes the file with rm
    (temp_repo_dir / "OOP99_exam_draft_v1.pdf").unlink()
    subprocess.run(["git", "add", "-u"], cwd=temp_repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "cleanup: remove temporary scratch files"], cwd=temp_repo_dir, check=True)

    # Commit 4: Add benign lab notes
    (temp_repo_dir / "lab_schedule.txt").write_text(
        "Lab 207 Schedule:\n"
        "Wed 14:00 - 16:00: OS 101 Lab Session\n"
        "Thu 16:30 - 18:30: OOP 99 Help Desk\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "lab_schedule.txt"], cwd=temp_repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "docs: update weekly lab hours"], cwd=temp_repo_dir, check=True)

    # Create archive containing the complete git repo
    output_tar.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output_tar, "w:gz") as tar:
        tar.add(temp_repo_dir, arcname="exam_draft_repo")

    # Clean up temp directory
    shutil.rmtree(temp_repo_dir, ignore_errors=True)


def main():
    repo_root = Path(__file__).resolve().parent
    temp_dir = repo_root / ".temp_build_repo"
    out_tar = repo_root / "files" / "exam_draft_repo.tar.gz"

    print(f"[*] Building git forensic challenge repo: {out_tar}")
    build_repo(temp_dir, out_tar)
    print(f"[+] Successfully generated: {out_tar} ({out_tar.stat().st_size} bytes)")
    print("[+] True Flag: case{git_reflog_rm_cant_hide_draft}")


if __name__ == "__main__":
    main()
