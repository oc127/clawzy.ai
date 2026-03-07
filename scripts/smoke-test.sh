#!/usr/bin/env bash
# =============================================================================
# Clawzy.ai — Smoke Test
# Verifies all services are running and responding correctly
# Usage: bash scripts/smoke-test.sh
# =============================================================================
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:3000}"
LITELLM_URL="${LITELLM_URL:-http://127.0.0.1:4000}"

# Load .env if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

MASTER_KEY="${LITELLM_MASTER_KEY:-}"
FAILURES=0

pass() { echo "  ✓ $*"; }
fail() { echo "  ✗ $*"; FAILURES=$((FAILURES + 1)); }

echo "=== Clawzy.ai Smoke Test ==="
echo ""

# ---------------------------------------------------------------------------
# 1. Backend health
# ---------------------------------------------------------------------------
echo "[1/7] Backend health check..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
  pass "Backend is alive (HTTP $HTTP_CODE)"
else
  fail "Backend returned HTTP $HTTP_CODE"
fi

# ---------------------------------------------------------------------------
# 2. Backend deep health (DB + Redis + LiteLLM)
# ---------------------------------------------------------------------------
echo "[2/7] Backend deep health (DB, Redis, LiteLLM)..."
DEEP=$(curl -sf "$BACKEND_URL/health/deep" 2>/dev/null || echo '{"status":"error"}')
DEEP_STATUS=$(echo "$DEEP" | jq -r '.status // "error"' 2>/dev/null || echo "error")
if [ "$DEEP_STATUS" = "ok" ]; then
  pass "All backend dependencies healthy"
elif [ "$DEEP_STATUS" = "degraded" ]; then
  fail "Some dependencies degraded:"
  echo "$DEEP" | jq -r '.checks[] | "    \(.service): \(.status)"' 2>/dev/null
else
  fail "Deep health check failed"
fi

# ---------------------------------------------------------------------------
# 3. Frontend
# ---------------------------------------------------------------------------
echo "[3/7] Frontend health check..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
  pass "Frontend is alive (HTTP $HTTP_CODE)"
else
  fail "Frontend returned HTTP $HTTP_CODE"
fi

# ---------------------------------------------------------------------------
# 4. Auth endpoint reachable
# ---------------------------------------------------------------------------
echo "[4/7] Auth endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BACKEND_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke@test.invalid","password":"x"}' 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "401" ]; then
  pass "Auth endpoint responding (HTTP 401 as expected)"
else
  fail "Auth endpoint returned HTTP $HTTP_CODE (expected 401)"
fi

# ---------------------------------------------------------------------------
# 5. LiteLLM health
# ---------------------------------------------------------------------------
echo "[5/7] LiteLLM health check..."
if [ -z "$MASTER_KEY" ]; then
  fail "LITELLM_MASTER_KEY not set, skipping LiteLLM tests"
else
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$LITELLM_URL/health/liveliness" 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ]; then
    pass "LiteLLM is alive (HTTP $HTTP_CODE)"
  else
    fail "LiteLLM returned HTTP $HTTP_CODE"
  fi
fi

# ---------------------------------------------------------------------------
# 6. LiteLLM models
# ---------------------------------------------------------------------------
echo "[6/7] Available models..."
if [ -n "$MASTER_KEY" ]; then
  MODEL_COUNT=$(curl -sf "$LITELLM_URL/v1/models" \
    -H "Authorization: Bearer $MASTER_KEY" 2>/dev/null | jq '.data | length' 2>/dev/null || echo "0")
  if [ "$MODEL_COUNT" -gt 0 ]; then
    pass "$MODEL_COUNT model(s) available"
  else
    fail "No models returned from LiteLLM"
  fi
else
  fail "Skipped (no LITELLM_MASTER_KEY)"
fi

# ---------------------------------------------------------------------------
# 7. DeepSeek chat
# ---------------------------------------------------------------------------
echo "[7/7] Testing DeepSeek (deepseek-chat)..."
if [ -n "$MASTER_KEY" ]; then
  RESPONSE=$(curl -sf "$LITELLM_URL/v1/chat/completions" \
    -H "Authorization: Bearer $MASTER_KEY" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "deepseek-chat",
      "messages": [{"role": "user", "content": "Say hello in one sentence."}],
      "max_tokens": 50
    }' 2>/dev/null || echo '{}')

  DS_CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content // empty' 2>/dev/null)
  if [ -n "$DS_CONTENT" ]; then
    pass "DeepSeek responded: $DS_CONTENT"
  else
    fail "DeepSeek returned no content"
  fi
else
  fail "Skipped (no LITELLM_MASTER_KEY)"
fi

echo ""
if [ "$FAILURES" -gt 0 ]; then
  echo "=== Smoke test finished with $FAILURES failure(s) ==="
  exit 1
else
  echo "=== All smoke tests passed ==="
fi
