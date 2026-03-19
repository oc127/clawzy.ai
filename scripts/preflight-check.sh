#!/usr/bin/env bash
# Nippon Claw — Pre-flight check before docker compose up
# Usage: bash scripts/preflight-check.sh

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

check_required() {
    local var_name="$1"
    local placeholder="$2"
    local value="${!var_name:-}"

    if [ -z "$value" ]; then
        echo -e "${RED}FAIL${NC}:  $var_name is not set"
        ERRORS=$((ERRORS + 1))
    elif [ "$value" = "$placeholder" ]; then
        echo -e "${RED}FAIL${NC}:  $var_name still has placeholder value"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}OK${NC}:    $var_name"
    fi
}

check_optional() {
    local var_name="$1"
    local value="${!var_name:-}"

    if [ -z "$value" ]; then
        echo -e "${YELLOW}WARN${NC}:  $var_name is not set (optional)"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}OK${NC}:    $var_name"
    fi
}

check_production() {
    local var_name="$1"
    local expected="$2"
    local value="${!var_name:-}"

    if [ "${DEPLOY_ENV:-}" = "production" ] && [ "$value" = "$expected" ]; then
        echo -e "${RED}FAIL${NC}:  $var_name is unsafe for production ('$expected')"
        ERRORS=$((ERRORS + 1))
    elif [ "${DEPLOY_ENV:-}" = "production" ]; then
        echo -e "${GREEN}OK${NC}:    $var_name"
    else
        echo -e "${YELLOW}WARN${NC}:  $var_name — remember to change for production"
        WARNINGS=$((WARNINGS + 1))
    fi
}

echo "=== Nippon Claw — Pre-flight Check ==="
echo ""

# Load .env if it exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo "Loaded .env"
    echo "DEPLOY_ENV: ${DEPLOY_ENV:-development}"
else
    echo -e "${RED}FAIL${NC}: .env not found. Run: cp .env.example .env"
    exit 1
fi

echo ""
echo "--- Required ---"
check_required POSTGRES_PASSWORD      "change_me_pg_password_2024"
check_required LITELLM_MASTER_KEY     "sk-clawzy-change-me"
check_required LITELLM_SALT_KEY       "salt-clawzy-change-me"
check_required DEEPSEEK_API_KEY       "sk-your-deepseek-api-key"
check_required DASHSCOPE_API_KEY      "sk-your-dashscope-api-key"
check_required OPENCLAW_GATEWAY_TOKEN "change-me-openclaw-gateway-token"

echo ""
echo "--- Production secrets ---"
check_production JWT_SECRET    "change-me-jwt-secret"
check_production CORS_ORIGINS  "*"

echo ""
echo "--- Optional (Stripe) ---"
check_optional STRIPE_SECRET_KEY
check_optional STRIPE_WEBHOOK_SECRET

echo ""

if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}$ERRORS error(s) found. Fix .env before running docker compose up.${NC}"
    exit 1
elif [ "$WARNINGS" -gt 0 ]; then
    echo -e "${YELLOW}$WARNINGS warning(s). OK for local dev, review before production.${NC}"
else
    echo -e "${GREEN}All checks passed. Ready to deploy.${NC}"
fi
