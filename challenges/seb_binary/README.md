# Safe Exam Browser (SEB): Windows Kiosk Lockdown Reversing

**Category:** Reverse Engineering  
**Difficulty:** Hard (500 pts, dynamic: 500/15/100)  
**Author:** Vansh Shah (@C00LVansh)  
**Flag:** `case{seb_win_pe_lockdown_integrity_bypassed}`

---

## Storyline

TA Piyush Pelaiya planted a modified SEB client (`SEB_KioskGuard.exe`) on the GICT Labs network share to silently bypass the OOP 99 mid-semester exam lockdown. Forensic investigators extracted the rogue binary from `\\GICT-SRV01\ExamSoft\` and must reverse-engineer it to uncover the proof-of-compromise flag.

## Architecture

The binary is a native Windows PE64 (x86_64) executable compiled with `x86_64-w64-mingw32-gcc -O2 -s`. It implements a 4-tier defense:

### Tier 1: Anti-Debugging
- **PEB inspection** via `gs:[0x60]`: checks `BeingDebugged` (PEB+0x02) and `NtGlobalFlag` (PEB+0xBC) for heap debug flags (0x70).
- **API checks**: `IsDebuggerPresent()` and `CheckRemoteDebuggerPresent()`.
- **Hardware breakpoint detection**: `GetThreadContext()` checks Dr0–Dr3 registers.
- **Timing defense**: `RDTSC` instruction pair around a computation block; if the cycle delta exceeds ~10M (single-stepping threshold), execution aborts.

### Tier 2: Process Blacklist
- `CreateToolhelp32Snapshot()` + `Process32First/Next` walks the process list.
- Scans for: `x64dbg.exe`, `x32dbg.exe`, `ghidra.exe`, `ida64.exe`, `cheatengine`, `wireshark.exe`, `procexp.exe`, `ollydbg.exe`, `processhacker.exe`, `httpdebugger`.
- Detection triggers a fake SEB crash dialog and clean exit.

### Tier 3: Self-Integrity Checksum (Anti-Patch Trap)
- Parses its own PE headers at runtime to locate the `.text` section.
- Computes a **FNV-1a 32-bit hash** over `SizeOfRawData` bytes of `.text`.
- Compares against the expected hash baked into `.rdata`.
- **The trap:** If a participant patches even one byte in `.text` (e.g., NOP-ing a JNE to bypass a check), the hash changes and decryption produces garbage.

### Tier 4: Encrypted Flag with Key Schedule
The flag is encrypted using a rolling cipher that mathematically incorporates the `.text` hash:

```
Encryption:  cipher[i] = (plain[i] ^ K_BASE[(i + H_text) % 16]) + SBOX[(i * 7) % 256]
Decryption:  plain[i]  = (cipher[i] - SBOX[(i * 7) % 256]) ^ K_BASE[(i + H_text) % 16]
```

Where:
- `K_BASE` = 16-byte static key: `DE AD BE EF CA FE BA BE 13 37 42 00 F0 0D C0 DE`
- `SBOX` = Standard AES S-Box (256 bytes)
- `H_text` = FNV-1a hash of the `.text` section (correct value required for decryption)
- All arithmetic is mod 256 (uint8_t)

## Anti-AI Defenses

1. **No plaintext flag**: Flag never appears as a string or single-byte XOR in the binary.
2. **Anti-patch trap**: Suggesting "patch the JNE to JE" corrupts the flag (checksum-dependent decryption).
3. **Multi-layer obfuscation**: Requires understanding PE structure, FNV-1a, and the rolling cipher math.

## Solve Path A: Static Analysis + Python (Recommended)

1. Load `SEB_KioskGuard.exe` into Ghidra or IDA Pro.
2. Locate the encrypted byte array in `.rdata` (44 bytes of ciphertext).
3. Identify `K_BASE` (16 bytes) and `SBOX` (256 bytes) in `.rdata`.
4. Trace the decryption function to understand the key schedule math.
5. Compute the `.text` section FNV-1a hash from the PE file.
6. Run the decryption in Python — see `solve.py`.

## Solve Path B: Dynamic Analysis (Windows/Wine + x64dbg)

1. Run under x64dbg with ScyllaHide to suppress anti-debug checks.
2. Hook/bypass `RDTSC` timing and process blacklist.
3. **Do NOT patch `.text`** — let the binary reach decryption naturally.
4. Extract the decrypted flag from memory/registers after the decryption call.

## Build Instructions

```bash
# Requires: x86_64-w64-mingw32-gcc, Python 3.8+
cd challenges/seb_binary/
python generate.py
# Output: files/SEB_KioskGuard.exe
```

## Verification

```bash
python solve.py
# Expected: exit code 0, flag: case{seb_win_pe_lockdown_integrity_bypassed}
```

## Directory Structure

```
challenges/seb_binary/
├── challenge.yml          # CTFd specification (dynamic: 500/15/100)
├── README.md              # This file
├── generate.py            # Build pipeline (compile + binary-patch)
├── solve.py               # Automated solver (PE parse + decrypt)
├── src/
│   └── seb_guard.c        # Challenge source code
└── files/
    └── SEB_KioskGuard.exe # Distributed artifact (PE64)
```
