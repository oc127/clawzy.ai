#!/bin/bash
# Daily PostgreSQL backup for Clawzy
# Run via cron: 0 3 * * * /opt/clawzy/scripts/backup-db.sh

set -euo pipefail

BACKUP_DIR="/opt/clawzy/backups"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/clawzy_${DATE}.sql.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Dump database via Docker
docker exec clawzy-postgres pg_dump -U clawzy -d clawzy | gzip > "$BACKUP_FILE"

# Remove old backups
find "$BACKUP_DIR" -name "clawzy_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

echo "[$(date)] Backup completed: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
