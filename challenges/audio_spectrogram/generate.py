#!/usr/bin/env python3
"""
generate.py — Artifact Generator for 'Audio Spectrogram: Lab Microphone Wiretap'
Track: Forensics & Stego | Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
Author: Yesha (Forensics Track Lead)

Generates:
    challenges/audio_spectrogram/files/lab207_ambient_wiretap.wav

Storyline Context:
    At 02:12 AM, campus surveillance activated an ambient acoustic sensor stationed
    near PC-04 in GICT Lab 207. While the audio captures low-frequency air-conditioner
    hum, electrical 50Hz hum, and sporadic keyboard clicks, high-frequency ultrasonic
    analysis reveals an acoustic watermark synthesized in the 16 kHz – 19.5 kHz range.

Anti-AI Defensive Layer:
    - Multimodal audio models discard high ultrasonic frequencies and focus on speech phonemes.
    - Text LLMs cannot inspect or render audio spectrogram transforms.
    - The flag is only visually discernible when inspected in Audacity or Sonic Visualiser
      under Spectrogram view (linear scale, 15 kHz - 20 kHz).

Flag:
    case{spectrogram_lab207_wiretap_audio}
"""

import math
import wave
import struct
import random
from pathlib import Path

FLAG = "case{spectrogram_lab207_wiretap_audio}"

CHALLENGE_DIR = Path(__file__).resolve().parent
FILES_DIR = CHALLENGE_DIR / "files"
OUTPUT_WAV = FILES_DIR / "lab207_ambient_wiretap.wav"

SAMPLE_RATE = 44100
COL_DURATION = 0.025  # 25 ms per column
FREQ_MIN = 16000.0    # Bottom row frequency (Hz)
FREQ_STEP = 500.0     # Step between rows (Hz)
NUM_ROWS = 7          # 7 frequency rows: 16.0k, 16.5k, 17.0k, 17.5k, 18.0k, 18.5k, 19.0k

# 5x7 Bitmap glyphs (Row 0 is top / 19.0kHz, Row 6 is bottom / 16.0kHz)
# 1 = tone on, 0 = tone off
GLYPHS = {
    'c': [
        "01110",
        "10001",
        "10000",
        "10000",
        "10001",
        "01110",
        "00000",
    ],
    'a': [
        "00000",
        "01110",
        "00001",
        "01111",
        "10001",
        "01111",
        "00000",
    ],
    's': [
        "01110",
        "10000",
        "01110",
        "00001",
        "10001",
        "01110",
        "00000",
    ],
    'e': [
        "01110",
        "10001",
        "11111",
        "10000",
        "10001",
        "01110",
        "00000",
    ],
    '{': [
        "00110",
        "00100",
        "00100",
        "01100",
        "00100",
        "00100",
        "00110",
    ],
    '}': [
        "01100",
        "00100",
        "00100",
        "00110",
        "00100",
        "00100",
        "01100",
    ],
    'p': [
        "00000",
        "01110",
        "10001",
        "11110",
        "10000",
        "10000",
        "10000",
    ],
    't': [
        "00100",
        "01110",
        "00100",
        "00100",
        "00100",
        "00101",
        "00010",
    ],
    'r': [
        "00000",
        "01011",
        "01100",
        "01000",
        "01000",
        "01000",
        "00000",
    ],
    'o': [
        "00000",
        "01110",
        "10001",
        "10001",
        "10001",
        "01110",
        "00000",
    ],
    'g': [
        "00000",
        "01111",
        "10001",
        "01111",
        "00001",
        "10001",
        "01110",
    ],
    'm': [
        "00000",
        "11011",
        "10101",
        "10101",
        "10101",
        "10101",
        "00000",
    ],
    'l': [
        "01100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00110",
        "00000",
    ],
    'b': [
        "10000",
        "11110",
        "10001",
        "10001",
        "10001",
        "11110",
        "00000",
    ],
    '2': [
        "01110",
        "10001",
        "00001",
        "00110",
        "01000",
        "11111",
        "00000",
    ],
    '0': [
        "01110",
        "10011",
        "10101",
        "11001",
        "10001",
        "01110",
        "00000",
    ],
    '7': [
        "11111",
        "00001",
        "00010",
        "00100",
        "00100",
        "00100",
        "00000",
    ],
    'w': [
        "00000",
        "10001",
        "10101",
        "10101",
        "10101",
        "01110",
        "00000",
    ],
    'i': [
        "00100",
        "00000",
        "01100",
        "00100",
        "00100",
        "01110",
        "00000",
    ],
    'd': [
        "00001",
        "01111",
        "10001",
        "10001",
        "10001",
        "01111",
        "00000",
    ],
    'u': [
        "00000",
        "10001",
        "10001",
        "10001",
        "10001",
        "01111",
        "00000",
    ],
    '_': [
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "11111",
        "00000",
    ],
    ' ': [
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
    ]
}


