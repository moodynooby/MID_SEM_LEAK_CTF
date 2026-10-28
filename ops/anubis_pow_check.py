#!/usr/bin/env python3
"""End-to-end Anubis Proof-of-Work check over the plain-HTTP LAN stack.

Reproduces exactly what a participant browser does, so an "Anubis loop" can be
told apart from a network/proxy problem:

  1. GET  /                      -> challenge page + verification cookie
  2. read the embedded `anubis_challenge` JSON (id, randomData, difficulty)
  3. brute-force a nonce where sha256(randomData + nonce) has N leading zeros
  4. GET  /.within.website/x/cmd/anubis/api/pass-challenge -> auth cookie
  5. GET  /                      -> real CTFd HTML (no challenge page)

Usage:
    python3 ops/anubis_pow_check.py http://10.20.15.43
    python3 ops/anubis_pow_check.py http://localhost

Exit code 0 = PASS, 1 = FAIL (with the reason printed).

Regression it guards against: Anubis v1.28+ defaults to COOKIE_SECURE=true and
COOKIE_PARTITIONED=true. Over http:// (port 80) browsers silently discard
`Secure` cookies (and `Partitioned`, which requires Secure), so the verification
cookie never comes back and every request loops on "user has cookies disabled".
Only http://localhost survived, because localhost is a trusted/secure origin.
[docker-compose.yml](../docker-compose.yml) therefore sets
COOKIE_SECURE=false and COOKIE_PARTITIONED=false for the ctfd_anubis service.
"""
from __future__ import annotations

import hashlib
import http.cookiejar
import json
import re
import sys
import urllib.parse
import urllib.request

API = "/.within.website/x/cmd/anubis/api"
TIMEOUT = 30


def main(base: str) -> int:
    base = base.rstrip("/")
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = [
        (
            "User-Agent",
            "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        )
    ]

    page = opener.open(base + "/", timeout=TIMEOUT).read().decode("utf-8", "replace")
    match = re.search(
        r'id="anubis_challenge" type="application/json">(.*?)</script>', page, re.S
    )
    if not match:
        print(f"[!] no challenge page served by {base}/ (proxy bypassing Anubis?)")
        print(page[:300])
        return 1

    payload = json.loads(match.group(1))
    difficulty = payload["rules"]["difficulty"]
    challenge_id = payload["challenge"]["id"]
    random_data = payload["challenge"]["randomData"]
    issued = [c.name for c in jar]
    print(f"[+] challenge page served | difficulty={difficulty} | cookies={issued}")

    nonce = 0
    while True:
        digest = hashlib.sha256((random_data + str(nonce)).encode()).hexdigest()
        if digest.startswith("0" * difficulty):
            break
        nonce += 1
    print(f"[+] solved nonce={nonce} hash={digest}")

    query = urllib.parse.urlencode(
        {
            "id": challenge_id,
            "response": digest,
            "nonce": nonce,
            "redir": "/",
            "elapsedTime": 1500,
        }
    )
    resp = opener.open(f"{base}{API}/pass-challenge?{query}", timeout=TIMEOUT)
    resp.read()
    names = [c.name for c in jar]
    print(f"[+] pass-challenge status={resp.status} cookies={names}")

    if not any(name.endswith("-auth") or "-auth-" in name for name in names):
        print("[!] FAIL: no Anubis auth cookie was issued")
        print("    -> verification cookie was rejected by the client (Secure/Partitioned over http?)")
        return 1

    after = opener.open(base + "/", timeout=TIMEOUT).read().decode("utf-8", "replace")
    if 'id="anubis_challenge"' in after:
        print("[!] FAIL: still served the challenge page after authentication")
        return 1

    print(f"[+] CTFd content served after auth ({len(after)} bytes)")
    print("[+] RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "http://localhost"))
