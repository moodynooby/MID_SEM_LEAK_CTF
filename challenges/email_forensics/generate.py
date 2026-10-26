#!/usr/bin/env python3
"""
generate.py — Evidence Generator for 'Email Forensics: The Angry TA's Leaked Mails'
Track: Network & Forensics | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Vatsal Pandya (@VP1107)

Generates:
    challenges/email_forensics/files/leaked_incident_mail.eml

Anti-AI Defensive Architecture:
    1. Multi-layered MIME hierarchy with nested message/rfc822 incident threads.
    2. Multiple decoy attachments containing realistic honeypot flags:
       - case{decoy_os101_rubric_not_the_leak}
       - case{decoy_spoofed_student_submission_flag}
       - case{nice_try_blind_ai_decoy_syllabus}
    3. Spoofed 'From' headers countered by authentic campus gateway routing headers:
       - X-Campus-Auth-User: piyush.pelaiya
       - X-Originating-IP: [10.207.42.19]
    4. Base64-encoded PDF attachment with genuine OOP 99 mid-sem exam paper
       and confession signature flag:
       case{ta_piyush_angry_leaked_oop99_mail}
"""

import os
import base64
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.message import MIMEMessage
from email import encoders
from pathlib import Path


def create_minimal_pdf(title: str, lines: list[str]) -> bytes:
    """Generate a clean, structurally valid PDF-1.4 binary without external dependencies."""
    content_stream = "BT\n/F1 11 Tf\n50 740 Td\n15 TL\n"
    # Title line
    escaped_title = title.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content_stream += f"/F1 14 Tf\n({escaped_title}) '\n/F1 10 Tf\n() '\n"
    for line in lines:
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content_stream += f"({escaped}) '\n"
    content_stream += "ET\n"

    stream_bytes = content_stream.encode("latin-1")
    length = len(stream_bytes)

    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    xref = []

    # Obj 1: Catalog
    xref.append(len(pdf))
    pdf.extend(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    # Obj 2: Pages
    xref.append(len(pdf))
    pdf.extend(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")

    # Obj 3: Page
    xref.append(len(pdf))
    pdf.extend(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )

    # Obj 4: Content Stream
    xref.append(len(pdf))
    pdf.extend(f"4 0 obj\n<< /Length {length} >>\nstream\n".encode("latin-1"))
    pdf.extend(stream_bytes)
    pdf.extend(b"\nendstream\nendobj\n")

    # Obj 5: Font
    xref.append(len(pdf))
    pdf.extend(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj\n")

    # Xref table
    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 6\n0000000000 65535 f \n".encode("latin-1"))
    for offset in xref:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    # Trailer
    pdf.extend(
        f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode(
            "latin-1"
        )
    )
    return bytes(pdf)


def build_decoy_thread_1() -> MIMEMultipart:
    """Decoy 1: Innocent student Sansh Vhah inquiring about OS 101 lab grades."""
    msg = MIMEMultipart()
    msg["From"] = "Sansh Vhah <sansh.v@ahduni.edu.in>"
    msg["To"] = "Prof. Hasmukh Chelaiya <hasmukh.chelaiya@ahduni.edu.in>"
    msg["Subject"] = "Re: OS 101 Assignment 2 - Evaluation Inquiry (Lab 208)"
    msg["Date"] = "Mon, 27 Oct 2026 17:15:22 +0530"
    msg["Message-ID"] = "<20261027171522.sansh.os101@ahduni.edu.in>"
    msg["X-Originating-IP"] = "[10.208.15.44]"
    msg["X-Campus-Auth-User"] = "sansh.v"

    body = (
        "Respected Prof. Chelaiya,\n\n"
        "I was reviewing my grade on Assignment 2 (Process Synchronization). TA Piyush Pelaiya\n"
        "deducted marks citing lock ordering issues. Could you please verify if the attached\n"
        "grading rubric was applied uniformly across all batches?\n\n"
        "Sincerely,\n"
        "Sansh Vhah (Roll: AU24BTECH042)\n"
        "Lab 208 Workstation\n"
    )
    msg.attach(MIMEText(body, "plain"))

    decoy_pdf = create_minimal_pdf(
        "AHMEDABAD UNIVERSITY - GICT - OS 101 GRADING RUBRIC",
        [
            "Course: OS 101 Operating Systems Principles",
            "Instructor: Prof. Hasmukh Chelaiya",
            "Batch: Autumn 2026 | Assignment 2 Rubric",
            "----------------------------------------------------------------",
            "Criterion 1: Correct Pthread Mutex Locking: 20 Marks",
            "Criterion 2: Deadlock Freedom & Banker Check: 15 Marks",
            "Criterion 3: Clean Process Termination: 15 Marks",
            "",
            "NOTICE: This is an archival grading rubric document.",
            "FLAG DECOY CHECK: case{decoy_os101_rubric_not_the_leak}",
            "----------------------------------------------------------------",
        ],
    )
    part = MIMEBase("application", "pdf")
    part.set_payload(decoy_pdf)
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition", "attachment", filename="OS101_Assignment2_Rubric_Decoy.pdf"
    )
    msg.attach(part)
    return msg


def build_decoy_thread_2() -> MIMEMultipart:
    """Decoy 2: Spoofed student complaint attempting to shift blame to Danas Moshi."""
    msg = MIMEMultipart()
    msg["From"] = "Danas Moshi <danas.m@ahduni.edu.in>"
    msg["To"] = "Academic Grievance Cell <grievance@ahduni.edu.in>"
    msg["Subject"] = "ANONYMOUS TIP: Someone accessed exam drafts in Lab 207"
    msg["Date"] = "Mon, 27 Oct 2026 21:35:10 +0530"
    msg["Message-ID"] = "<20261027213510.spoofed.tip@ahduni.edu.in>"
    msg["X-Originating-IP"] = "[10.207.99.101]"
    msg["X-Campus-Auth-User"] = "unknown_guest"

    body = (
        "To Whom It May Concern,\n\n"
        "I noticed unusual activity near the instructor console in Lab 207 around 21:00.\n"
        "A student was browsing the network share. Attached is a terminal log capture.\n\n"
        "Decoy Flag Verification: case{decoy_spoofed_student_submission_flag}\n"
    )
    msg.attach(MIMEText(body, "plain"))

    decoy_pdf = create_minimal_pdf(
        "GICT LAB 207 - ANONYMOUS INCIDENT REPORT (DECOY)",
        [
            "Timestamp: 27-Oct-2026 21:30 IST",
            "Location: Terminal 14, GICT Lab 207",
            "Observed activity: SSH session to internal repository.",
            "DECOY ARTIFACT - NOT THE LEAKED MIDSEM PAPER",
            "FLAG: case{decoy_spoofed_student_submission_flag}",
        ],
    )
    part = MIMEBase("application", "pdf")
    part.set_payload(decoy_pdf)
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition", "attachment", filename="Lab207_Incident_Decoy.pdf"
    )
    msg.attach(part)
    return msg


def build_decoy_thread_3() -> MIMEMultipart:
    """Decoy 3: Dean's office circular regarding exam preparation and security."""
    msg = MIMEMultipart()
    msg["From"] = "Dean of Academic Affairs <dean.academic@ahduni.edu.in>"
    msg["To"] = "All Faculty & TAs <cse-faculty-ta@ahduni.edu.in>"
    msg["Subject"] = "CIRCULAR: Protocol for Mid-Semester Exam Security & Confidentiality"
    msg["Date"] = "Sun, 26 Oct 2026 11:00:00 +0530"
    msg["Message-ID"] = "<20261026110000.dean.circular@ahduni.edu.in>"
    msg["X-Originating-IP"] = "[10.200.1.5]"
    msg["X-Campus-Auth-User"] = "dean.academic"

    body = (
        "Dear Faculty Colleagues and Teaching Assistants,\n\n"
        "Please strictly adhere to the academic conduct guidelines for all upcoming\n"
        "examinations, including OS 101 and OOP 99.\n\n"
        "All drafts must be stored exclusively on encrypted faculty drives.\n\n"
        "Regards,\nOffice of Academic Affairs\n"
    )
    msg.attach(MIMEText(body, "plain"))

    decoy_pdf = create_minimal_pdf(
        "OFFICE OF ACADEMIC AFFAIRS - EXAM SECURITY PROTOCOL",
        [
            "Ref: AU/ACAD/2026/OCT-MIDSEM-099",
            "Issued: 26 October 2026",
            "Target: All Course Instructors & Teaching Assistants",
            "----------------------------------------------------------------",
            "Guideline 1: No unencrypted network transfers of exam papers.",
            "Guideline 2: TAs must submit verified grading logs within 72 hours.",
            "",
            "Decoy Verification Flag: case{nice_try_blind_ai_decoy_syllabus}",
            "----------------------------------------------------------------",
        ],
    )
    part = MIMEBase("application", "pdf")
    part.set_payload(decoy_pdf)
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition", "attachment", filename="Dean_Exam_Security_Protocol.pdf"
    )
    msg.attach(part)
    return msg


