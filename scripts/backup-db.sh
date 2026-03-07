#!/usr/bin/env bash
# =============================================================================
# Clawzy.ai — PostgreSQL 数据库自动备份
# 支持本地 + 阿里云 OSS（S3 兼容 API，无需 ossutil64）
#
# 用法：cron 每 6 小时执行
#   0 */6 * * * /opt/clawzy/scripts/backup-db.sh >> /var/log/clawzy-backup.log 2>&1
#
# 环境变量：
#   BACKUP_DIR              本地备份目录（默认 /var/backups/clawzy）
#   RETENTION_DAYS          本地保留天数（默认 14）
#   OSS_ENDPOINT            OSS Endpoint（如 oss-ap-southeast-1.aliyuncs.com）
#   OSS_BUCKET              OSS Bucket 名称
#   OSS_ACCESS_KEY_ID       阿里云 AccessKey ID
#   OSS_ACCESS_KEY_SECRET   阿里云 AccessKey Secret
#   OSS_PREFIX              OSS 目录前缀（默认 backups/）
#   OSS_RETENTION_DAYS      OSS 保留天数（默认 30）
#   ALERT_WEBHOOK_URL       失败时告警 webhook（Slack / Discord）
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BACKUP_DIR="${BACKUP_DIR:-/var/backups/clawzy}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/clawzy_${TIMESTAMP}.sql.gz"

OSS_ENDPOINT="${OSS_ENDPOINT:-}"
OSS_BUCKET="${OSS_BUCKET:-}"
OSS_ACCESS_KEY_ID="${OSS_ACCESS_KEY_ID:-}"
OSS_ACCESS_KEY_SECRET="${OSS_ACCESS_KEY_SECRET:-}"
OSS_PREFIX="${OSS_PREFIX:-backups/}"
OSS_RETENTION_DAYS="${OSS_RETENTION_DAYS:-30}"

ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-}"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
fail() { log "ERROR: $*"; send_alert "$*"; exit 1; }

send_alert() {
    if [ -n "$ALERT_WEBHOOK_URL" ]; then
        curl -sf -X POST "$ALERT_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"🚨 [Clawzy Backup] $1\"}" \
            > /dev/null 2>&1 || true
    fi
}

# ---------------------------------------------------------------------------
# S3 Signature V4 — OSS 兼容，纯 bash + curl + openssl，无额外依赖
# ---------------------------------------------------------------------------
_s3_sign() {
    # Usage: _s3_sign <method> <object_key> <content_type> [payload_hash]
    local method="$1" object_key="$2" content_type="${3:-}" payload_hash="${4:-}"
    local date_iso date_short region host scope

    date_iso=$(date -u +%Y%m%dT%H%M%SZ)
    date_short=$(date -u +%Y%m%d)
    region=$(echo "$OSS_ENDPOINT" | sed -E 's/^oss-//;s/\.aliyuncs\.com$//')
    host="${OSS_BUCKET}.${OSS_ENDPOINT}"
    scope="${date_short}/${region}/s3/aws4_request"

    [ -z "$payload_hash" ] && payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    # Build canonical headers (must be sorted)
    local canonical_headers="" signed_headers=""
    if [ -n "$content_type" ]; then
        canonical_headers="content-type:${content_type}\nhost:${host}\nx-amz-content-sha256:${payload_hash}\nx-amz-date:${date_iso}"
        signed_headers="content-type;host;x-amz-content-sha256;x-amz-date"
    else
        canonical_headers="host:${host}\nx-amz-content-sha256:${payload_hash}\nx-amz-date:${date_iso}"
        signed_headers="host;x-amz-content-sha256;x-amz-date"
    fi

    local canonical_request="${method}\n/${object_key}\n\n${canonical_headers}\n\n${signed_headers}\n${payload_hash}"
    local canonical_hash
    canonical_hash=$(printf '%b' "$canonical_request" | sha256sum | cut -d' ' -f1)

    local string_to_sign="AWS4-HMAC-SHA256\n${date_iso}\n${scope}\n${canonical_hash}"

    # HMAC signing chain
    local k_date k_region k_service k_signing signature
    k_date=$(printf '%s' "$date_short" | openssl dgst -sha256 -hmac "AWS4${OSS_ACCESS_KEY_SECRET}" -binary | xxd -p -c 256)
    k_region=$(printf '%s' "$region" | openssl dgst -sha256 -mac HMAC -macopt "hexkey:${k_date}" -binary | xxd -p -c 256)
    k_service=$(printf '%s' "s3" | openssl dgst -sha256 -mac HMAC -macopt "hexkey:${k_region}" -binary | xxd -p -c 256)
    k_signing=$(printf '%s' "aws4_request" | openssl dgst -sha256 -mac HMAC -macopt "hexkey:${k_service}" -binary | xxd -p -c 256)
    signature=$(printf '%b' "$string_to_sign" | openssl dgst -sha256 -mac HMAC -macopt "hexkey:${k_signing}" -hex 2>/dev/null | sed 's/^.* //')

    # Return values via global vars (bash doesn't have multi-return)
    _S3_AUTH="AWS4-HMAC-SHA256 Credential=${OSS_ACCESS_KEY_ID}/${scope}, SignedHeaders=${signed_headers}, Signature=${signature}"
    _S3_DATE="$date_iso"
    _S3_HOST="$host"
    _S3_HASH="$payload_hash"
}

