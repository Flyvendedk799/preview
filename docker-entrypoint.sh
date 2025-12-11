#!/bin/sh
# Docker entrypoint script for nginx frontend
# Simplified for faster startup - Railway has aggressive health check timeout

set -e

echo "[Entrypoint] Starting at $(date -u '+%H:%M:%S UTC')"
echo "[Entrypoint] PORT=${PORT:-NOT_SET}"

# Set defaults
if [ -z "$PORT" ]; then
    export PORT=80
fi

# Derive BACKEND_API_URL if not set
if [ -z "$BACKEND_API_URL" ] && [ -n "$VITE_API_BASE_URL" ]; then
    BACKEND_API_URL=$(echo "$VITE_API_BASE_URL" | sed 's|/api/v1$||')
    export BACKEND_API_URL
fi
if [ -z "$BACKEND_API_URL" ]; then
    export BACKEND_API_URL="https://placeholder.invalid"
fi

echo "[Entrypoint] Generating nginx config..."

# Run envsubst on template (only substitute PORT and BACKEND_API_URL)
envsubst '${PORT} ${BACKEND_API_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Verify config
echo "[Entrypoint] Listening on port: $PORT"
grep "listen" /etc/nginx/conf.d/default.conf | head -1

# Remove templates to prevent nginx entrypoint from running envsubst again
rm -rf /etc/nginx/templates

# TEST: Verify nginx config is valid before starting
echo "[Entrypoint] Testing nginx config..."
nginx -t 2>&1 || { echo "[ERROR] nginx config test failed!"; exit 1; }
echo "[Entrypoint] Config OK!"

# Start nginx directly (bypass nginx entrypoint for faster startup)
echo "[Entrypoint] Starting nginx on port $PORT..."
exec nginx -g "daemon off;"
