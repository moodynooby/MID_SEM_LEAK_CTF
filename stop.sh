#!/usr/bin/env bash
# =================================================================
# CTFd Stack Shutdown Script
# IEEE AUSB: Case File: The Mid-Sem Leak
# =================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_CMD=""
if command -v docker &>/dev/null && docker compose version &>/dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
elif command -v podman-compose &>/dev/null; then
    COMPOSE_CMD="podman-compose"
elif command -v podman &>/dev/null && podman compose version &>/dev/null; then
    COMPOSE_CMD="podman compose"
fi

if [ -n "$COMPOSE_CMD" ]; then
    echo "[*] Gracefully stopping CTFd containers..."
    $COMPOSE_CMD down
    echo "[+] Containers stopped successfully."
else
    echo "[!] Compose command not found."
fi
