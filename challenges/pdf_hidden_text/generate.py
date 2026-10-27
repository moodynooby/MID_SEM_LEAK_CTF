#!/usr/bin/env python3
"""
generate.py — Artifact Generator for 'PDF Hidden Text: The Redacted Exam Paper'
Track: Forensics & Stego | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Yesha (Forensics Track Lead)

Generates:
    challenges/pdf_hidden_text/files/OOP99_Exam_Paper_REDACTED.pdf

Storyline Context:
    Before circulating the official exam schedule, Prof. Hasmukh Chelaiya prepared
    the master draft of the OOP 99 mid-sem examination. Before sending the draft to
    department colleagues, he visually redacted Section C (containing Question 4 and
    the confidential bonus rubric) using black boxes in a PDF editor.
    However, the redaction was purely cosmetic (visual rectangle overlay and #FFFFFF
    text color) without flattening the underlying PDF stream!

Anti-AI Defensive Layer:
    - Looking at an image or screenshot of the PDF reveals only a solid black redaction box.
    - Standard image OCR tools fail on the redacted zone.
    - Pure PDF stream analysis (pdftotext, pdfminer, qpdf, or raw stream decoding)
      reveals the unflattened text operators and the flag.

Flag:
    case{redacted_pdf_layer_text_exposed}
"""

import os
import sys
from pathlib import Path

FLAG = "case{redacted_pdf_layer_text_exposed}"

CHALLENGE_DIR = Path(__file__).resolve().parent
FILES_DIR = CHALLENGE_DIR / "files"
OUTPUT_PDF = FILES_DIR / "OOP99_Exam_Paper_REDACTED.pdf"


