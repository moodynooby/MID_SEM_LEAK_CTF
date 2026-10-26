#!/usr/bin/env bash
# =============================================================================
# stage_workstation.sh — Physical Workstation Staging Script
# Challenge: Physical Forensics: Lab 207 Terminal RAM Dump
# Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)
# =============================================================================
# OPERATIONAL INSTRUCTIONS FOR TECH LEADS (Manas / Krish):
# Run this script on the physical designated PC (PC-04) in Lab 207 during pre-event setup:
#   chmod +x stage_workstation.sh
#   ./stage_workstation.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAW_FILE="${SCRIPT_DIR}/files/lab207_terminal_ram.raw"
SHM_TARGET="/dev/shm/lab207_terminal_ram.raw"

echo "[*] Staging Lab 207 PC-04 Crime Scene Workstation..."

# 1. Verify artifact exists
if [ ! -f "${RAW_FILE}" ]; then
    echo "[!] Artifact not found. Generating now..."
    python3 "${SCRIPT_DIR}/generate.py"
fi

# 2. Copy memory dump directly to volatile /dev/shm RAM filesystem
echo "[+] Copying volatile memory snapshot to ${SHM_TARGET}..."
cp "${RAW_FILE}" "${SHM_TARGET}"
chmod 644 "${SHM_TARGET}"

# 3. Simulate live running suspect process in background
export EXAM_EXFIL_FLAG="case{volatility3_lab207_terminal_ram}"
export CULPRIT_ALIAS="ta_piyush"
export TARGET_VAULT="https://faculty.ahduni.edu.in/vault/oop99"

# 4. Display Crime Scene Banner on screen
clear
cat << "EOF"
================================================================================
          AHMEDABAD UNIVERSITY (SEAS / GICT) — CAMPUS SECURITY
                       CRIME SCENE PRESERVATION NOTICE
================================================================================
 VENUE: Computer Lab 207                     DESIGNATION: PC-04 (Evidence Terminal)
 INCIDENT: Mid-Sem Exam Leak (OOP 99)         STATUS: ACTIVE VOLATILE QUARANTINE
================================================================================

 [!] INVESTIGATION PROTOCOL:
     Investigators must physically access this station to acquire forensic evidence.
     The volatile memory snapshot of the suspect's session has been saved to:

     ===>  /dev/shm/lab207_terminal_ram.raw  <===

 [!] TRIAGE OPTIONS FOR PARTICIPANTS:
     1. Mount your USB thumb drive and copy the .raw image for offline analysis:
        cp /dev/shm/lab207_terminal_ram.raw /media/your_usb/
     2. Or run local memory extraction & strings carving directly on this station.

 [!] NOTICE:
     In the event of hardware reset or high congestion, an offline backup mirror
     is also downloadable directly from the CTFd scoreboard challenge page.
================================================================================
EOF

echo "[+] Workstation PC-04 is successfully staged."
