#!/usr/bin/env python3
"""
generate.py — Artifact Generator for "Liam's Idea: Fragmented Exfiltration"
Track: Forensics & Stego | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Yesha (Forensics Track Lead)

Generates:
    challenges/fragmented_exfiltration/files/part01.txt ... part12.txt

Storyline Context:
    At 02:13:42 IST, TA Piyush exfiltrated CCTV footage and terminal captures
    confirming the theft of Prof. Hasmukh Chelaiya's OOP 99 mid-sem exam paper.
    To bypass GICT's campus Data Loss Prevention (DLP) packet size inspectors,
    he fragmented the Base64 stream across 12 irregular chunks (part01.txt ... part12.txt).

Anti-AI Defensive Layer:
    - Multi-file irregular boundary chunking: feeding individual chunks to an LLM
      results in truncation errors and invalid Base64 padding.
    - Custom firewall header banners that require automated or shell concatenation
      filtering (e.g. `grep -v '^#' part*.txt | tr -d '\r\n ' | base64 -d > exfil.mp4`).

Flag:
    case{reconstructed_exfil_chunk_assembly}
"""

import os
import sys
import base64
import tempfile
import subprocess
from pathlib import Path

FLAG = "case{reconstructed_exfil_chunk_assembly}"
NUM_PARTS = 12

CHALLENGE_DIR = Path(__file__).resolve().parent
FILES_DIR = CHALLENGE_DIR / "files"


def generate_video(output_mp4_path: Path):
    """Generates a compact CCTV terminal MP4 video embedding the flag."""
    text_content = (
        "=========================================\n"
        " GICT LAB 207 - CCTV FOOTAGE [CAM 04]  \n"
        " TIMESTAMP: 2026-10-28 02:13:42 IST     \n"
        " SUSPECT WORKSTATION: PC-04 [TA PIYUSH] \n"
        " INCIDENT: EXFILTRATION OF OOP 99 EXAM  \n"
        " STATUS: DATA LOSS PREVENTION (DLP) LEAK\n"
        "=========================================\n"
        f"\n  FLAG: {FLAG}\n\n"
        "========================================="
    )

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
        tf.write(text_content)
        tpath = tf.name

    try:
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=#081014:s=640x360:d=3:r=10",
            "-vf", (
                f"drawtext=textfile={tpath}:"
                "x=(w-text_w)/2:y=(h-text_h)/2:"
                "fontsize=18:fontcolor=#00ff88:line_spacing=6"
            ),
            "-metadata", f"comment={FLAG}",
            "-metadata", f"title=GICT_LAB207_CCTV_CAM04_EXFIL_{FLAG}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            str(output_mp4_path)
        ]
        subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True)
    except Exception as e:
        print(f"[-] ffmpeg execution failed: {e}. Falling back to embedded minimal MP4 payload.")
        generate_fallback_mp4(output_mp4_path)
    finally:
        if os.path.exists(tpath):
            os.remove(tpath)


def generate_fallback_mp4(output_mp4_path: Path):
    """Fallback valid MP4 container containing the exfiltration flag."""
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "testsrc=duration=2:size=320x240:rate=10",
        "-metadata", f"comment={FLAG}",
        "-metadata", f"title=GICT_LAB207_EXFIL_{FLAG}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        str(output_mp4_path)
    ]
    try:
        subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True)
    except Exception:
        # Raw binary MP4 container with ftyp box and flag embedded
        # Standard ISO Base Media File Format (MP4)
        ftyp = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom"
        mdat_data = f"GICT_INCIDENT_CCTV_PC04_TIMESTAMP_02:13:42_{FLAG}_OOP99".encode("utf-8")
        mdat = len(mdat_data + b"\x00\x00\x00\x00").to_bytes(4, "big") + b"mdat" + mdat_data
        output_mp4_path.write_bytes(ftyp + mdat)


def main():
    print(f"[*] Generating 'Liam\\'s Idea: Fragmented Exfiltration' challenge artifacts...")
    FILES_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_mp4 = Path(tmpdir) / "evidence_exfil.mp4"
        generate_video(temp_mp4)

        if not temp_mp4.exists() or temp_mp4.stat().st_size == 0:
            generate_fallback_mp4(temp_mp4)

        video_bytes = temp_mp4.read_bytes()
        print(f"[+] Master exfiltration video created ({len(video_bytes)} bytes)")

        # Encode to Base64
        b64_data = base64.b64encode(video_bytes).decode("ascii")

    # Split b64 string across 12 parts
    chunk_size = (len(b64_data) + NUM_PARTS - 1) // NUM_PARTS

    for i in range(NUM_PARTS):
        part_num = i + 1
        part_filename = f"part{part_num:02d}.txt"
        part_path = FILES_DIR / part_filename

        chunk = b64_data[i * chunk_size : (i + 1) * chunk_size]

        header = (
            f"# ====================================================================\n"
            f"# GICT CAMPUS SECURITY — INTERCEPTED DLP EXFILTRATION STREAM\n"
            f"# INCIDENT ID: 2026-10-28-OOP99-LEAK | FRAGMENT: {part_num:02d}/{NUM_PARTS:02d}\n"
            f"# SOURCE: 10.207.42.19 (Lab 207 PC-04) -> WAN GATEWAY\n"
            f"# NOTICE: Payload chunks must be assembled sequentially and cleaned.\n"
            f"# ====================================================================\n"
        )

        # Wrap chunk every 76 characters for realistic MIME/Base64 look
        wrapped_chunk = "\n".join(chunk[j : j + 76] for j in range(0, len(chunk), 76))
        content = header + wrapped_chunk + "\n"

        part_path.write_text(content, encoding="utf-8")
        print(f"  -> Generated {part_filename} ({len(content)} bytes)")

    print(f"[+] Successfully generated all {NUM_PARTS} fragmented chunks in {FILES_DIR}")


if __name__ == "__main__":
    main()
