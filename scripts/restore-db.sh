#!/usr/bin/env bash
# =============================================================================
# Clawzy.ai — 数据库恢复脚本
# 从本地文件或 OSS 下载备份，恢复到 PostgreSQL
#
# 用法：
#   ./restore-db.sh /var/backups/clawzy/clawzy_20250307_120000.sql.gz
#   ./restore-db.sh --from-oss clawzy_20250307_120000.sql.gz
#   ./restore-db.sh --list-oss            # 列出 OSS 上所有备份
#   ./restore-db.sh --latest-local        # 恢复最新本地备份
# =============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/clawzy}"
OSS_ENDPOINT="${OSS_ENDPOINT:-}"
OSS_BUCKET="${OSS_BUCKET:-}"
OSS_ACCESS_KEY_ID="${OSS_ACCESS_KEY_ID:-}"
OSS_ACCESS_KEY_SECRET="${OSS_ACCESS_KEY_SECRET:-}"
OSS_PREFIX="${OSS_PREFIX:-backups/}"

# Source S3 functions from backup script (same directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

_check_oss_config() {
    if [ -z "$OSS_ENDPOINT" ] || [ -z "$OSS_BUCKET" ] || [ -z "$OSS_ACCESS_KEY_ID" ] || [ -z "$OSS_ACCESS_KEY_SECRET" ]; then
        echo "ERROR: OSS not configured. Set OSS_ENDPOINT, OSS_BUCKET, OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET"
        exit 1
    fi
}

# Source the S3 signing functions from backup-db.sh
# We extract them by sourcing the file but not running main
_load_oss_functions() {
    _check_oss_config
    # Source only the function definitions
    eval "$(sed -n '/^_s3_sign()/,/^# ===/p' "${SCRIPT_DIR}/backup-db.sh" | head -n -1)"
}

usage() {
    echo "Usage:"
    echo "  $0 <local-backup-file.sql.gz>"
    echo "  $0 --from-oss <filename.sql.gz>"
    echo "  $0 --list-oss"
    echo "  $0 --list-local"
    echo "  $0 --latest-local"
    exit 1
}

list_local() {
    log "Local backups in ${BACKUP_DIR}:"
    if ls "${BACKUP_DIR}"/clawzy_*.sql.gz 1>/dev/null 2>&1; then
        ls -lhtr "${BACKUP_DIR}"/clawzy_*.sql.gz | awk '{print "  " $NF " (" $5 ")"}'
    else
        echo "  (none)"
    fi
}

list_oss() {
    _load_oss_functions
    log "OSS backups in ${OSS_BUCKET}/${OSS_PREFIX}:"
    xml_response=$(oss_list "$OSS_PREFIX")
    if [ -n "$xml_response" ]; then
        echo "$xml_response" | grep -oP '(?<=<Key>)[^<]+' 2>/dev/null | while read -r key; do
            size=$(echo "$xml_response" | grep -oP "(?<=<Key>${key}</Key>.*<Size>)[0-9]+" 2>/dev/null | head -1 || echo "?")
            if [ "$size" != "?" ] && [ "$size" -gt 0 ] 2>/dev/null; then
                size_mb=$((size / 1024 / 1024))
                echo "  ${key} (${size_mb}MB)"
            else
                echo "  ${key}"
            fi
        done
    else
        echo "  (none or failed to list)"
    fi
}

restore_from_file() {
    local file="$1"

    if [ ! -f "$file" ]; then
        echo "ERROR: File not found: $file"
        exit 1
    fi

    if ! gzip -t "$file" 2>/dev/null; then
        echo "ERROR: File is corrupt or not gzipped: $file"
        exit 1
    fi

    local size
    size=$(du -h "$file" | cut -f1)
    log "Restoring from: ${file} (${size})"

    echo ""
    echo "⚠️  WARNING: This will DROP and recreate the clawzy database!"
    echo "   All current data will be LOST."
    echo ""
    read -rp "Type 'yes' to confirm: " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Aborted."
        exit 0
    fi

    log "Stopping backend services..."
    docker compose stop backend celery-worker celery-beat 2>/dev/null || true

    log "Dropping and recreating database..."
    docker exec clawzy-postgres psql -U clawzy -d postgres -c "DROP DATABASE IF EXISTS clawzy;" || true
    docker exec clawzy-postgres psql -U clawzy -d postgres -c "CREATE DATABASE clawzy OWNER clawzy;"

    log "Restoring backup..."
    gunzip -c "$file" | docker exec -i clawzy-postgres psql -U clawzy clawzy

    log "Running migrations..."
    docker compose exec backend alembic upgrade head 2>/dev/null || \
        log "WARNING: Could not run migrations. Run manually: docker compose exec backend alembic upgrade head"

    log "Restarting services..."
    docker compose start backend celery-worker celery-beat 2>/dev/null || true

    log "Restore complete!"
}

# ===========================================================================
# Main
# ===========================================================================
[ $# -eq 0 ] && usage

case "$1" in
    --list-local)
        list_local
        ;;
    --list-oss)
        list_oss
        ;;
    --latest-local)
        latest=$(ls -t "${BACKUP_DIR}"/clawzy_*.sql.gz 2>/dev/null | head -1 || echo "")
        if [ -z "$latest" ]; then
            echo "ERROR: No local backups found in ${BACKUP_DIR}"
            exit 1
        fi
        restore_from_file "$latest"
        ;;
    --from-oss)
        [ $# -lt 2 ] && { echo "ERROR: Specify OSS filename"; usage; }
        _load_oss_functions
        filename="$2"
        oss_key="${OSS_PREFIX}${filename}"
        tmp_file="/tmp/clawzy_restore_${filename}"

        log "Downloading from OSS: ${oss_key}..."
        if oss_download "$oss_key" "$tmp_file"; then
            log "Download complete."
            restore_from_file "$tmp_file"
            rm -f "$tmp_file"
        else
            echo "ERROR: Failed to download from OSS: ${oss_key}"
            exit 1
        fi
        ;;
    -h|--help)
        usage
        ;;
    *)
        restore_from_file "$1"
        ;;
esac
