#!/usr/bin/env python3
"""
solve.py — Automated Solver for 'Audio Spectrogram: Lab Microphone Wiretap'
Track: Forensics & Stego | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Yesha (Forensics Track Lead)

Walkthrough Solution:
    1. The participant receives `lab207_ambient_wiretap.wav`.
    2. Playing the file produces audible ambient 50Hz electrical hum, HVAC ventilation,
       and occasional keyboard click noise.
    3. Loading the file into Audacity or Sonic Visualiser:
       - Audacity: Click track dropdown -> 'Spectrogram'.
       - Open Spectrogram Settings: Set Min Frequency to 15000 Hz, Max Frequency to 20000 Hz.
       - The flag visually resolves in the high-frequency spectrum:
         `case{spectrogram_lab207_wiretap_audio}`
    4. Programmatic solution:
       - This solver uses the Goertzel algorithm across the 7 synthesized frequency rows
         (16.0 kHz - 19.0 kHz) to reconstruct the bitmap columns and decode the glyphs.
"""

import math
import wave
import struct
import sys
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent
WAV_PATH = CHALLENGE_DIR / "files" / "lab207_ambient_wiretap.wav"
EXPECTED_FLAG = "case{spectrogram_lab207_wiretap_audio}"

# Import generator constants for matching
sys.path.insert(0, str(CHALLENGE_DIR))
try:
    from generate import GLYPHS, NUM_ROWS, FREQ_MIN, FREQ_STEP, COL_DURATION
except ImportError:
    print("[-] Error: Unable to import constants from generate.py")
    sys.exit(1)


def goertzel(chunk, target_freq, sample_rate):
    """Computes Goertzel magnitude for a specific target frequency."""
    N = len(chunk)
    k = int(0.5 + (N * target_freq / sample_rate))
    omega = (2.0 * math.pi * k) / N
    coeff = 2.0 * math.cos(omega)
    q0 = q1 = q2 = 0.0
    for s in chunk:
        q0 = coeff * q1 - q2 + s
        q2 = q1
        q1 = q0
    return math.sqrt(q1 * q1 + q2 * q2 - q1 * q2 * coeff)


def solve():
    print(f"[*] Solving Audio Spectrogram challenge from: {WAV_PATH}")
    if not WAV_PATH.exists():
        print(f"[-] Error: File not found: {WAV_PATH}")
        return False

    with wave.open(str(WAV_PATH), "rb") as wf:
        sr = wf.getframerate()
        nframes = wf.getnframes()
        raw = wf.readframes(nframes)
        samples = struct.unpack(f"<{nframes}h", raw)

    print(f"[+] Loaded {nframes} samples ({nframes / sr:.2f} seconds) at {sr} Hz.")

    col_samples = int(sr * COL_DURATION)
    row_freqs = [FREQ_MIN + (NUM_ROWS - 1 - r) * FREQ_STEP for r in range(NUM_ROWS)]
    lead_in = int(sr * 1.5)

    # Reconstruct binary column matrix
    detected_cols = []
    total_cols = (nframes - lead_in - int(sr * 1.5)) // col_samples

    for c in range(total_cols):
        start = lead_in + c * col_samples
        chunk = samples[start : start + col_samples]
        col_bits = []
        for f in row_freqs:
            mag = goertzel(chunk, f, sr)
            col_bits.append("1" if mag > 400000.0 else "0")
        detected_cols.append("".join(col_bits))

    # Reverse lookup map: 5-column tuple -> character
    glyph_col_map = {}
    for ch, rows in GLYPHS.items():
        cols = []
        for c_idx in range(5):
            cols.append("".join(rows[r_idx][c_idx] for r_idx in range(NUM_ROWS)))
        glyph_col_map[ch] = tuple(cols)

    # Decode characters
    idx = 8  # Skip initial padding
    decoded_chars = []
    while idx + 5 <= len(detected_cols):
        cand_cols = tuple(detected_cols[idx : idx + 5])
        match = None
        for ch, cols in glyph_col_map.items():
            if cols == cand_cols:
                match = ch
                break
        if match:
            decoded_chars.append(match)
            idx += 6  # 5 character columns + 1 separator column
        else:
            if all(c == "0000000" for c in cand_cols):
                break
            idx += 1

    recovered_flag = "".join(decoded_chars).strip()
    print(f"[+] Recovered spectrogram flag string: '{recovered_flag}'")

    if recovered_flag == EXPECTED_FLAG:
        print(f"[SUCCESS] Validated Flag: {recovered_flag}")
        return True
    else:
        print(f"[-] Flag mismatch. Expected '{EXPECTED_FLAG}', got '{recovered_flag}'")
        return False


if __name__ == "__main__":
    success = solve()
    sys.exit(0 if success else 1)
