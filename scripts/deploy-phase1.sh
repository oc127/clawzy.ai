#!/usr/bin/env bash
# =============================================================================
# Clawzy.ai — Phase 1 一键部署脚本
# 目标: 空白 Ubuntu 22.04 ECS → 完整运行的 Clawzy.ai 服务栈
# 用法: ssh root@8.216.45.216 'bash -s' < scripts/deploy-phase1.sh
# =============================================================================
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
fail() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "============================================="
echo "  Clawzy.ai Phase 1 — 一键部署"
echo "  目标服务器: $(hostname) ($(uname -m))"
echo "============================================="
echo ""

# ─── Step 1: 系统更新 ────────────────────────────────────────────────────────
log "Step 1/8: 系统更新..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq curl git ca-certificates gnupg lsb-release ufw
log "系统更新完成"

# ─── Step 2: 安装 Docker (官方源) ────────────────────────────────────────────
log "Step 2/8: 安装 Docker..."
if command -v docker &>/dev/null; then
    warn "Docker 已安装，跳过"
else
    # 添加 Docker 官方 GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # 添加仓库
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# 验证
docker --version || fail "Docker 安装失败"
docker compose version || fail "Docker Compose 安装失败"
systemctl enable docker
systemctl start docker
log "Docker 安装完成: $(docker --version)"

# ─── Step 3: 克隆项目 ────────────────────────────────────────────────────────
log "Step 3/8: 克隆项目..."
if [ -d "/opt/clawzy/.git" ]; then
    warn "项目已存在，执行 git pull..."
    cd /opt/clawzy
    git pull origin main || git pull origin master || warn "pull 失败，使用现有代码"
else
    rm -rf /opt/clawzy
    git clone https://github.com/oc127/clawzy.ai.git /opt/clawzy
    cd /opt/clawzy
fi
log "项目克隆完成: /opt/clawzy"

# ─── Step 4: 生成 .env ──────────────────────────────────────────────────────
log "Step 4/8: 生成 .env 配置文件..."
ENV_FILE="/opt/clawzy/.env"

if [ -f "$ENV_FILE" ]; then
    warn ".env 已存在，备份为 .env.bak.$(date +%s)"
    cp "$ENV_FILE" "$ENV_FILE.bak.$(date +%s)"
fi

# 生成随机密钥
PG_PASS=$(openssl rand -hex 16)
LITELLM_MK="sk-clawzy-$(openssl rand -hex 16)"
LITELLM_SK="salt-$(openssl rand -hex 16)"
JWT_SEC=$(openssl rand -hex 32)
OC_TOKEN=$(openssl rand -hex 32)
ADMIN_KEY=$(openssl rand -hex 16)

cat > "$ENV_FILE" <<ENVEOF
# =============================================================================
# Clawzy.ai — 自动生成于 $(date -Iseconds)
# =============================================================================

# --- PostgreSQL ---
POSTGRES_PASSWORD=${PG_PASS}

# --- LiteLLM Proxy ---
LITELLM_MASTER_KEY=${LITELLM_MK}
LITELLM_SALT_KEY=${LITELLM_SK}

# --- Model Provider API Keys ---
# ⚠️ 请手动填写以下两个 API Key:
DEEPSEEK_API_KEY=
DASHSCOPE_API_KEY=

# --- Clawzy Backend ---
JWT_SECRET=${JWT_SEC}

# --- Stripe (Phase 2) ---
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_STARTER=price_starter_monthly
STRIPE_PRICE_PRO=price_pro_monthly
STRIPE_PRICE_BUSINESS=price_business_monthly

# --- Frontend ---
NEXT_PUBLIC_API_URL=http://8.216.45.216/api/v1
NEXT_PUBLIC_WS_URL=ws://8.216.45.216/api/v1
NEXT_PUBLIC_STRIPE_PRICE_STARTER=price_starter_monthly
NEXT_PUBLIC_STRIPE_PRICE_PRO=price_pro_monthly
NEXT_PUBLIC_STRIPE_PRICE_BUSINESS=price_business_monthly

# --- OpenClaw ---
OPENCLAW_GATEWAY_TOKEN=${OC_TOKEN}

# --- Admin & Monitoring ---
ADMIN_API_KEY=${ADMIN_KEY}
ALERT_WEBHOOK_URL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_CHAT_ID=

