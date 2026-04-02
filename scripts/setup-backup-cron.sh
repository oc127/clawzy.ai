#!/bin/bash
# Run this once on the server to set up daily backups at 3 AM JST
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/clawzy/scripts/backup-db.sh >> /opt/clawzy/backups/backup.log 2>&1") | crontab -
echo "Backup cron job installed. Will run daily at 3 AM."