def build_authentic_leaked_paper_pdf() -> bytes:
    """Generate the authentic leaked OOP 99 mid-sem exam paper with confession flag."""
    return create_minimal_pdf(
        "AHMEDABAD UNIVERSITY - GICT - DEPARTMENT OF COMPUTER SCIENCE",
        [
            "COURSE CODE: OOP 99 | OBJECT-ORIENTED PROGRAMMING SYSTEMS",
            "MID-SEMESTER EXAMINATION - AUTUMN 2026",
            "COURSE INSTRUCTOR: PROF. HASMUKH CHELAIYA",
            "TIME ALLOWED: 2 HOURS | MAXIMUM MARKS: 50",
            "================================================================================",
            "STRICTLY CONFIDENTIAL - LEAKED EVIDENCE ARTIFACT - DO NOT REPRODUCE",
            "================================================================================",
            "",
            "QUESTION 1: Dynamic Polymorphism & Virtual Table Internals (15 Marks)",
            "  (a) Contrast the memory layout of single inheritance vs virtual diamond inheritance.",
            "  (b) Given a class hierarchy with multiple virtual functions, trace vptr assignment",
            "      during object construction and demonstrate object slicing during pass-by-value.",
            "",
            "QUESTION 2: RAII, Smart Pointer Mechanics & Exception Safety (15 Marks)",
            "  (a) Implement a thread-safe reference-counting custom shared_ptr without std::shared_ptr.",
            "  (b) Demonstrate why cyclic references of std::shared_ptr cause memory leaks, and",
            "      show how std::weak_ptr resolves the ownership cycle.",
            "",
            "QUESTION 3: Thread-Safe Singleton & Concurrency Pitfalls (20 Marks)",
            "  (a) Implement Meyers' Singleton and explain thread-safety guarantees under C++11.",
            "  (b) [IRONIC QUESTION - PROF. CHELAIYA'S PET PEEVE]:",
            "      Analyze why acquiring Mutex A before Mutex B in Worker 1, and Mutex B before",
            "      Mutex A in Worker 2 leads to catastrophic Deadlock under concurrent load.",
            "      Explain how Dijkstra's lock hierarchy solves this problem permanently.",
            "",
            "================================================================================",
            "[CRIME SCENE EVIDENCE NOTE ATTACHED BY LEAKER - TA PIYUSH PELAIYA]:",
            "  Prof. Chelaiya: You docked 25 marks on my OS 101 evaluation and called my lock",
            "  hierarchy 'sloppy' in front of the lab. You said deadlock avoidance is",
            "  non-negotiable. Well, let us see your OOP 99 exam schedule avoid deadlock now!",
            "  I exfiltrated your confidential draft from your workstation share.",
            "",
            "  AUTHENTIC CONFESSION & SIGNATURE FLAG:",
            "  case{ta_piyush_angry_leaked_oop99_mail}",
            "================================================================================",
        ],
    )


