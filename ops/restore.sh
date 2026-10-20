#!/usr/bin/env bash
# =================================================================
# Automated Restore Script for CTFd & MariaDB
# IEEE AUSB: Case File: The Mid-Sem Leak (Backup Laptop Recovery)
# =================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

BACKUP_ARCHIVE="${1:-}"

# If no archive specified, pick the newest backup
if [ -z "$BACKUP_ARCHIVE" ]; then
    BACKUP_ARCHIVE=$(ls -t "$ROOT_DIR/backups"/ctfd_backup_*.tar.gz 2>/dev/null | head -n 1 || true)
fi

if [ -z "$BACKUP_ARCHIVE" ] || [ ! -f "$BACKUP_ARCHIVE" ]; then
    echo "[!] Error: No backup archive found to restore."
    echo "    Usage: ./ops/restore.sh [path/to/ctfd_backup_YYYYMMDD_HHMMSS.tar.gz]"
    exit 1
fi

echo "=========================================================="
echo " [IEEE AUSB CTF] Restoring CTFd from: $(basename "$BACKUP_ARCHIVE")"
echo "=========================================================="

CONTAINER_CLI="docker"
COMPOSE_CMD="docker compose"
if ! command -v docker &>/dev/null && command -v podman &>/dev/null; then
    CONTAINER_CLI="podman"
    COMPOSE_CMD="podman compose"
fi

TEMP_RESTORE_DIR=$(mktemp -d /tmp/ctfd_restore_XXXXXX)

echo "[*] Extracting backup archive..."
tar -xzf "$BACKUP_ARCHIVE" -C "$TEMP_RESTORE_DIR"

if [ -f "$TEMP_RESTORE_DIR/.env" ] && [ ! -f .env ]; then
    cp "$TEMP_RESTORE_DIR/.env" .env
fi

source .env 2>/dev/null || true
DB_USER="${MYSQL_USER:-ctfd}"
DB_PASS="${MYSQL_PASSWORD:-ctfd_secure_pass}"
DB_NAME="${MYSQL_DATABASE:-ctfd}"

# Ensure database container is up
echo "[*] Ensuring database and cache containers are running..."
$COMPOSE_CMD up -d db cache
sleep 4

echo "[*] Importing MariaDB database ($DB_NAME)..."
if [ -f "$TEMP_RESTORE_DIR/database.sql" ]; then
    $CONTAINER_CLI exec -i ctfd_db mariadb \
        -u "$DB_USER" \
        "-p$DB_PASS" \
        "$DB_NAME" < "$TEMP_RESTORE_DIR/database.sql"
    echo "[+] Database restored successfully."
else
    echo "[!] Warning: database.sql not found in archive."
fi

# Bring up the rest of the stack
echo "[*] Starting CTFd application and reverse proxy..."
$COMPOSE_CMD up -d

# Restore uploads
if [ -d "$TEMP_RESTORE_DIR/uploads" ] && [ "$(ls -A "$TEMP_RESTORE_DIR/uploads")" ]; then
    echo "[*] Restoring challenge uploads into CTFd container..."
    $CONTAINER_CLI cp "$TEMP_RESTORE_DIR/uploads/." ctfd_app:/var/uploads/
    $CONTAINER_CLI exec ctfd_app chown -R 1001:1001 /var/uploads 2>/dev/null || true
fi

# Restart CTFd app container to reload cached models
$CONTAINER_CLI restart ctfd_app

# Cleanup
rm -rf "$TEMP_RESTORE_DIR"

echo "=========================================================="
echo " [SUCCESS] Restoration complete!"
echo " CTFd is restored and live with all teams, submissions, and challenges."
echo " Check web interface at: http://localhost:${HOST_PORT:-80}"
echo "=========================================================="
