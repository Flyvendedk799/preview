#!/bin/sh
# Docker entrypoint script for nginx frontend
# Railway dashboard has port 80 configured, so nginx listens on 80

set -e

echo "[Entrypoint] Starting nginx frontend..."

# Derive BACKEND_API_URL if not set
if [ -z "$BACKEND_API_URL" ] && [ -n "$VITE_API_BASE_URL" ]; then
    BACKEND_API_URL=$(echo "$VITE_API_BASE_URL" | sed 's|/api/v1$||')
    export BACKEND_API_URL
    echo "[Entrypoint] Derived BACKEND_API_URL: $BACKEND_API_URL"
fi

if [ -z "$BACKEND_API_URL" ]; then
    export BACKEND_API_URL="https://placeholder.invalid"
    echo "[Entrypoint] WARNING: BACKEND_API_URL not set"
fi

# Run envsubst on template (only substitute BACKEND_API_URL)
echo "[Entrypoint] Generating nginx config..."
envsubst '${BACKEND_API_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Remove templates to prevent nginx entrypoint from running envsubst again
rm -rf /etc/nginx/templates

# Test config
nginx -t 2>&1 || { echo "[ERROR] nginx config test failed!"; exit 1; }

echo "[Entrypoint] Starting nginx on port 80..."
exec nginx -g "daemon off;"
