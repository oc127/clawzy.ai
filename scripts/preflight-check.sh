#!/usr/bin/env bash
# Clawzy.ai — Pre-flight check before docker compose up
# Usage: bash scripts/preflight-check.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

ERRORS=0

check_var() {
    local var_name="$1"
    local placeholder="$2"
    local value="${!var_name:-}"

    if [ -z "$value" ]; then
        echo -e "${RED}FAIL${NC}: $var_name is not set"
        ERRORS=$((ERRORS + 1))
    elif [ "$value" = "$placeholder" ]; then
        echo -e "${RED}FAIL${NC}: $var_name still has placeholder value"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}OK${NC}:   $var_name"
    fi
}

echo "=== Clawzy.ai Pre-flight Check ==="
echo ""

# Load .env if it exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo "Loaded .env file"
else
    echo -e "${RED}FAIL${NC}: .env file not found. Copy .env.example to .env and fill in values."
    exit 1
fi

echo ""

check_var POSTGRES_PASSWORD "change_me_pg_password_2024"
check_var LITELLM_MASTER_KEY "sk-clawzy-change-me"
check_var LITELLM_SALT_KEY "salt-clawzy-change-me"
check_var DEEPSEEK_API_KEY "sk-your-deepseek-api-key"
check_var DASHSCOPE_API_KEY "sk-your-dashscope-api-key"
check_var JWT_SECRET "change-me-jwt-secret"
check_var OPENCLAW_GATEWAY_TOKEN "change-me-openclaw-gateway-token"

echo ""

if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}$ERRORS issue(s) found. Fix .env before running docker compose up.${NC}"
    exit 1
else
    echo -e "${GREEN}All checks passed. Ready to deploy.${NC}"
fi
