#!/bin/sh
# Docker entrypoint script for nginx frontend
# Substitutes ${PORT} and ${BACKEND_API_URL} in nginx config

set -e

echo "[Entrypoint] Starting nginx frontend..."
echo "[Entrypoint] PORT=${PORT:-NOT_SET}"

# Set default PORT if not provided
if [ -z "$PORT" ]; then
    export PORT=8080
    echo "[Entrypoint] PORT not set, defaulting to 8080"
fi

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

# Run envsubst on template (substitute PORT and BACKEND_API_URL)
echo "[Entrypoint] Generating nginx config for port $PORT..."
envsubst '${PORT} ${BACKEND_API_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Show the listen line for debugging
grep "listen" /etc/nginx/conf.d/default.conf | head -1

# Remove templates to prevent nginx entrypoint from running envsubst again
rm -rf /etc/nginx/templates

# Test config
nginx -t 2>&1 || { echo "[ERROR] nginx config test failed!"; exit 1; }

echo "[Entrypoint] Starting nginx on port $PORT..."
exec nginx -g "daemon off;"