def build_spectrogram_columns(text: str):
    """Converts string into sequence of column vectors (each column has 7 boolean values)."""
    columns = []
    # Leading padding
    for _ in range(8):
        columns.append([0] * NUM_ROWS)

    for char in text:
        glyph = GLYPHS.get(char, GLYPHS[' '])
        # Transpose rows into 5 columns
        for col_idx in range(5):
            col_vector = []
            for row_idx in range(NUM_ROWS):
                is_active = 1 if glyph[row_idx][col_idx] == '1' else 0
                col_vector.append(is_active)
            columns.append(col_vector)
        # 1 column inter-character space
        columns.append([0] * NUM_ROWS)

    # Trailing padding
    for _ in range(8):
        columns.append([0] * NUM_ROWS)

    return columns


def generate_audio():
    print(f"[*] Synthesizing spectrogram wiretap audio for flag: {FLAG}")
    columns = build_spectrogram_columns(FLAG)
    samples_per_col = int(SAMPLE_RATE * COL_DURATION)
    total_stego_samples = len(columns) * samples_per_col

    # Total audio duration includes 1.5s lead-in and 1.5s trail-out
    lead_in_samples = int(SAMPLE_RATE * 1.5)
    trail_out_samples = int(SAMPLE_RATE * 1.5)
    total_samples = lead_in_samples + total_stego_samples + trail_out_samples

    print(f"[+] Total audio length: {total_samples / SAMPLE_RATE:.2f} seconds ({len(columns)} columns)")

    # Seed random for deterministic synthesis
    random.seed(42)

    # Precalculate frequencies for each row:
    # Row 0 (top of glyph) -> 19000 Hz, Row 6 (bottom) -> 16000 Hz
    row_freqs = [FREQ_MIN + (NUM_ROWS - 1 - r) * FREQ_STEP for r in range(NUM_ROWS)]

    audio_samples = []

    # Phase accumulators for continuity
    phases = [0.0] * NUM_ROWS
    hum_phase_50 = 0.0
    hum_phase_100 = 0.0

    current_col_idx = -1
    active_rows = [0] * NUM_ROWS

    for n in range(total_samples):
        # Determine if we are in the stego time window
        if lead_in_samples <= n < (lead_in_samples + total_stego_samples):
            stego_offset = n - lead_in_samples
            col_idx = stego_offset // samples_per_col
            if col_idx != current_col_idx:
                current_col_idx = col_idx
                active_rows = columns[col_idx]
        else:
            active_rows = [0] * NUM_ROWS

        # 1. High frequency stego tones (16 kHz - 19 kHz)
        stego_signal = 0.0
        active_count = sum(active_rows)
        if active_count > 0:
            scale = 4500.0 / math.sqrt(active_count)
            for r in range(NUM_ROWS):
                if active_rows[r]:
                    stego_signal += scale * math.sin(phases[r])

        for r in range(NUM_ROWS):
            phases[r] += 2.0 * math.pi * row_freqs[r] / SAMPLE_RATE
            if phases[r] > 2.0 * math.pi:
                phases[r] -= 2.0 * math.pi

        # 2. Ambient room noise:
        # Electrical mains hum: 50 Hz + 100 Hz harmonic
        hum_phase_50 += 2.0 * math.pi * 50.0 / SAMPLE_RATE
        hum_phase_100 += 2.0 * math.pi * 100.0 / SAMPLE_RATE
        hum = 1200.0 * math.sin(hum_phase_50) + 600.0 * math.sin(hum_phase_100)

        # Ambient low-pass air/ventilation noise
        ventilation = (random.random() - 0.5) * 400.0

        # Sporadic keyboard click noise (bursts)
        # Random click trigger every ~0.6 seconds
        click = 0.0
        if (n % int(SAMPLE_RATE * 0.7)) < 150:
            click = (random.random() - 0.5) * 3500.0 * math.exp(-(n % int(SAMPLE_RATE * 0.7)) / 30.0)

        total_val = stego_signal + hum + ventilation + click

        # Clamp 16-bit signed integer
        clamped = max(-32767, min(32767, int(total_val)))
        audio_samples.append(clamped)

    # Write WAV file
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUTPUT_WAV), "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        raw_frames = struct.pack(f"<{len(audio_samples)}h", *audio_samples)
        wf.writeframes(raw_frames)

    print(f"[+] Successfully wrote {len(raw_frames)} bytes to {OUTPUT_WAV}")


def main():
    print("[*] Generating 'Audio Spectrogram: Lab Microphone Wiretap' artifacts...")
    generate_audio()
    print("[+] Done.")


if __name__ == "__main__":
    main()
