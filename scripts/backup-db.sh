#!/usr/bin/env bash
# Clawzy.ai 数据库备份脚本
# 用法：cron 每 6 小时执行
#   0 */6 * * * /opt/clawzy/scripts/backup-db.sh >> /var/log/clawzy-backup.log 2>&1

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/clawzy}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/clawzy_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."

# 备份 + 压缩
if ! docker exec clawzy-postgres pg_dump -U clawzy clawzy | gzip > "$BACKUP_FILE"; then
    echo "[$(date)] ERROR: pg_dump failed"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# 验证备份文件
if ! gzip -t "$BACKUP_FILE" 2>/dev/null; then
    echo "[$(date)] ERROR: Backup file is corrupt: ${BACKUP_FILE}"
    exit 1
fi

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date)] Backup created: ${BACKUP_FILE} (${SIZE})"

# 上传到阿里云 OSS（如果 ossutil 已安装且配置了 bucket）
OSS_BUCKET="${OSS_BUCKET:-}"
if [ -n "$OSS_BUCKET" ] && command -v ossutil64 &> /dev/null; then
    echo "[$(date)] Uploading to OSS: ${OSS_BUCKET}"
    if ossutil64 cp "$BACKUP_FILE" "oss://${OSS_BUCKET}/backups/clawzy_${TIMESTAMP}.sql.gz" --force; then
        echo "[$(date)] OSS upload complete."
    else
        echo "[$(date)] WARNING: OSS upload failed, local backup is still available."
    fi
elif [ -n "$OSS_BUCKET" ]; then
    echo "[$(date)] WARNING: OSS_BUCKET set but ossutil64 not found. Install: https://help.aliyun.com/document_detail/120075.html"
fi

# 清理过期备份
DELETED=$(find "$BACKUP_DIR" -name "clawzy_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete -print | wc -l)
echo "[$(date)] Cleaned up ${DELETED} backups older than ${RETENTION_DAYS} days"

echo "[$(date)] Backup complete."
