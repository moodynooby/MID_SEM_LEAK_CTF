#!/usr/bin/env bash
# =================================================================
# Automated Backup Script for CTFd & MariaDB
# IEEE AUSB: Case File: The Mid-Sem Leak
# =================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$ROOT_DIR/backups"
TEMP_DIR="$BACKUP_DIR/temp_$TIMESTAMP"

mkdir -p "$BACKUP_DIR" "$TEMP_DIR"

# Detect engine
CONTAINER_CLI="docker"
if ! command -v docker &>/dev/null && command -v podman &>/dev/null; then
    CONTAINER_CLI="podman"
fi

echo "=========================================================="
echo " [IEEE AUSB CTF] Creating CTFd Backup snapshot: $TIMESTAMP"
echo "=========================================================="

# Check if db container is running
if ! $CONTAINER_CLI ps --format '{{.Names}}' | grep -q 'ctfd_db'; then
    echo "[!] Error: ctfd_db container is not running. Please start the stack first."
    exit 1
fi

source .env 2>/dev/null || true
DB_USER="${MYSQL_USER:-ctfd}"
DB_PASS="${MYSQL_PASSWORD:-ctfd_secure_pass}"
DB_NAME="${MYSQL_DATABASE:-ctfd}"

# 1. Dump MySQL Database
echo "[*] Exporting MariaDB database ($DB_NAME)..."
$CONTAINER_CLI exec ctfd_db mariadb-dump \
    -u "$DB_USER" \
    "-p$DB_PASS" \
    --single-transaction \
    --quick \
    "$DB_NAME" > "$TEMP_DIR/database.sql"

# 2. Copy Uploaded Files
echo "[*] Archiving uploaded challenge attachments and files..."
if $CONTAINER_CLI ps --format '{{.Names}}' | grep -q 'ctfd_app'; then
    $CONTAINER_CLI cp ctfd_app:/var/uploads "$TEMP_DIR/uploads" 2>/dev/null || mkdir -p "$TEMP_DIR/uploads"
else
    mkdir -p "$TEMP_DIR/uploads"
fi

# 3. Copy configuration
cp .env "$TEMP_DIR/.env" 2>/dev/null || true
cp docker-compose.yml "$TEMP_DIR/docker-compose.yml" 2>/dev/null || true

# 4. Create compressed tarball
ARCHIVE_NAME="ctfd_backup_${TIMESTAMP}.tar.gz"
echo "[*] Compressing backup archive: $ARCHIVE_NAME..."
tar -czf "$BACKUP_DIR/$ARCHIVE_NAME" -C "$TEMP_DIR" .

# 5. Clean up temporary directory
rm -rf "$TEMP_DIR"

ARCHIVE_SIZE=$(du -h "$BACKUP_DIR/$ARCHIVE_NAME" | cut -f1)

echo "=========================================================="
echo " [SUCCESS] Backup created successfully!"
echo " Location: $BACKUP_DIR/$ARCHIVE_NAME ($ARCHIVE_SIZE)"
echo " To restore on the backup laptop, run:"
echo "     ./ops/restore.sh $BACKUP_DIR/$ARCHIVE_NAME"
echo "=========================================================="
