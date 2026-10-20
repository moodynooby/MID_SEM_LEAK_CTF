# Docket #104: The Exam Exfiltration Payload

- **Category:** Reverse Engineering (Medium/Hard)
- **Flag:** `case{payload_deobfuscated_target_ip_identified}`
- **Story Arc:** Act IV — Recovering the malicious exfiltration script.

## Concept & Solution
1. The script contains layers of base64 decoding and zlib decompression terminated with `eval()`.
2. Teams can safely analyze the code by replacing the final `eval(decoded_payload)` with `print(decoded_payload)` inside a sandbox.
3. The printed payload reveals the socket connection string and embedded verification flag.
