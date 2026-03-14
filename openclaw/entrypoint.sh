#!/bin/sh
# Entrypoint wrapper for OpenClaw gateway container.
# Runs as root (user: "0:0") to fix Docker volume permissions,
# then delegates to the image's original docker-entrypoint.sh.

# Fix volume permissions — Docker named volumes are created as root
mkdir -p /home/node/.openclaw/workspace /home/node/.openclaw/cron /home/node/workspace
chown -R node:node /home/node/.openclaw /home/node/workspace

# Generate openclaw.json from template, substituting environment variables.
CONFIG_TEMPLATE="/tmp/openclaw.json.tpl"
CONFIG_TARGET="/home/node/.openclaw/openclaw.json"

if [ -f "$CONFIG_TEMPLATE" ]; then
    sed "s|\${LITELLM_MASTER_KEY}|${LITELLM_MASTER_KEY}|g" \
        "$CONFIG_TEMPLATE" > "$CONFIG_TARGET"
    chown node:node "$CONFIG_TARGET"
fi

# Delegate to the image's original entrypoint (handles PATH, user, etc.)
exec docker-entrypoint.sh "$@"
