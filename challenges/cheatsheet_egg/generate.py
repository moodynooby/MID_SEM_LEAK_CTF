#!/usr/bin/env python3
"""
generate.py — Artifact Generator for 'Flag in Cheatsheet: Participant Kit Easter Egg'
Track: Network & Forensics | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Vatsal Pandya (@VP1107)

Generates:
    challenges/cheatsheet_egg/files/CTF_101_CheatSheet.md
    Synchronizes with docs/participant_kit/CTF_101_CheatSheet.md

Anti-AI Defensive Layer:
    - Concealed inside HTML comment streams and invisible zero-width annotations.
    - Decoy comments containing false leads:
      <!-- TODO(ta_piyush): remove testing flag case{decoy_superficial_html_comment} -->

True Flag:
    case{always_read_the_cheat_sheet_first}
"""

import shutil
from pathlib import Path

TARGET_FLAG = "case{always_read_the_cheat_sheet_first}"
DECOY_FLAG = "case{decoy_superficial_html_comment}"


def build_cheatsheet(output_path: Path, master_docs_path: Path):
    content = f"""# 🕵️ CTF 101 Cheat Sheet: Investigator's Toolkit
## Case File: The Mid-Sem Leak — IEEE AUSB

Welcome to your first digital forensics case! Keep this cheat sheet handy during the competition.

<!-- TODO(ta_piyush): remove testing flag {DECOY_FLAG} -->

---

### 1. Essential Linux Terminal Commands
```bash
# Search for printable strings inside unknown or binary files
strings evidence.bin | grep -i "case{{"
strings -n 8 mystery_file.raw

# Identify the true MIME/file type regardless of file extension
file artifact.bin

# Inspect hexadecimal bytes of a file
hexdump -C -n 128 suspicious.png
xxd evidence.raw | head -n 20

# Grep through log files for patterns or error codes
grep -i "admin" access.log
grep " 404 " access.log | awk '{{print $1, $7}}' | sort | uniq -c
```

---

### 2. Digital Forensics Quick Reference

| Task | Recommended Tool | Command / Action |
| :--- | :--- | :--- |
| **Check file metadata** | `exiftool` | `exiftool image.png` (check comments, dates, camera tags) |
| **Extract hidden files** | `binwalk` | `binwalk -e suspicious.pdf` |
| **Inspect Steganography** | `zsteg` / StegOnline | Look for hidden payloads across RGB LSB channels |
| **Analyze PCAP Network Logs** | `Wireshark` / `tshark` | Filters: `http`, `tcp.port == 80`, `ip.addr == 10.207.x.x` |

#### Common Magic Bytes (File Headers)
If a file won't open, its first bytes might be corrupted:
- **PNG:** `89 50 4E 47 0D 0A 1A 0A`
- **JPEG:** `FF D8 FF E0` or `FF D8 FF E1`
- **PDF:** `25 50 44 46` (`%PDF`)
- **ZIP / DOCX:** `50 4B 03 04` (`PK..`)

---

### 3. Cryptography & Encoding

| Format | Example | How to Decode |
| :--- | :--- | :--- |
| **Base64** | `Y2FzZXtsZWFrfQ==` | Terminal: `echo "..." | base64 -d` |
| **Hexadecimal** | `636173657b` | Terminal: `echo "..." | xxd -r -p` |
| **ROT13 / Caesar** | `pnfr{{...}}` | Shift letters by 13 positions (CyberChef) |
| **Vigenère** | Polyalphabetic cipher | Use a key phrase (e.g., room number or suspect handle) |
| **URL Encoding** | `%27%20OR%201%3D1` | CyberChef: URL Decode |

> **Pro Tip:** Bookmark **CyberChef** (`gchq.github.io/CyberChef`). It handles 90% of CTF decryption and decoding with simple drag-and-drop operations!

---

### 4. Web Inspection & Bug Spotting
- **Inspect Element (`F12` or `Ctrl+Shift+I`):**
  - Check HTML comments (`<!-- TODO: remove debug flag -->`).
  - Check the **Network Tab** for response headers (`X-Flag`, `Set-Cookie`).
  - Check **Storage / Application Tab** for cookies and local storage tokens.
- **Common SQL Injection Bypass:**
  - `' OR 1=1 --`
  - `admin' --`

---

### 5. Submitting Your Flags
- Every flag follows the format: **`case{{flag_text_here}}`**
- Flags are case-sensitive. Submit directly into the CTFd dashboard!

<!-- ================================================================= -->
<!-- IEEE AUSB CTF 2026 OFFICIAL CHEATSHEET EASTER EGG                 -->
<!-- The observant investigator reads the manual before touching tools. -->
<!-- REWARD FLAG: {TARGET_FLAG}           -->
<!-- ================================================================= -->
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

    if master_docs_path.exists():
        master_docs_path.write_text(content, encoding="utf-8")


def main():
    repo_root = Path(__file__).resolve().parent
    out_file = repo_root / "files" / "CTF_101_CheatSheet.md"
    master_file = repo_root.parent.parent / "docs" / "participant_kit" / "CTF_101_CheatSheet.md"

    print(f"[*] Generating cheatsheet easter egg: {out_file}")
    build_cheatsheet(out_file, master_file)
    print(f"[+] Successfully generated: {out_file}")
    print(f"[+] Synchronized with participant kit: {master_file}")
    print(f"[+] True Flag: {TARGET_FLAG}")


if __name__ == "__main__":
    main()
