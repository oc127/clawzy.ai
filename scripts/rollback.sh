#!/usr/bin/env bash
# =============================================================================
# Clawzy.ai — Production Rollback Script
# Usage:
#   ./scripts/rollback.sh --to <commit-sha>     # 回滚到指定 commit
#   ./scripts/rollback.sh --steps <n>            # 回滚 n 个 commit（默认 1）
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
LOG_DIR="/var/log/clawzy"
LOG_FILE="$LOG_DIR/rollback.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[rollback]${NC} $*"; echo "[$(date -u +%FT%TZ)] $*" >> "$LOG_FILE" 2>/dev/null || true; }
warn() { echo -e "${YELLOW}[rollback]${NC} $*"; echo "[$(date -u +%FT%TZ)] WARN: $*" >> "$LOG_FILE" 2>/dev/null || true; }
error() { echo -e "${RED}[rollback]${NC} $*" >&2; echo "[$(date -u +%FT%TZ)] ERROR: $*" >> "$LOG_FILE" 2>/dev/null || true; }

# Ensure log directory exists
mkdir -p "$LOG_DIR" 2>/dev/null || true

# Parse arguments
TARGET_COMMIT=""
STEPS=1

while [[ $# -gt 0 ]]; do
  case $1 in
    --to)
      TARGET_COMMIT="$2"
      shift 2
      ;;
    --steps)
      STEPS="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [--to <commit-sha>] [--steps <n>]"
      echo ""
      echo "Options:"
      echo "  --to <sha>    Rollback to a specific commit"
      echo "  --steps <n>   Rollback n commits (default: 1)"
      exit 0
      ;;
    *)
      error "Unknown option: $1"
      exit 1
      ;;
  esac
done

cd "$PROJECT_DIR"

# Record current state
CURRENT_COMMIT=$(git rev-parse --short HEAD)
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

log "=== Rollback started ==="
log "Current commit: $CURRENT_COMMIT (branch: $CURRENT_BRANCH)"

# Determine target commit
if [ -n "$TARGET_COMMIT" ]; then
  # Validate the commit exists
  if ! git cat-file -e "$TARGET_COMMIT" 2>/dev/null; then
    error "Commit $TARGET_COMMIT does not exist"
    exit 1
  fi
  log "Target: specific commit $TARGET_COMMIT"
else
  TARGET_COMMIT=$(git rev-parse --short "HEAD~$STEPS")
  log "Target: $STEPS step(s) back -> $TARGET_COMMIT"
fi

# Confirm
echo ""
echo "  Current: $CURRENT_COMMIT"
echo "  Target:  $TARGET_COMMIT"
echo ""
read -r -p "Proceed with rollback? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  log "Rollback cancelled by user"
  exit 0
fi

# --- 1. Checkout target commit ---
log "Checking out $TARGET_COMMIT..."
git checkout "$TARGET_COMMIT"

# --- 2. Rebuild images ---
log "Rebuilding Docker images..."
docker compose -f "$COMPOSE_FILE" build --parallel

# --- 3. Restart services ---
log "Restarting services..."
docker compose -f "$COMPOSE_FILE" up -d

# --- 4. Wait for backend health ---
log "Waiting for backend health..."
HEALTHY=false
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    log "Backend is healthy."
    HEALTHY=true
    break
  fi
  sleep 1
done

if [ "$HEALTHY" = false ]; then
  error "Backend failed to start within 30s after rollback!"
  error "Current state: commit $TARGET_COMMIT"
  error "Previous state was: $CURRENT_COMMIT"
  error "Manual intervention required. NOT auto-reverting to avoid loops."
  docker compose -f "$COMPOSE_FILE" logs backend --tail=50
  exit 1
fi

# --- 5. Run smoke tests ---
log "Running smoke tests..."
if [ -f "$SCRIPT_DIR/smoke-test.sh" ]; then
  if bash "$SCRIPT_DIR/smoke-test.sh"; then
    log "Smoke tests passed."
  else
    warn "Smoke tests had failures (non-blocking for rollback)"
  fi
else
  log "No smoke test script found, skipping."
fi

# --- 6. Record rollback event ---
if [ -f .env ]; then
  source .env 2>/dev/null || true
fi
ADMIN_KEY="${ADMIN_API_KEY:-}"
if [ -n "$ADMIN_KEY" ]; then
  curl -sf http://localhost:8000/admin/deploy-event \
    -H "X-Admin-Key: $ADMIN_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"commit\":\"$TARGET_COMMIT\",\"timestamp\":\"$(date -u +%FT%TZ)\",\"type\":\"rollback\",\"from\":\"$CURRENT_COMMIT\"}" || true
fi

log "=== Rollback complete ==="
log "Rolled back from $CURRENT_COMMIT to $TARGET_COMMIT"
echo ""
docker compose -f "$COMPOSE_FILE" ps
