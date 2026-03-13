#!/bin/sh
# Generate openclaw.json from template, substituting environment variables.
# This is needed because JSON files don't support ${ENV_VAR} syntax natively.

CONFIG_TEMPLATE="/tmp/openclaw.json.tpl"
CONFIG_TARGET="/home/node/.openclaw/openclaw.json"

if [ -f "$CONFIG_TEMPLATE" ]; then
    sed "s|\${LITELLM_MASTER_KEY}|${LITELLM_MASTER_KEY}|g" \
        "$CONFIG_TEMPLATE" > "$CONFIG_TARGET"
fi

# Execute the original command
exec "$@"