def build_pdf_document(output_path: Path):
    """Generates an authentic multi-section university exam PDF with cosmetic redaction."""
    # Page content stream instructions in standard PDF syntax
    # Includes header, questions, solid black redaction bar, and hidden text underneath
    content_lines = [
        # --- UNIVERSITY HEADER ---
        "0.1 0.1 0.1 rg",
        "BT",
        "/F2 16 Tf",
        "50 740 Td",
        "(AHMEDABAD UNIVERSITY - SCHOOL OF ENGINEERING AND APPLIED SCIENCE) Tj",
        "ET",
        "BT",
        "/F1 11 Tf",
        "50 722 Td",
        "(Department of Computer Science & Engineering | Academic Year 2026-2027) Tj",
        "ET",
        "BT",
        "/F2 13 Tf",
        "50 695 Td",
        "(CSE 205: Object-Oriented Programming (OOP 99) - Mid-Semester Exam) Tj",
        "ET",
        "BT",
        "/F1 10 Tf",
        "50 675 Td",
        "(Course Faculty: Prof. Hasmukh Chelaiya    | Date: 28 Oct 2026 | Time: 2 Hours | Max Marks: 50) Tj",
        "ET",
        # Decorative divider line
        "0.3 0.3 0.3 RG",
        "1.5 w",
        "50 660 m",
        "562 660 l",
        "S",
        # --- INSTRUCTIONS ---
        "BT",
        "/F3 9 Tf",
        "50 642 Td",
        "(CONFIDENTIAL DRAFT - PRE-DISTRIBUTION REVIEW COPY. UNAUTHORIZED SHARING STRICTLY FORBIDDEN.) Tj",
        "ET",
        # --- SECTION A ---
        "BT",
        "/F2 11 Tf",
        "50 615 Td",
        "(SECTION A: Inheritance Models & Dynamic Polymorphism [15 Marks]) Tj",
        "ET",
        "BT",
        "/F1 10 Tf",
        "50 595 Td",
        "(Q1. [8 Marks] Explain the internal memory layout of a C++ vtable pointer (__vptr).) Tj",
        "0 -15 Td",
        "(    Discuss how multiple inheritance complicates virtual table offsets and pointer fixups.) Tj",
        "0 -20 Td",
        "(Q2. [7 Marks] Analyze the diamond problem in C++ and explain how virtual base classes) Tj",
        "0 -15 Td",
        "(    resolve ambiguous member variable instantiation.) Tj",
        "ET",
        # --- SECTION B ---
        "BT",
        "/F2 11 Tf",
        "50 515 Td",
        "(SECTION B: Memory Management & Object Lifetime [15 Marks]) Tj",
        "ET",
        "BT",
        "/F1 10 Tf",
        "50 495 Td",
        "(Q3. [15 Marks] Evaluate the implementation of RAII in custom smart pointers.) Tj",
        "0 -15 Td",
        "(    Demonstrate how std::weak_ptr prevents reference-count cycles in graph nodes.) Tj",
        "ET",
        # --- SECTION C (COSMETICALLY REDACTED) ---
        "BT",
        "/F2 11 Tf",
        "50 435 Td",
        "(SECTION C: Advanced Systems & Security Analysis [20 Marks] - [REDACTED SECTION]) Tj",
        "ET",
        # Redaction rectangle drawn in solid black
        "0 0 0 rg",
        "0 0 0 RG",
        "48 330 515 90 re",
        "f",
        # Underneath / in the same layer: text rendered in white #FFFFFF (1 1 1 rg)
        "1 1 1 rg",
        "BT",
        "/F2 10 Tf",
        "55 395 Td",
        "(QUESTION 4 [CLASSIFIED BONUS SECTION - 20 MARKS]:) Tj",
        "ET",
        "BT",
        "/F1 9 Tf",
        "55 375 Td",
        "(Faculty Solution & Master Rubric: Analyze vulnerability CVE-2026-9901 in TA grading sandbox.) Tj",
        "0 -14 Td",
        f"(LEAKED ANSWER KEY FLAG: {FLAG}) Tj",
        "0 -14 Td",
        "(Investigative Note: File recovered from TA Piyush Pelaiya workstation staging cache.) Tj",
        "ET",
        # Footer
        "0.5 0.5 0.5 rg",
        "BT",
        "/F1 8 Tf",
        "220 50 Td",
        "(AU Exam Cell -- Confidential Document -- Page 1 of 1) Tj",
        "ET",
    ]

    stream_content = "\n".join(content_lines) + "\n"
    stream_bytes = stream_content.encode("utf-8")
    stream_len = len(stream_bytes)

    # Construct complete valid PDF with xref table
    objects = []
    offsets = []

    # Header
    pdf_header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    current_offset = len(pdf_header)

    # Object 1: Catalog
    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    offsets.append(current_offset)
    current_offset += len(obj1)
    objects.append(obj1)

    # Object 2: Pages
    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    offsets.append(current_offset)
    current_offset += len(obj2)
    objects.append(obj2)

    # Object 3: Page
    obj3 = (
        b"3 0 obj\n"
        b"<< /Type /Page\n"
        b"   /Parent 2 0 R\n"
        b"   /MediaBox [0 0 612 792]\n"
        b"   /Resources <<\n"
        b"      /Font <<\n"
        b"         /F1 4 0 R\n"
        b"         /F2 5 0 R\n"
        b"         /F3 6 0 R\n"
        b"      >>\n"
        b"   >>\n"
        b"   /Contents 7 0 R\n"
        b">>\n"
        b"endobj\n"
    )
    offsets.append(current_offset)
    current_offset += len(obj3)
    objects.append(obj3)

    # Object 4: Font F1 (Helvetica)
    obj4 = b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    offsets.append(current_offset)
    current_offset += len(obj4)
    objects.append(obj4)

    # Object 5: Font F2 (Helvetica-Bold)
    obj5 = b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n"
    offsets.append(current_offset)
    current_offset += len(obj5)
    objects.append(obj5)

    # Object 6: Font F3 (Helvetica-Oblique)
    obj6 = b"6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique >>\nendobj\n"
    offsets.append(current_offset)
    current_offset += len(obj6)
    objects.append(obj6)

    # Object 7: Contents Stream
    obj7_header = f"7 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("utf-8")
    obj7_footer = b"\nendstream\nendobj\n"
    obj7 = obj7_header + stream_bytes + obj7_footer
    offsets.append(current_offset)
    current_offset += len(obj7)
    objects.append(obj7)

    # Cross-reference table
    xref_offset = current_offset
    xref_lines = [
        f"xref\n0 {len(objects) + 1}\n",
        "0000000000 65535 f \n"
    ]
    for off in offsets:
        xref_lines.append(f"{off:010d} 00000 n \n")
    xref = "".join(xref_lines).encode("utf-8")

    # Trailer
    trailer = (
        f"trailer\n"
        f"<< /Size {len(objects) + 1}\n"
        f"   /Root 1 0 R\n"
        f">>\n"
        f"startxref\n"
        f"{xref_offset}\n"
        f"%%EOF\n"
    ).encode("utf-8")

    pdf_data = pdf_header + b"".join(objects) + xref + trailer
    output_path.write_bytes(pdf_data)
    print(f"[+] Generated PDF exam paper at: {output_path} ({len(pdf_data)} bytes)")


def main():
    print("[*] Generating 'PDF Hidden Text: The Redacted Exam Paper' artifacts...")
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    build_pdf_document(OUTPUT_PDF)
    print("[+] Done.")


if __name__ == "__main__":
    main()
