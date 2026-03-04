#!/usr/bin/env bash
# Clawzy.ai 数据库备份脚本
# 用法：cron 每天凌晨 4 点执行
#   0 4 * * * /path/to/backup-db.sh

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/clawzy}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/clawzy_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

# 备份 + 压缩
docker exec clawzy-postgres pg_dump -U clawzy clawzy | gzip > "$BACKUP_FILE"

echo "Backup created: ${BACKUP_FILE} ($(du -h "$BACKUP_FILE" | cut -f1))"

# 清理过期备份
find "$BACKUP_DIR" -name "clawzy_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete
echo "Cleaned up backups older than ${RETENTION_DAYS} days"
