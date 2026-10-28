# Ransomware Infected: Backdoor Web Shell in PCAP
## Challenge Writeup & Author Rationale

- **Author:** Vatsal Pandya (`@VP1107`)
- **Track:** Network & Forensics (Issue #5 / Challenge #2)
- **Category:** Network
- **Estimated Difficulty:** Medium — 500 → 200 pts (decay 16 solves)  
- **Tester / Solve-Verified By:** Krish Poddar (`@Krish-452`) / Manas Doshi (`@moodynooby`)
- **True Flag:** `case{pcap_webshell_exfil_key_found}`
- **Decoy Honeyflags:**
  - `case{student_sansh_portal_session_cookie}`
  - `case{au_campus_syslog_telemetry_token}`

---

## 1. Challenge Concept & Lore

In *Case File: The Mid-Sem Leak*, forensic triaging of the faculty subnet (`10.20.0.12`) identified an unmonitored backdoor webshell planted at `/assets/vendor.php`. 

Network packet captures (`infected.pcap`) revealed that **TA Piyush Pelaiya** (`10.207.42.19`) used this webshell to execute remote exfiltration commands against the confidential examination storage. To evade basic Network Intrusion Detection Systems (NIDS) and string analysis, the webshell communication protocol XOR-encrypts commands and responses using an ephemeral session key supplied in the HTTP request header `X-Session-Key`.

---

## 2. Anti-AI Defensive Architecture

1. **Custom XOR Obfuscated Stream:**
   The exfiltrated content is transmitted in hex-encoded form encrypted with key `midsem_leaked_key_99`. A naive `strings infected.pcap` or generic AI prompt pasting the raw PCAP text will fail to locate the true flag.

2. **Decoy Honeyflags in Plaintext Traffic:**
   Background legitimate and telemetry streams contain plaintext decoys:
   - `case{student_sansh_portal_session_cookie}` in a login request to `/auth/login.php`
   - `case{au_campus_syslog_telemetry_token}` in `/api/telemetry`
   Automated AI regex scrapers that extract the first `case{...}` match will trap the honeyflag.

3. **Multi-Step Protocol Reversal:**
   The solver must isolate the specific webshell exchange, parse custom HTTP headers, extract the XOR key, and write a decryption routine.

---

## 3. Walkthrough & Official Solution

### Step 1: Open PCAP in Wireshark & Filter for HTTP POST
In Wireshark or `tshark`, filter for HTTP POST requests:
```wireshark
http.request.method == "POST"
```

Observe three distinct POST streams:
1. `POST /auth/login.php` (Decoy student authentication)
2. `POST /api/telemetry` (Decoy telemetry payload)
3. `POST /assets/vendor.php` (Suspicious interaction with PHP backdoor)

### Step 2: Inspect Headers of `/assets/vendor.php` Request
Follow the TCP Stream for the conversation with `/assets/vendor.php`:
```http
POST /assets/vendor.php HTTP/1.1
Host: faculty.ahduni.internal
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0
Content-Type: application/x-www-form-urlencoded
X-Session-Key: midsem_leaked_key_99
X-Requested-With: XMLHttpRequest
Content-Length: 131

data=2a222328...
```
Identify the custom header:
`X-Session-Key: midsem_leaked_key_99`

### Step 3: Decrypt the Server Response Payload
The server response body contains hex-encoded XOR ciphertext:
```http
HTTP/1.1 200 OK
Date: Tue, 28 Oct 2026 02:45:12 GMT
Server: Apache/2.4.52 (Ubuntu)
Content-Type: text/plain; charset=UTF-8
Content-Length: 346

263b3531393f...
```

Decrypt using Python:
```python
def xor_crypt(data, key):
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

key = b"midsem_leaked_key_99"
hex_payload = "..." # Hex string from response body
ciphertext = bytes.fromhex(hex_payload)
print(xor_crypt(ciphertext, key).decode())
```

Output:
```text
EXFILTRATION_SUCCESS
TARGET: OOP99_MidSem_FinalDraft.pdf (SHA256: 8f9b42...)
CONFIRMATION_KEY: case{pcap_webshell_exfil_key_found}
STAGING_BUFFER: /tmp/.piyush_exfil_vault/
```

The flag is:
`case{pcap_webshell_exfil_key_found}`

---

## 4. Hints & Cost Strategy

- **Hint 1 (-50 pts):** "Inspect custom HTTP headers in the repeated POST requests to /assets/vendor.php. Look for custom session authentication tokens."

---

## 5. Solve-Test Verification Log

- **Date Tested:** 26/10/2026
- **Automated Verification:** `uv run python challenges/ransomware_pcap/solve.py` $\rightarrow$ Exit code 0.
- **Estimated Human Solve Time:** 10–15 minutes.
- **Verification Summary:**
  - Raw PCAP parsing isolates webshell stream without third-party dependencies.
  - Plaintext honeyflags trapped and bypassed.
  - XOR decryption validates target flag `case{pcap_webshell_exfil_key_found}`.
