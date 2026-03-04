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
docker exec clawzy-postgres pg_dump -U clawzy clawzy | gzip > "$BACKUP_FILE"

# 验证备份文件
if ! gzip -t "$BACKUP_FILE" 2>/dev/null; then
    echo "[$(date)] ERROR: Backup file is corrupt: ${BACKUP_FILE}"
    exit 1
fi

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date)] Backup created: ${BACKUP_FILE} (${SIZE})"

# 清理过期备份
DELETED=$(find "$BACKUP_DIR" -name "clawzy_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete -print | wc -l)
echo "[$(date)] Cleaned up ${DELETED} backups older than ${RETENTION_DAYS} days"

echo "[$(date)] Backup complete."
