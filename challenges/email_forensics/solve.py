#!/usr/bin/env python3
"""
solve.py — Automated Forensic Solver for 'Email Forensics: The Angry TA's Leaked Mails'
Track: Network & Forensics | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Vatsal Pandya (@VP1107)

Solve Path:
    1. Parse RFC 822 / MIME structure of 'files/leaked_incident_mail.eml'.
    2. Recurse through attached message/rfc822 sub-threads.
    3. Filter out decoy student communications and administrative memos.
    4. Detect spoofed From header ("Anonymous Student Council") vs authentic internal
       gateway routing headers:
       - X-Campus-Auth-User: piyush.pelaiya
       - X-Originating-IP: [10.207.42.19]
    5. Extract the base64-encoded PDF attachment:
       'OOP99_MidSem_Exam_LEAKED_CONFIDENTIAL.pdf'.
    6. Extract and verify the true flag:
       case{ta_piyush_angry_leaked_oop99_mail}
"""

import sys
import re
import email
from email import policy
from pathlib import Path

TARGET_FLAG = "case{ta_piyush_angry_leaked_oop99_mail}"
KNOWN_DECOYS = {
    "case{os101_assignment2_grading_rubric_official}",
    "case{student_sansh_lab_extension_request_auth}",
    "case{dean_academic_integrity_protocol_2026}",
}


def analyze_eml_file(eml_path: Path):
    if not eml_path.exists():
        print(f"[-] Error: Target artifact not found at {eml_path}")
        sys.exit(1)

    print(f"[*] Loading incident artifact: {eml_path}")
    with open(eml_path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    print(f"[*] Top-level Subject: {msg['Subject']}")
    print(f"[*] Top-level From:    {msg['From']}")
    print(f"[*] MIME Structure inspection commencing...\n")

    all_messages = []

    def walk_messages(current_msg, depth=0):
        all_messages.append((depth, current_msg))
        for part in current_msg.iter_parts():
            if part.get_content_type() == "message/rfc822":
                payload = part.get_payload()
                if isinstance(payload, list):
                    for sub in payload:
                        walk_messages(sub, depth + 1)
                elif hasattr(payload, "iter_parts"):
                    walk_messages(payload, depth + 1)

    walk_messages(msg)
    print(f"[+] Total distinct email entities discovered in spool: {len(all_messages)}")

    genuine_message = None
    extracted_attachments = []

    for depth, m in all_messages:
        subj = m.get("Subject", "<No Subject>")
        sender = m.get("From", "<No Sender>")
        auth_user = m.get("X-Campus-Auth-User", "None")
        orig_ip = m.get("X-Originating-IP", "None")
        print(f"  [Level {depth}] Subject: {subj[:55]}")
        print(f"           From: {sender} | AuthUser: {auth_user} | IP: {orig_ip}")

        # Check for the authenticated TA Piyush Pelaiya indicators
        if auth_user == "piyush.pelaiya" or "10.207.42.19" in str(orig_ip):
            print(f"    ==> [!] MATCH: Genuine exfiltration message isolated! (Piyush Pelaiya / 10.207.42.19)")
            genuine_message = m

        # Inspect all attachments across all messages to monitor decoys vs authentic target
        for part in m.iter_parts():
            cd = part.get("Content-Disposition", "")
            fn = part.get_filename()
            if fn:
                content = part.get_payload(decode=True)
                if content:
                    extracted_attachments.append((fn, content, auth_user, orig_ip))

    if not genuine_message:
        print("[-] Forensic triage failed: Authentic exfiltration message not isolated.")
        sys.exit(1)

    # Search for flag in genuine message body
    confession_flag = None
    for part in genuine_message.walk():
        if part.get_content_type() == "text/plain":
            body = part.get_payload(decode=True).decode("utf-8", errors="replace")
            matches = re.findall(r"case\{[^}]+\}", body)
            for m in matches:
                if m == TARGET_FLAG:
                    confession_flag = m
                elif m in KNOWN_DECOYS:
                    print(f"    [-] Caught decoy in message body: {m}")

    # Inspect the exfiltrated exam paper attachment
    print(f"\n[*] Inspecting attachments extracted ({len(extracted_attachments)} files):")
    target_attachment_flag = None
    for fn, data, auth_user, ip in extracted_attachments:
        is_pdf = data.startswith(b"%PDF")
        print(f"  - File: {fn} ({len(data)} bytes, Valid PDF: {is_pdf}, Origin: {auth_user}@{ip})")
        # Extract text strings from PDF payload
        text = data.decode("latin-1", errors="replace")
        flags = re.findall(r"case\{[^}]+\}", text)
        for fl in flags:
            if fl in KNOWN_DECOYS:
                print(f"    [!] Detected decoy honeyflag: {fl} in {fn}")
            elif fl == TARGET_FLAG:
                print(f"    [+] TARGET EXAM PAPER FLAG LOCATED: {fl} in {fn}")
                target_attachment_flag = fl

    print("\n" + "=" * 60)
    print("FORENSIC SOLVER VERIFICATION RESULTS:")
    print(f"  Target Flag:                 {TARGET_FLAG}")
    print(f"  Confession Body Flag:        {confession_flag}")
    print(f"  Exam Paper Attachment Flag:  {target_attachment_flag}")
    print("=" * 60)

    if target_attachment_flag == TARGET_FLAG and confession_flag == TARGET_FLAG:
        print("[+] SUCCESS: Challenge verified cleanly! Extracted flag matches expected.")
        sys.exit(0)
    else:
        print("[-] FAILURE: Flag verification failed.")
        sys.exit(1)


def main():
    repo_root = Path(__file__).resolve().parent
    eml_file = repo_root / "files" / "leaked_incident_mail.eml"
    analyze_eml_file(eml_file)


if __name__ == "__main__":
    main()
