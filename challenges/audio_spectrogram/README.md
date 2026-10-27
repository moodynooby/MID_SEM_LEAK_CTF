# Audio Spectrogram: Lab Microphone Wiretap

**Track:** Stego & Forensics  
**Difficulty:** Medium (Dynamic 500 $\rightarrow$ 100)  
**Author:** Yesha (Forensics Track Lead)  
**Flag:** `case{spectrogram_lab207_wiretap_audio}`

---

## 1. Challenge Overview & Canon Storyline
At 02:12 AM on the night of the incident, an ambient microphone sensor stationed above workstation PC-04 in AU Lab 207 captured room audio. While the human ear only hears 50 Hz electrical hum, air ventilation, and keyboard clicks, an acoustic watermark was modulated into the high-frequency ultrasonic spectrum (16.0 kHz – 19.5 kHz).

---

## 2. Anti-AI Defensive Principle
- **Multimodal Audio Blindspot:** Text-only LLMs cannot process or render waveform audio. Even multimodal audio AI models (Gemini Audio, Whisper) focus on human speech phonemes below 4 kHz and completely ignore ultrasonic visual steganography.
- **Sensory Tooling Requirement:** Solvers must use visual audio analysis software like **Audacity** or **Sonic Visualiser** to inspect the frequency spectrum.

---

## 3. Step-by-Step Solution Walkthrough

### Method A: Visual Spectrogram in Audacity
1. Download and open `files/lab207_ambient_wiretap.wav` in **Audacity** (available on Linux, macOS, and Windows).
2. Click the small downward arrow next to the track name (`lab207_ambient_wiretap`) on the left panel.
3. Select **Spectrogram** view (switches from default Waveform).
4. (Optional) Right-click the vertical frequency scale on the right and select **Spectrogram Settings**:
   - Window size: `1024` or `2048`
   - Min Frequency: `15000 Hz`
   - Max Frequency: `20000 Hz`
5. The visual text flag appears clearly painted in bright spectral peaks:
   ```text
   case{spectrogram_lab207_wiretap_audio}
   ```

### Method B: Automated Python Goertzel Solver
Run the repository solver:
```bash
uv run python challenges/audio_spectrogram/solve.py
```
Output:
```text
[*] Solving Audio Spectrogram challenge from: .../lab207_ambient_wiretap.wav
[+] Loaded 401188 samples (9.10 seconds) at 44100 Hz.
[+] Recovered spectrogram flag string: 'case{spectrogram_lab207_wiretap_audio}'
[SUCCESS] Validated Flag: case{spectrogram_lab207_wiretap_audio}
```

---

## 4. Verification Protocol
1. [x] High-quality WAV file generated at `files/lab207_ambient_wiretap.wav`.
2. [x] Spectrogram visual resolution confirmed in 16–20 kHz band.
3. [x] Generator (`generate.py`) runs reproducibly using pure standard library (`wave`, `struct`, `math`).
4. [x] Solver (`solve.py`) verifies exact flag extraction.
5. [x] Challenge configuration (`challenge.yml`) is valid.
