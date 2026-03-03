#!/usr/bin/env bash
# =============================================================================
# Clawzy.ai — Smoke Test
# Verifies LiteLLM proxy is routing to DeepSeek & Qwen correctly
# Usage: bash scripts/smoke-test.sh
# =============================================================================
set -euo pipefail

LITELLM_URL="${LITELLM_URL:-http://127.0.0.1:4000}"

# Load .env if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

MASTER_KEY="${LITELLM_MASTER_KEY:-}"
if [ -z "$MASTER_KEY" ]; then
  echo "ERROR: LITELLM_MASTER_KEY not set. Source .env or export it."
  exit 1
fi

echo "=== Clawzy.ai Smoke Test ==="
echo ""

# ---------------------------------------------------------------------------
# 1. Health check
# ---------------------------------------------------------------------------
echo "[1/4] LiteLLM health check..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$LITELLM_URL/health/liveliness")
if [ "$HTTP_CODE" = "200" ]; then
  echo "  ✓ LiteLLM is alive (HTTP $HTTP_CODE)"
else
  echo "  ✗ LiteLLM returned HTTP $HTTP_CODE"
  exit 1
fi

# ---------------------------------------------------------------------------
# 2. List models
# ---------------------------------------------------------------------------
echo "[2/4] Available models..."
curl -s "$LITELLM_URL/v1/models" \
  -H "Authorization: Bearer $MASTER_KEY" | jq -r '.data[].id' 2>/dev/null | \
  while read -r model; do echo "  - $model"; done

# ---------------------------------------------------------------------------
# 3. Test DeepSeek
# ---------------------------------------------------------------------------
echo "[3/4] Testing DeepSeek (deepseek-chat)..."
RESPONSE=$(curl -s "$LITELLM_URL/v1/chat/completions" \
  -H "Authorization: Bearer $MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Say hello in one sentence."}],
    "max_tokens": 50
  }')

DS_CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content // empty' 2>/dev/null)
if [ -n "$DS_CONTENT" ]; then
  echo "  ✓ DeepSeek responded: $DS_CONTENT"
else
  echo "  ✗ DeepSeek failed:"
  echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
fi

# ---------------------------------------------------------------------------
# 4. Test Qwen
# ---------------------------------------------------------------------------
echo "[4/4] Testing Qwen (qwen-turbo)..."
RESPONSE=$(curl -s "$LITELLM_URL/v1/chat/completions" \
  -H "Authorization: Bearer $MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-turbo",
    "messages": [{"role": "user", "content": "Say hello in one sentence."}],
    "max_tokens": 50
  }')

QW_CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content // empty' 2>/dev/null)
if [ -n "$QW_CONTENT" ]; then
  echo "  ✓ Qwen responded: $QW_CONTENT"
else
  echo "  ✗ Qwen failed:"
  echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
fi

echo ""
echo "=== Smoke test complete ==="
