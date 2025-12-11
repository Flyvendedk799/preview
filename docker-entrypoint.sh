#!/bin/sh
# Docker entrypoint script for nginx frontend
# This script provides debugging info and ensures environment is set correctly

set -e

echo "=============================================="
echo "[DEBUG] Container Starting at $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=============================================="

# Show all environment variables (filter sensitive ones)
echo "[DEBUG] Environment Variables:"
echo "  PORT=${PORT:-NOT_SET}"
echo "  BACKEND_API_URL=${BACKEND_API_URL:-NOT_SET}"
echo "  VITE_API_BASE_URL=${VITE_API_BASE_URL:-NOT_SET}"

# If BACKEND_API_URL is not set, try to derive it from VITE_API_BASE_URL
if [ -z "$BACKEND_API_URL" ] && [ -n "$VITE_API_BASE_URL" ]; then
    BACKEND_API_URL=$(echo "$VITE_API_BASE_URL" | sed 's|/api/v1$||' | sed 's|/api/v1/.*$||')
    export BACKEND_API_URL
    echo "[DEBUG] Derived BACKEND_API_URL from VITE_API_BASE_URL: $BACKEND_API_URL"
fi

# Set default if still not set
if [ -z "$BACKEND_API_URL" ]; then
    echo "[WARN] BACKEND_API_URL is not set, using placeholder"
    export BACKEND_API_URL="https://placeholder.invalid"
fi

# CRITICAL: Railway requires listening on $PORT
# If PORT is not set, default to 80
if [ -z "$PORT" ]; then
    echo "[WARN] PORT is not set by Railway, defaulting to 80"
    export PORT=80
fi

echo "[DEBUG] Will listen on port: $PORT"
echo "[DEBUG] Will proxy to backend: $BACKEND_API_URL"

# Show what files exist
echo "[DEBUG] Files in /etc/nginx/templates/:"
ls -la /etc/nginx/templates/ 2>/dev/null || echo "  (directory doesn't exist)"

echo "[DEBUG] Files in /etc/nginx/conf.d/:"
ls -la /etc/nginx/conf.d/ 2>/dev/null || echo "  (directory doesn't exist)"

echo "[DEBUG] Static files check:"
echo "  index.html exists: $(test -f /usr/share/nginx/html/index.html && echo 'YES' || echo 'NO')"
ls /usr/share/nginx/html/ | head -5

# Execute the original nginx entrypoint (which processes templates and starts nginx)
echo "[DEBUG] Calling nginx entrypoint..."
echo "=============================================="

exec /docker-entrypoint.sh "$@"
