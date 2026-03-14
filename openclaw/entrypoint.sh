#!/bin/sh
# Entrypoint for OpenClaw gateway container.
# Runs as root (via docker-compose user: "0:0") to fix volume permissions,
# then drops to the node user for the actual process.

# Fix volume permissions — Docker named volumes are created as root
mkdir -p /home/node/.openclaw/workspace /home/node/workspace
chown -R node:node /home/node/.openclaw /home/node/workspace

# Generate openclaw.json from template, substituting environment variables.
CONFIG_TEMPLATE="/tmp/openclaw.json.tpl"
CONFIG_TARGET="/home/node/.openclaw/openclaw.json"

if [ -f "$CONFIG_TEMPLATE" ]; then
    sed "s|\${LITELLM_MASTER_KEY}|${LITELLM_MASTER_KEY}|g" \
        "$CONFIG_TEMPLATE" > "$CONFIG_TARGET"
    chown node:node "$CONFIG_TARGET"
fi

# Drop privileges and execute the original command as node user
exec su -s /bin/sh node -c "exec $*"
