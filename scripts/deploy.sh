#!/usr/bin/env bash
# =============================================================================
# Clawzy.ai — Production Deployment Script
# Usage: ./scripts/deploy.sh [--skip-build] [--skip-migrate]
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[deploy]${NC} $*"; }
warn() { echo -e "${YELLOW}[deploy]${NC} $*"; }
error() { echo -e "${RED}[deploy]${NC} $*" >&2; }

SKIP_BUILD=false
SKIP_MIGRATE=false

for arg in "$@"; do
  case $arg in
    --skip-build) SKIP_BUILD=true ;;
    --skip-migrate) SKIP_MIGRATE=true ;;
    *) error "Unknown option: $arg"; exit 1 ;;
  esac
done

cd "$PROJECT_DIR"

# --- 1. Check .env and critical variables ---
if [ ! -f .env ]; then
  error ".env file not found. Copy .env.example and fill in values."
  exit 1
fi

source .env 2>/dev/null || true

MISSING=0
for var in JWT_SECRET POSTGRES_PASSWORD LITELLM_MASTER_KEY; do
  val="${!var:-}"
  if [ -z "$val" ] || [ "$val" = "change-me-jwt-secret" ] || [ "$val" = "sk-clawzy-change-me" ]; then
    error "Critical variable $var is missing or still a placeholder"
    MISSING=1
  fi
done

# Warn (but don't block) for optional-but-important vars
for var in STRIPE_SECRET_KEY SMTP_HOST SENTRY_DSN; do
  if [ -z "${!var:-}" ]; then
    warn "$var is not set — related features will be disabled"
  fi
done

if [ "$MISSING" = "1" ]; then
  error "Fix critical variables above before deploying."
  exit 1
fi

# --- 2. Pull latest code ---
log "Pulling latest code..."
git pull origin main

# --- 3. Build images ---
if [ "$SKIP_BUILD" = false ]; then
  log "Building Docker images..."
  docker compose -f "$COMPOSE_FILE" build --parallel
else
  warn "Skipping build (--skip-build)"
fi

# --- 4. Start services ---
log "Starting services..."
docker compose -f "$COMPOSE_FILE" up -d

# --- 5. Wait for backend ---
log "Waiting for backend health..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    log "Backend is healthy."
    break
  fi
  if [ "$i" = "30" ]; then
    error "Backend failed to start within 30s"
    docker compose -f "$COMPOSE_FILE" logs backend --tail=50
    exit 1
  fi
  sleep 1
done

# --- 6. Run migrations ---
if [ "$SKIP_MIGRATE" = false ]; then
  log "Running database migrations..."
  docker compose -f "$COMPOSE_FILE" exec backend alembic upgrade head
else
  warn "Skipping migrations (--skip-migrate)"
fi

# --- 7. Smoke test ---
log "Running smoke tests..."
if [ -f "$SCRIPT_DIR/smoke-test.sh" ]; then
  bash "$SCRIPT_DIR/smoke-test.sh"
else
  # Basic health check
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    log "Health check passed."
  else
    error "Health check failed!"
    exit 1
  fi
fi

log "Deployment complete!"
docker compose -f "$COMPOSE_FILE" ps