# --- Email (Phase 2) ---
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@clawzy.ai
APP_URL=http://8.216.45.216

# --- Sentry ---
SENTRY_DSN=

# --- Backup (Phase 2) ---
OSS_ENDPOINT=oss-ap-southeast-1.aliyuncs.com
OSS_BUCKET=
OSS_ACCESS_KEY_ID=
OSS_ACCESS_KEY_SECRET=
OSS_PREFIX=backups/
OSS_RETENTION_DAYS=30
ENVEOF

chmod 600 "$ENV_FILE"
log ".env 生成完成 (密钥已自动生成)"

# ─── Step 5: 配置防火墙 UFW ─────────────────────────────────────────────────
log "Step 5/8: 配置防火墙..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable
log "UFW 防火墙已启用 (开放: 22, 80, 443)"

# ─── Step 6: 拉取镜像并启动服务 ──────────────────────────────────────────────
log "Step 6/8: 拉取 Docker 镜像 (可能需要几分钟)..."
cd /opt/clawzy

# Phase 1: 先启动基础设施 (postgres + redis + litellm)
# backend/web 需要 build, 先拉可拉的镜像
docker compose pull postgres redis litellm || warn "部分镜像拉取失败，继续..."

log "Step 7/8: 启动服务..."
# 使用 docker-compose.yml（开发版，端口暴露到 127.0.0.1 方便调试）
# Phase 1 先启动核心三件套: postgres + redis + litellm
docker compose up -d postgres redis
log "等待 PostgreSQL 和 Redis 就绪..."
sleep 10

# 检查 postgres 是否健康
for i in $(seq 1 12); do
    if docker compose exec -T postgres pg_isready -U clawzy &>/dev/null; then
        log "PostgreSQL 就绪"
        break
    fi
    if [ "$i" -eq 12 ]; then
        fail "PostgreSQL 启动超时"
    fi
    sleep 5
done

# 启动 LiteLLM
docker compose up -d litellm
log "等待 LiteLLM 启动..."
sleep 15

# ─── Step 8: 健康检查 ────────────────────────────────────────────────────────
log "Step 8/8: 运行健康检查..."
echo ""

# LiteLLM 健康检查 (重试)
LITELLM_OK=false
for i in $(seq 1 6); do
    if curl -sf http://127.0.0.1:4000/health/liveliness &>/dev/null; then
        LITELLM_RESULT=$(curl -s http://127.0.0.1:4000/health/liveliness)
        log "LiteLLM 健康检查: $LITELLM_RESULT"
        LITELLM_OK=true
        break
    fi
    warn "LiteLLM 未就绪，等待 10s... ($i/6)"
    sleep 10
done
if [ "$LITELLM_OK" = false ]; then
    warn "LiteLLM 尚未就绪，查看日志: docker compose -f /opt/clawzy/docker-compose.yml logs litellm"
fi

# Redis 检查
if docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
    log "Redis 健康检查: PONG"
else
    warn "Redis 未就绪"
fi

# PostgreSQL 检查
if docker compose exec -T postgres pg_isready -U clawzy &>/dev/null; then
    log "PostgreSQL 健康检查: 就绪"
else
    warn "PostgreSQL 未就绪"
fi

echo ""
echo "─────────────── 服务状态 ───────────────"
docker compose ps
echo ""

echo "============================================="
echo "  Clawzy.ai Phase 1 部署完成!"
echo "============================================="
echo ""
echo "  项目目录:  /opt/clawzy"
echo "  配置文件:  /opt/clawzy/.env"
echo ""
echo "  运行中的服务:"
echo "    PostgreSQL:  127.0.0.1:5432"
echo "    Redis:       127.0.0.1:6379"
echo "    LiteLLM:     127.0.0.1:4000"
echo ""
echo -e "  ${YELLOW}⚠️  请手动编辑 .env 填写 API Key:${NC}"
echo "    nano /opt/clawzy/.env"
echo ""
echo "    需要填写:"
echo "    - DEEPSEEK_API_KEY=你的DeepSeek密钥"
echo "    - DASHSCOPE_API_KEY=你的通义千问密钥"
echo ""
echo "  填写后重启 LiteLLM:"
echo "    cd /opt/clawzy && docker compose restart litellm"
echo ""
echo "  后续启动 backend/web (需要 build):"
echo "    cd /opt/clawzy && docker compose up -d --build backend web"
echo ""
echo "============================================="
