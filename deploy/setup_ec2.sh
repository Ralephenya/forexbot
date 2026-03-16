#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# ForexBot EC2 Setup Script
# Run this ONCE on a fresh Ubuntu 22.04 EC2 instance
#
# Usage:
#   chmod +x setup_ec2.sh
#   ./setup_ec2.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo "======================================================"
echo " ForexBot EC2 Setup"
echo "======================================================"

# ── 1. System packages ────────────────────────────────────────────────────────
echo ""
echo "[1/6] Installing system packages..."
sudo apt-get update -q
sudo apt-get install -y -q \
    git \
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
    ufw

# ── 2. Docker ─────────────────────────────────────────────────────────────────
echo ""
echo "[2/6] Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -q
    sudo apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker $USER
    echo "  Docker installed."
else
    echo "  Docker already installed."
fi

# ── 3. Firewall ───────────────────────────────────────────────────────────────
echo ""
echo "[3/6] Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow 8000/tcp    # ForexBot API port
sudo ufw --force enable
echo "  Firewall: SSH + port 8000 open."

# ── 4. Clone repo ─────────────────────────────────────────────────────────────
echo ""
echo "[4/6] Setting up ForexBot..."
REPO_DIR="$HOME/forexbot"
if [ -d "$REPO_DIR" ]; then
    echo "  Repo already exists at $REPO_DIR, pulling latest..."
    cd "$REPO_DIR" && git pull
else
    echo "  Clone your forexbot repo here:"
    echo "  git clone <your-repo-url> $REPO_DIR"
    echo "  Then re-run this script."
    echo ""
    echo "  OR copy files manually with scp:"
    echo "  scp -r ./forexbot ubuntu@<EC2-IP>:~/"
fi

# ── 5. Environment setup ──────────────────────────────────────────────────────
echo ""
echo "[5/6] Environment setup..."
if [ -d "$REPO_DIR" ]; then
    cd "$REPO_DIR"
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo ""
        echo "  ┌────────────────────────────────────────────────────────────┐"
        echo "  │  ACTION REQUIRED: Edit .env before starting               │"
        echo "  │                                                            │"
        echo "  │  nano $REPO_DIR/.env                                       │"
        echo "  │                                                            │"
        echo "  │  Set:                                                      │"
        echo "  │    METAAPI_TOKEN      — from https://app.metaapi.cloud    │"
        echo "  │    METAAPI_ACCOUNT_ID — your MT5 account ID in MetaAPI   │"
        echo "  └────────────────────────────────────────────────────────────┘"
        echo ""
    else
        echo "  .env already exists."
    fi
fi

# ── 6. Start services ─────────────────────────────────────────────────────────
echo ""
echo "[6/6] Instructions to start ForexBot..."
echo ""
echo "  cd $REPO_DIR"
echo "  nano .env          # Add your MetaAPI credentials"
echo "  docker compose up -d --build"
echo "  docker compose logs -f   # Watch the logs"
echo ""
echo "  Your API will be at: http://$(curl -s ifconfig.me):8000"
echo "  Enter this URL in the ForexBot mobile app Settings."
echo ""
echo "======================================================"
echo " Setup complete!"
echo "======================================================"
