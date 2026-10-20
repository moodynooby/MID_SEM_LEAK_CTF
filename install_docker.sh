#!/usr/bin/env bash
# =================================================================
# Docker Engine & Docker Compose Installer for Ubuntu (24.04 / 26.04)
# IEEE AUSB: Case File: The Mid-Sem Leak
# =================================================================

set -euo pipefail

echo "=========================================================="
echo " [IEEE AUSB CTF] Installing Docker & Docker Compose"
echo "=========================================================="

if [ "$EUID" -ne 0 ]; then
    echo "[!] Please run with sudo: sudo ./install_docker.sh"
    exit 1
fi

# 1. Remove conflicting packages
echo "[*] Cleaning up any conflicting packages..."
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
    apt-get remove -y "$pkg" 2>/dev/null || true
done

# 2. Update and install prerequisites
echo "[*] Installing required system tools..."
apt-get update -y
apt-get install -y ca-certificates curl gnupg lsb-release

# 3. Add official Docker GPG key
echo "[*] Configuring official Docker GPG repository..."
install -m 0755 -d /etc/apt/keyrings
if [ ! -f /etc/apt/keyrings/docker.asc ]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
fi

# 4. Add Docker repository to Apt sources
UBUNTU_CODENAME=$(lsb_release -cs 2>/dev/null || echo "noble")
# Fallback to noble if on newer preview release where repository is compatible
if [ "$UBUNTU_CODENAME" = "resolute" ]; then
    UBUNTU_CODENAME="noble"
fi

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $UBUNTU_CODENAME stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. Install Docker packages
echo "[*] Installing Docker Engine, CLI, and Compose plugin..."
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6. Enable and start Docker service
echo "[*] Enabling and starting Docker daemon..."
systemctl enable --now docker

# 7. Add current user to docker group
TARGET_USER="${SUDO_USER:-$USER}"
if [ -n "$TARGET_USER" ] && [ "$TARGET_USER" != "root" ]; then
    echo "[*] Adding user '$TARGET_USER' to 'docker' group..."
    usermod -aG docker "$TARGET_USER"
    echo "[+] User '$TARGET_USER' added to docker group. (Run 'newgrp docker' or re-login to apply without logout)."
fi

echo "=========================================================="
echo " [SUCCESS] Docker & Docker Compose installed successfully!"
echo " Docker Version:  $(docker --version)"
echo " Compose Version: $(docker compose version)"
echo "=========================================================="
