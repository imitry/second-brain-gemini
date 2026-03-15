#!/bin/bash
set -e

# Map PROXY_URL (set in Coolify) to standard proxy environment variables
# so that all tools (Gemini CLI, curl, npm, etc.) route through SOCKS5
if [ -n "$PROXY_URL" ]; then
    export ALL_PROXY="$PROXY_URL"
    export HTTP_PROXY="$PROXY_URL"
    export HTTPS_PROXY="$PROXY_URL"
    export http_proxy="$PROXY_URL"
    export https_proxy="$PROXY_URL"
    echo "[entrypoint] Proxy configured: ${PROXY_URL##*@}"
fi

exec "$@"
