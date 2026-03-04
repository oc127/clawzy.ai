#!/usr/bin/env bash
# =============================================================================
# Clawzy.ai — Server Bootstrap Script
# Target: Ubuntu 22.04 (Alibaba Cloud ECS 4C8G Singapore)
# Usage:  curl -fsSL <url>/setup-server.sh | bash
#    or:  bash scripts/setup-server.sh
# =============================================================================
set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${CYAN}[clawzy]${NC} $*"; }
ok()   { echo -e "${GREEN}[  ok  ]${NC} $*"; }
warn() { echo -e "${YELLOW}[ warn ]${NC} $*"; }
err()  { echo -e "${RED}[error ]${NC} $*" >&2; }

# ---------------------------------------------------------------------------
# 1. System update & essentials
# ---------------------------------------------------------------------------
log "Updating system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
  ca-certificates curl gnupg lsb-release git jq ufw > /dev/null
ok "System packages updated"

# ---------------------------------------------------------------------------
# 2. Install Docker (official method)
# ---------------------------------------------------------------------------
if command -v docker &> /dev/null; then
  ok "Docker already installed: $(docker --version)"
else
  log "Installing Docker..."
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update -qq
  sudo apt-get install -y -qq \
    docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin > /dev/null
  sudo usermod -aG docker "$USER"
  ok "Docker installed: $(docker --version)"
  warn "You may need to log out and back in for docker group to take effect"
fi

# ---------------------------------------------------------------------------
# 3. Firewall setup (UFW)
# ---------------------------------------------------------------------------
log "Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP (future nginx)
sudo ufw allow 443/tcp     # HTTPS (future nginx)
# LiteLLM and OpenClaw are bound to 127.0.0.1, not exposed externally
sudo ufw --force enable
ok "Firewall configured (SSH/HTTP/HTTPS only)"

# ---------------------------------------------------------------------------
# 4. Clone/update project
# ---------------------------------------------------------------------------
DEPLOY_DIR="${CLAWZY_DEPLOY_DIR:-/opt/clawzy}"
if [ ! -d "$DEPLOY_DIR" ]; then
  log "Creating deployment directory at $DEPLOY_DIR..."
  sudo mkdir -p "$DEPLOY_DIR"
  sudo chown "$USER":"$USER" "$DEPLOY_DIR"
fi
ok "Deploy directory: $DEPLOY_DIR"

# ---------------------------------------------------------------------------
# 5. Setup .env if missing
# ---------------------------------------------------------------------------
if [ ! -f "$DEPLOY_DIR/.env" ]; then
  if [ -f "$DEPLOY_DIR/.env.example" ]; then
    log "Creating .env from .env.example — PLEASE EDIT WITH YOUR KEYS"
    cp "$DEPLOY_DIR/.env.example" "$DEPLOY_DIR/.env"
    chmod 600 "$DEPLOY_DIR/.env"

    # Generate random secrets for keys that still have placeholder values
    PG_PASS=$(openssl rand -hex 16)
    MASTER_KEY="sk-clawzy-$(openssl rand -hex 16)"
    SALT_KEY="salt-$(openssl rand -hex 16)"
    GW_TOKEN=$(openssl rand -hex 32)

    sed -i "s/change_me_pg_password_2024/$PG_PASS/" "$DEPLOY_DIR/.env"
    sed -i "s/sk-clawzy-change-me/$MASTER_KEY/" "$DEPLOY_DIR/.env"
    sed -i "s/salt-clawzy-change-me/$SALT_KEY/" "$DEPLOY_DIR/.env"
    sed -i "s/change-me-openclaw-gateway-token/$GW_TOKEN/" "$DEPLOY_DIR/.env"

    warn "Auto-generated secrets in .env"
    warn "You MUST edit $DEPLOY_DIR/.env to add:"
    warn "  - DEEPSEEK_API_KEY"
    warn "  - DASHSCOPE_API_KEY"
  else
    err ".env.example not found in $DEPLOY_DIR"
    exit 1
  fi
else
  ok ".env already exists"
fi

# ---------------------------------------------------------------------------
# 6. Pull images & start services
# ---------------------------------------------------------------------------
log "Pulling Docker images..."
cd "$DEPLOY_DIR"
docker compose pull

log "Starting services..."
docker compose up -d

# ---------------------------------------------------------------------------
# 7. Health check
# ---------------------------------------------------------------------------
log "Waiting for services to become healthy..."
sleep 10

check_service() {
  local name=$1
  local url=$2
  local max_retries=12
  local i=0
  while [ $i -lt $max_retries ]; do
    if curl -sf "$url" > /dev/null 2>&1; then
      ok "$name is healthy"
      return 0
    fi
    sleep 5
    i=$((i + 1))
  done
  warn "$name did not become healthy within 60s (may still be starting)"
  return 1
}

check_service "LiteLLM"  "http://127.0.0.1:4000/health/liveliness"
check_service "Backend"  "http://127.0.0.1:8000/health"
check_service "OpenClaw"  "http://127.0.0.1:18789/health"

# ---------------------------------------------------------------------------
# 8. Setup automated backups (cron)
# ---------------------------------------------------------------------------
log "Setting up automated database backups..."
CRON_JOB="0 */6 * * * ${DEPLOY_DIR}/scripts/backup-db.sh >> /var/log/clawzy-backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v "backup-db.sh"; echo "$CRON_JOB") | crontab -
mkdir -p /var/backups/clawzy
ok "Database backup scheduled every 6 hours"

# ---------------------------------------------------------------------------
# 9. Print summary
# ---------------------------------------------------------------------------
echo ""
echo "============================================="
echo " Clawzy.ai — Deployment Summary"
echo "============================================="
echo " LiteLLM Proxy:  http://127.0.0.1:4000"
echo " LiteLLM UI:     http://127.0.0.1:4000/ui"
echo " OpenClaw GW:    ws://127.0.0.1:18789"
echo " OpenClaw Bridge: http://127.0.0.1:18790"
echo ""
echo " Next steps:"
echo "   1. Edit .env with your API keys"
echo "   2. docker compose restart"
echo "   3. Test: curl http://127.0.0.1:4000/v1/models"
echo "============================================="
