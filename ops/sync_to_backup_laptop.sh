#!/usr/bin/env bash
# =================================================================
# LAN Sync Script: Primary Server -> Standby Backup Laptop
# IEEE AUSB: Case File: The Mid-Sem Leak
# =================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKUP_TARGET_IP="${1:-}"
BACKUP_TARGET_USER="${2:-manas}"
REMOTE_PATH="${3:-/home/$BACKUP_TARGET_USER/Desktop/MID_SEM_LEAK_CTF}"

echo "=========================================================="
echo " [IEEE AUSB CTF] Sync to Standby Backup Laptop"
echo "=========================================================="

if [ -z "$BACKUP_TARGET_IP" ]; then
    echo "Usage: ./ops/sync_to_backup_laptop.sh <BACKUP_LAPTOP_LAN_IP> [SSH_USER] [REMOTE_PATH]"
    echo ""
    echo "Example:"
    echo "    ./ops/sync_to_backup_laptop.sh 192.168.1.50 manas"
    echo ""
    echo "Alternatively, to sync to a plugged-in USB drive:"
    echo "    cp -r $ROOT_DIR/backups /media/$USER/USB_NAME/"
    exit 1
fi

# 1. Trigger local backup first
echo "[*] Step 1: Generating fresh snapshot on primary host..."
"$SCRIPT_DIR/backup.sh"

LATEST_BACKUP=$(ls -t "$ROOT_DIR/backups"/ctfd_backup_*.tar.gz | head -n 1)
echo "[+] Latest snapshot: $(basename "$LATEST_BACKUP")"

# 2. Sync to standby laptop via rsync/scp
echo "[*] Step 2: Transferring backup to $BACKUP_TARGET_USER@$BACKUP_TARGET_IP:$REMOTE_PATH/backups/ ..."
ssh -o ConnectTimeout=5 "$BACKUP_TARGET_USER@$BACKUP_TARGET_IP" "mkdir -p '$REMOTE_PATH/backups'"
scp "$LATEST_BACKUP" "$BACKUP_TARGET_USER@$BACKUP_TARGET_IP:$REMOTE_PATH/backups/"

echo ""
echo "=========================================================="
echo " [SUCCESS] Backup synchronized to Standby Laptop!"
echo " On the backup laptop, in case of emergency switchover, simply run:"
echo "     cd $REMOTE_PATH && ./ops/restore.sh"
echo "=========================================================="
