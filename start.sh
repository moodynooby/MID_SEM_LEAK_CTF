#!/usr/bin/env bash
# =================================================================
# CTFd Stack Startup Script
# IEEE AUSB: Case File: The Mid-Sem Leak
# =================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}===================================================================${NC}"
echo -e "${BLUE}${BOLD} [IEEE AUSB] Starting CTFd Stack: Case File: The Mid-Sem Leak       ${NC}"
echo -e "${BLUE}${BOLD}===================================================================${NC}"

# 1. Detect Compose Provider
COMPOSE_CMD=""
if command -v docker &>/dev/null && docker compose version &>/dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
elif command -v podman-compose &>/dev/null; then
    COMPOSE_CMD="podman-compose"
elif command -v podman &>/dev/null && podman compose version &>/dev/null; then
    COMPOSE_CMD="podman compose"
else
    echo -e "${RED}[ERROR] Neither Docker Compose nor Podman Compose was found.${NC}"
    echo -e "${YELLOW}To install Docker Engine on Ubuntu, run:${NC}"
    echo -e "    ${BOLD}sudo ./install_docker.sh${NC}"
    exit 1
fi

echo -e "[*] Using container engine: ${GREEN}${COMPOSE_CMD}${NC}"

# 2. Check for .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}[!] .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    # Generate random secret key
    RANDOM_SECRET=$(head -c 32 /dev/urandom | xxd -p 2>/dev/null || openssl rand -hex 32 2>/dev/null || date +%s%N | sha256sum | head -c 64)
    sed -i "s/change_me_to_a_random_secret_key_for_event_32chars_long/$RANDOM_SECRET/" .env
    echo -e "${GREEN}[+] Created .env with random secret key.${NC}"
fi

# Load variables
source .env 2>/dev/null || true
TARGET_PORT="${HOST_PORT:-80}"

# 3. Port check
if ss -tuln | grep -q ":${TARGET_PORT} "; then
    echo -e "${YELLOW}[!] Warning: Port ${TARGET_PORT} is already bound by another process on host.${NC}"
    echo -e "${YELLOW}    If this is from a previous run of CTFd, it will be recreated.${NC}"
fi

# 4. Start containers
echo -e "[*] Launching CTFd, MariaDB, Redis, and Nginx reverse proxy..."
$COMPOSE_CMD up -d

# 5. Determine Primary LAN IP
PRIMARY_LAN_IP=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1' | grep -v '^172\.' | head -n 1 || echo "localhost")

echo ""
echo -e "${GREEN}${BOLD}===================================================================${NC}"
echo -e "${GREEN}${BOLD} [SUCCESS] CTFd Stack is Up and Running!                           ${NC}"
echo -e "${GREEN}${BOLD}===================================================================${NC}"
echo -e " ${BOLD}Host Local Access:${NC}       http://localhost:${TARGET_PORT}"
echo -e " ${BOLD}Participant LAN URL:${NC}     http://${PRIMARY_LAN_IP}:${TARGET_PORT}"
echo ""
echo -e " ${BOLD}Services running:${NC}"
$COMPOSE_CMD ps
echo ""
echo -e "${BLUE}[*] Next Steps for Tech Leads (Krish, Manas, Vansh Shah):${NC}"
echo -e "  1. Open http://localhost:${TARGET_PORT} in your browser to complete the 1-minute CTFd setup wizard."
echo -e "  2. Set event name: 'Case File: The Mid-Sem Leak — IEEE AUSB'."
echo -e "  3. Generate an Admin API Token in CTFd (Profile -> Access Tokens) and paste it into .env (CTFD_ADMIN_TOKEN)."
echo -e "  4. Use ${BOLD}./ops/backup.sh${NC} to snapshot the database before and during the event."
echo -e "${BLUE}${BOLD}===================================================================${NC}"
