# Liam's Idea: Fragmented Exfiltration

**Track:** Forensics & Stego  
**Difficulty:** Easy — 300 → 100 pts (decay 20 solves)  
**Author:** Yesha (Forensics Track Lead)  
**Flag:** `case{reconstructed_exfil_chunk_assembly}`

---

## 1. Challenge Overview & Canon Storyline
At 02:13:42 IST on 28 October 2026, teaching assistant Piyush Pelaiya accessed Lab 207 Workstation PC-04 to finalize the theft of Prof. ManMishra Chelaiya's OOP 99 mid-sem examination draft. To preserve proof of his revenge against Prof. Chelaiya's grading in OS 101, Piyush recorded a short CCTV/terminal feed showing the exam access.

When uploading the recording to an external relay, the campus firewall Data Loss Prevention (DLP) system triggered an alert on large outbound Base64 streams. To circumvent the filter, Piyush split the payload into 12 non-standard text chunks (`part01.txt` ... `part12.txt`) preceded by firewall comment headers.

---

## 2. Anti-AI Defensive Principle
- **Fragmented Multi-File Context Confusion:** Feeding an individual chunk into a web LLM yields a decoding error because each piece contains a fragment of the Base64 stream without standard 4-byte padding alignment.
- **Comment Stripping Requirement:** The files include multi-line `#` comment headers that must be parsed or filtered out. An automated shell pipeline or custom script is required to reassemble the data in exact sequence.

---

## 3. Step-by-Step Solution Walkthrough

### Method A: One-Liner Bash Pipeline
In any Unix/Linux or macOS terminal:
```bash
cd files/
grep -v '^#' part*.txt | tr -d '\r\n ' | base64 -d > exfil_video.mp4
```
Then open the video in any media player (`vlc exfil_video.mp4` or `mpv exfil_video.mp4`) or extract metadata:
```bash
strings exfil_video.mp4 | grep "case{"
```
Output:
```text
case{reconstructed_exfil_chunk_assembly}
```

### Method B: Automated Python Solver
Run the repository solver:
```bash
uv run python challenges/fragmented_exfiltration/solve.py
```
Output:
```text
[*] Reassembling fragmented exfiltration chunks from files/...
[+] Found 12 chunk files to assemble.
[+] Concatenated clean Base64 stream (94792 chars)
[+] Successfully decoded binary video container (71093 bytes)
[+] SUCCESS: Extracted flag: case{reconstructed_exfil_chunk_assembly}
```

---

## 4. Verification Protocol
1. [x] 12 chunk files (`part01.txt` through `part12.txt`) present in `files/`.
2. [x] Generator (`generate.py`) generates clean, reproducible MP4 artifacts and fragments.
3. [x] Solver (`solve.py`) successfully reconstructs and verifies the flag.
4. [x] Challenge configuration (`challenge.yml`) is valid.