def build_culprit_exfiltration_message() -> MIMEMultipart:
    """
    Build the authentic exfiltration email sent by TA Piyush Pelaiya.
    Features spoofed From header, un-spoofed authentication and IP headers,
    the full angry confession, and the base64-encoded leaked exam paper.
    """
    msg = MIMEMultipart("mixed")

    # Authentic mail gateway routing headers
    msg["Received"] = (
        "from mailgw.ahduni.edu.in (mailgw.ahduni.edu.in [172.16.0.25])\n"
        "    by campus-mail.ahduni.edu.in (Postfix) with ESMTP id 4X98bL207v\n"
        "    for <all-students-cse@ahduni.edu.in>; Mon, 27 Oct 2026 23:48:14 +0530 (IST)"
    )
    msg["Received"] = (
        "from dhcp-10-207-42-19.campus.internal (piyush-laptop.dyn.campus.internal [10.207.42.19])\n"
        "    (using TLSv1.3 with cipher TLS_AES_256_GCM_SHA384)\n"
        "    by mailgw.ahduni.edu.in (Postfix) with ESMTPSA id 3K91aB411z\n"
        "    for <all-students-cse@ahduni.edu.in>; Mon, 27 Oct 2026 23:48:12 +0530 (IST)"
    )

    # Forensic signature headers
    msg["X-Originating-IP"] = "[10.207.42.19]"
    msg["X-Campus-Auth-User"] = "piyush.pelaiya"
    msg["X-Authenticated-Sender"] = "piyush.pelaiya@ahduni.edu.in"
    msg["X-Mailer"] = "Thunderbird/115.3.1 (Linux; Ubuntu 24.04 LTS)"

    # Spoofed visual headers (what the casual recipient sees)
    msg["From"] = '"Anonymous Student Council" <student_council_leaks@protonmail.com>'
    msg["Reply-To"] = "piyush.pelaiya@ahduni.edu.in"
    msg["To"] = "all-students-cse@ahduni.edu.in"
    msg["Date"] = "Mon, 27 Oct 2026 23:48:10 +0530"
    msg["Subject"] = "[LEAK] OOP 99 Mid-Sem Question Paper Leaked!! Revenge for OS 101!"
    msg["Message-ID"] = "<20261027234810.10207.piyush@ahduni.edu.in>"

    confession_body = (
        "To all CSE students,\n\n"
        "You thought Prof. Hasmukh Chelaiya was untouchable? You thought his precious\n"
        "OOP 99 mid-semester exam was securely guarded on his ThinkPad?\n\n"
        "Earlier this semester, Prof. Chelaiya humiliated me in front of the entire department\n"
        "during OS 101 evaluations. He deducted 25 marks on my concurrency lab submission,\n"
        "claiming a theoretical lock hierarchy violation in my pthread barrier implementation.\n"
        "He laughed and said: 'Deadlock avoidance is non-negotiable in OS 101, Mr. Pelaiya.'\n\n"
        "Well, let's see how his department avoids deadlock when the entire batch has the\n"
        "confidential OOP 99 question paper before Wednesday morning!\n\n"
        "I pulled the draft directly from his workstation share during his midnight sync session.\n"
        "The complete, unredacted question paper is attached below.\n\n"
        "Signed,\n"
        "TA Piyush Pelaiya\n"
        "Graduate Teaching Assistant (Systems & Concurrency)\n"
        "GICT Lab 207\n\n"
        "Confession & Signature Flag:\n"
        "case{ta_piyush_angry_leaked_oop99_mail}\n"
    )
    msg.attach(MIMEText(confession_body, "plain", "utf-8"))

    # The authentic leaked exam attachment
    exam_pdf_bytes = build_authentic_leaked_paper_pdf()
    part = MIMEBase("application", "pdf")
    part.set_payload(exam_pdf_bytes)
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        "attachment",
        filename="OOP99_MidSem_Exam_LEAKED_CONFIDENTIAL.pdf",
    )
    part.add_header("X-Attachment-Classification", "CONFIDENTIAL-EXAM-PAPER")
    msg.attach(part)

    return msg


