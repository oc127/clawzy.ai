#!/usr/bin/env bash
# cleanup-orphans.sh — 清理孤儿 OpenClaw 容器和网络
#
# 孤儿 = Docker 中还在跑但数据库里已没有对应 agent 记录的容器
#
# 用法:
#   bash scripts/cleanup-orphans.sh           # dry-run（只报告，不删）
#   bash scripts/cleanup-orphans.sh --force   # 实际删除
#
# 建议加 cron: 0 * * * * /opt/clawzy/scripts/cleanup-orphans.sh --force >> /var/log/clawzy-cleanup.log 2>&1

set -euo pipefail

FORCE=false
[[ "${1:-}" == "--force" ]] && FORCE=true

DB_CONTAINER="${DB_CONTAINER:-clawzy-postgres}"
DB_NAME="${DB_NAME:-clawzy}"
DB_USER="${DB_USER:-clawzy}"

echo "=== Clawzy Orphan Cleanup — $(date -Iseconds) ==="
echo "Mode: $( [[ "$FORCE" == true ]] && echo 'FORCE (will remove)' || echo 'DRY-RUN (report only)' )"
echo

# 1. 获取 Docker 中所有 clawzy.managed 容器的 agent_id
docker_agents=$(docker ps -a \
  --filter "label=clawzy.managed=true" \
  --format '{{.Label "clawzy.agent_id"}}' 2>/dev/null | sort -u)

if [[ -z "$docker_agents" ]]; then
  echo "No managed containers found in Docker. Nothing to do."
  exit 0
fi

echo "Managed containers in Docker:"
echo "$docker_agents" | sed 's/^/  - /'
echo

# 2. 获取数据库中所有 agent id
db_agents=$(docker exec "$DB_CONTAINER" \
  psql -U "$DB_USER" -d "$DB_NAME" -t -A -c \
  "SELECT id FROM agents WHERE container_id IS NOT NULL;" 2>/dev/null | sort -u)

echo "Active agents in DB:"
if [[ -z "$db_agents" ]]; then
  echo "  (none)"
else
  echo "$db_agents" | sed 's/^/  - /'
fi
echo

# 3. 对比找出孤儿
orphans=$(comm -23 <(echo "$docker_agents") <(echo "$db_agents"))

if [[ -z "$orphans" ]]; then
  echo "No orphaned containers found."
  exit 0
fi

echo "Orphaned containers found:"
echo "$orphans" | sed 's/^/  - /'
echo

# 4. 清理
count=0
while IFS= read -r agent_id; do
  [[ -z "$agent_id" ]] && continue
  container_name="clawzy-agent-${agent_id}"
  network_name="clawzy-agent-${agent_id}"

  if $FORCE; then
    echo "Removing container: $container_name"
    docker rm -f "$container_name" 2>/dev/null || true

    echo "Removing network: $network_name"
    docker network rm "$network_name" 2>/dev/null || true
  else
    echo "[DRY-RUN] Would remove container: $container_name"
    echo "[DRY-RUN] Would remove network: $network_name"
  fi

  count=$((count + 1))
done <<< "$orphans"

echo
echo "Total orphans: $count"
$FORCE && echo "Cleanup complete." || echo "Run with --force to actually remove."