oss_upload() {
    local file="$1" object_key="$2"
    local payload_hash
    payload_hash=$(sha256sum "$file" | cut -d' ' -f1)

    _s3_sign "PUT" "$object_key" "application/gzip" "$payload_hash"

    local http_code
    http_code=$(curl -sf -o /dev/null -w "%{http_code}" -X PUT \
        "https://${_S3_HOST}/${object_key}" \
        -H "Content-Type: application/gzip" \
        -H "x-amz-date: ${_S3_DATE}" \
        -H "x-amz-content-sha256: ${_S3_HASH}" \
        -H "Authorization: ${_S3_AUTH}" \
        --data-binary "@${file}" \
        --connect-timeout 30 \
        --max-time 600)

    [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]
}

oss_download() {
    local object_key="$1" dest="$2"

    _s3_sign "GET" "$object_key" ""

    curl -sf -o "$dest" \
        "https://${_S3_HOST}/${object_key}" \
        -H "x-amz-date: ${_S3_DATE}" \
        -H "x-amz-content-sha256: ${_S3_HASH}" \
        -H "Authorization: ${_S3_AUTH}" \
        --connect-timeout 30 \
        --max-time 600
}

oss_delete() {
    local object_key="$1"

    _s3_sign "DELETE" "$object_key" ""

    curl -sf -o /dev/null -X DELETE \
        "https://${_S3_HOST}/${object_key}" \
        -H "x-amz-date: ${_S3_DATE}" \
        -H "x-amz-content-sha256: ${_S3_HASH}" \
        -H "Authorization: ${_S3_AUTH}" \
        --connect-timeout 10 \
        --max-time 30 || true
}

oss_list() {
    local prefix="$1"

    _s3_sign "GET" "" ""

    curl -sf \
        "https://${_S3_HOST}/?list-type=2&prefix=${prefix}" \
        -H "x-amz-date: ${_S3_DATE}" \
        -H "x-amz-content-sha256: ${_S3_HASH}" \
        -H "Authorization: ${_S3_AUTH}" \
        --connect-timeout 10 \
        --max-time 30 2>/dev/null || echo ""
}

# ===========================================================================
# Main
# ===========================================================================
mkdir -p "$BACKUP_DIR"

log "Starting backup..."