def generate_incident_eml(output_path: Path):
    """
    Assemble the master incident triage export containing:
    - Master incident triage header from AU-CIRT to Prof. Chelaiya
    - Decoy Thread 1: Sansh Vhah OS 101 rubric inquiry
    - Decoy Thread 2: Danas Moshi spoofed report
    - Decoy Thread 3: Dean's office security circular
    - True Evidence: TA Piyush Pelaiya's authenticated exfiltration email with leaked exam PDF
    """
    master_msg = MIMEMultipart("mixed")
    master_msg["From"] = "Campus Security Operations <soc@ahduni.edu.in>"
    master_msg["To"] = "Prof. Hasmukh Chelaiya <hasmukh.chelaiya@ahduni.edu.in>"
    master_msg["Cc"] = "Dean of Academic Affairs <dean.academic@ahduni.edu.in>"
    master_msg["Date"] = "Tue, 28 Oct 2026 01:15:30 +0530"
    master_msg["Subject"] = (
        "FW: [INCIDENT TICKET #7042] Re: URGENT: Leak Investigation - Unofficial "
        "Circulation of OOP 99 Exam Paper"
    )
    master_msg["Message-ID"] = "<20261028011530.soc.cirt.7042@ahduni.edu.in>"
    master_msg["X-Incident-Ticket"] = "INCIDENT-2026-7042-MIDSEM-LEAK"
    master_msg["X-Priority"] = "1 (Highest)"

    briefing = (
        "Dear Prof. Chelaiya,\n\n"
        "At 00:15 IST, our campus mail filter gateway (mailgw.ahduni.edu.in) triggered an\n"
        "automated alert on a high-volume outbound mail blast targeting the student body.\n\n"
        "The intercepted export collates multiple threads captured between 17:00 and 23:50 IST\n"
        "on 27 October 2026. The exfiltration message utilized spoofed external 'From' headers\n"
        "claiming to be an 'Anonymous Student Council'. However, internal gateway authentication\n"
        "records and X-Originating-IP traces point to a workstation inside GICT Lab 207.\n\n"
        "Please review the attached thread components, analyze the RFC 822 routing headers,\n"
        "and verify the authenticity of the attached OOP 99 draft paper.\n\n"
        "Forensic Evidence Attached:\n"
        "  1. Decoy Thread #1: sansh_vhah_os101_rubric.eml (Student grade inquiry)\n"
        "  2. Decoy Thread #2: anonymous_lab207_tip.eml (Spoofed blame redirect)\n"
        "  3. Decoy Thread #3: dean_security_circular.eml (Archival administrative memo)\n"
        "  4. Evidence Item #4: intercepted_exfiltration_blast.eml (Authentic exfiltration blast)\n\n"
        "- Ahmedabad University Cyber Incident Response Team (AU-CIRT)\n"
        "GICT Security Operations Center\n"
    )
    master_msg.attach(MIMEText(briefing, "plain", "utf-8"))

    # Attach Decoys as message/rfc822 sub-messages
    msg_decoy1 = MIMEMessage(build_decoy_thread_1())
    msg_decoy1.add_header(
        "Content-Disposition", "attachment", filename="sansh_vhah_os101_rubric.eml"
    )
    master_msg.attach(msg_decoy1)

    msg_decoy2 = MIMEMessage(build_decoy_thread_2())
    msg_decoy2.add_header(
        "Content-Disposition", "attachment", filename="anonymous_lab207_tip.eml"
    )
    master_msg.attach(msg_decoy2)

    msg_decoy3 = MIMEMessage(build_decoy_thread_3())
    msg_decoy3.add_header(
        "Content-Disposition", "attachment", filename="dean_security_circular.eml"
    )
    master_msg.attach(msg_decoy3)

    # Attach Authentic Culprit Exfiltration Message
    msg_culprit = MIMEMessage(build_culprit_exfiltration_message())
    msg_culprit.add_header(
        "Content-Disposition",
        "attachment",
        filename="intercepted_exfiltration_blast.eml",
    )
    master_msg.attach(msg_culprit)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(master_msg.as_bytes())


def main():
    repo_root = Path(__file__).resolve().parent
    out_file = repo_root / "files" / "leaked_incident_mail.eml"
    print(f"[*] Building challenge artifact: {out_file}")
    generate_incident_eml(out_file)
    print(f"[+] Successfully generated: {out_file} ({out_file.stat().st_size} bytes)")
    print("[+] Verified true flag: case{ta_piyush_angry_leaked_oop99_mail}")
    print("[+] Decoy honeyflags embedded: 3")


if __name__ == "__main__":
    main()
