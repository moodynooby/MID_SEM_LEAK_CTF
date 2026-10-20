# Docket #101: The Corrupted Snapshot

- **Category:** Forensics (Easy)
- **Flag:** `case{cctv_frame_corrupted_header_restored}`
- **Story Arc:** Act I — The initial discovery in Lab 207.

## Concept & Solution
The intruder corrupted the first 8 bytes of the PNG file (changing `89 50 4E 47 0D 0A 1A 0A` to zeros or bogus characters).
1. Open the file in CyberChef or a hex editor.
2. Restore the PNG magic bytes (`89 50 4E 47 0D 0A 1A 0A`).
3. View the image or run `zsteg` / `strings` to retrieve the flag printed across the timestamp overlay.