# ---------------------------------------------------------------------------
# Step 1: pg_dump + compress
# ---------------------------------------------------------------------------
if ! docker exec clawzy-postgres pg_dump -U clawzy clawzy | gzip > "$BACKUP_FILE"; then
    rm -f "$BACKUP_FILE"
    fail "pg_dump failed"
fi

if ! gzip -t "$BACKUP_FILE" 2>/dev/null; then
    fail "Backup file corrupt: ${BACKUP_FILE}"
fi

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "Local backup created: ${BACKUP_FILE} (${SIZE})"

# ---------------------------------------------------------------------------
# Step 2: Upload to OSS (S3 兼容 API)
# ---------------------------------------------------------------------------
OSS_UPLOADED=false

if [ -n "$OSS_ENDPOINT" ] && [ -n "$OSS_BUCKET" ] && [ -n "$OSS_ACCESS_KEY_ID" ] && [ -n "$OSS_ACCESS_KEY_SECRET" ]; then
    OSS_KEY="${OSS_PREFIX}clawzy_${TIMESTAMP}.sql.gz"
    log "Uploading to OSS: ${OSS_BUCKET}/${OSS_KEY}"

    for attempt in 1 2 3; do
        if oss_upload "$BACKUP_FILE" "$OSS_KEY"; then
            log "OSS upload complete (attempt ${attempt})."
            OSS_UPLOADED=true
            break
        else
            log "WARNING: OSS upload attempt ${attempt} failed."
            [ "$attempt" -lt 3 ] && sleep $((attempt * 5))
        fi
    done

    if [ "$OSS_UPLOADED" = false ]; then
        log "ERROR: All OSS upload attempts failed. Local backup still available."
        send_alert "OSS upload failed after 3 retries. Local: ${BACKUP_FILE}"
    fi
else
    log "OSS not configured — local-only mode. Set OSS_ENDPOINT/OSS_BUCKET/OSS_ACCESS_KEY_ID/OSS_ACCESS_KEY_SECRET to enable."
fi

# ---------------------------------------------------------------------------
# Step 3: Clean up old local backups
# ---------------------------------------------------------------------------
DELETED=$(find "$BACKUP_DIR" -name "clawzy_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete -print | wc -l)
[ "$DELETED" -gt 0 ] && log "Cleaned up ${DELETED} local backups older than ${RETENTION_DAYS} days"

# ---------------------------------------------------------------------------
# Step 4: Clean up old OSS backups (beyond OSS_RETENTION_DAYS)
# ---------------------------------------------------------------------------
if [ "$OSS_UPLOADED" = true ] && [ "$OSS_RETENTION_DAYS" -gt 0 ]; then
    log "Checking OSS for backups older than ${OSS_RETENTION_DAYS} days..."
    cutoff_date=$(date -u -d "${OSS_RETENTION_DAYS} days ago" +%Y%m%d 2>/dev/null || \
                  date -u -v-${OSS_RETENTION_DAYS}d +%Y%m%d 2>/dev/null || echo "")

    if [ -n "$cutoff_date" ]; then
        xml_response=$(oss_list "$OSS_PREFIX")
        if [ -n "$xml_response" ]; then
            oss_deleted=0
            for key in $(echo "$xml_response" | grep -oP '(?<=<Key>)[^<]+' 2>/dev/null || echo ""); do
                file_date=$(echo "$key" | grep -oP 'clawzy_\K[0-9]{8}' 2>/dev/null || echo "")
                if [ -n "$file_date" ] && [ "$file_date" -lt "$cutoff_date" ] 2>/dev/null; then
                    oss_delete "$key"
                    oss_deleted=$((oss_deleted + 1))
                fi
            done
            [ "$oss_deleted" -gt 0 ] && log "Cleaned up ${oss_deleted} OSS backups older than ${OSS_RETENTION_DAYS} days"
        fi
    fi
fi

log "Backup complete. local=${BACKUP_FILE} oss=${OSS_UPLOADED}"
