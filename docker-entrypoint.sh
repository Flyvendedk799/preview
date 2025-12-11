#!/bin/sh
# Docker entrypoint script for nginx frontend
# This script substitutes LISTEN_PORT and BACKEND_URL_PLACEHOLDER in nginx config using sed
# We do this manually instead of using envsubst to avoid breaking nginx internal variables ($uri, $scheme, etc.)

set -e

# Set default PORT if not provided (Railway sets this dynamically)
if [ -z "$PORT" ]; then
    PORT=80
    echo "[Entrypoint] PORT not set, defaulting to 80"
else
    echo "[Entrypoint] PORT is set to: $PORT"
fi

# If BACKEND_API_URL is not set, try to derive it from VITE_API_BASE_URL
if [ -z "$BACKEND_API_URL" ] && [ -n "$VITE_API_BASE_URL" ]; then
    # Extract base URL from VITE_API_BASE_URL (remove /api/v1 if present)
    BACKEND_API_URL=$(echo "$VITE_API_BASE_URL" | sed 's|/api/v1$||' | sed 's|/api/v1/.*$||')
    echo "[Entrypoint] Set BACKEND_API_URL from VITE_API_BASE_URL: $BACKEND_API_URL"
fi

# If still not set, use a default (this will cause a 502 but nginx will start)
if [ -z "$BACKEND_API_URL" ]; then
    echo "[Entrypoint] WARNING: BACKEND_API_URL is not set. Please set it in Railway environment variables."
    echo "[Entrypoint] WARNING: The /docs proxy will not work until BACKEND_API_URL is configured."
    BACKEND_API_URL="https://placeholder.invalid"
fi

# Substitute our custom placeholders in nginx config
# The config file uses LISTEN_PORT and BACKEND_URL_PLACEHOLDER as placeholders
# We use sed to replace them, leaving nginx $variables (like $uri, $scheme) untouched
echo "[Entrypoint] Configuring nginx..."
echo "[Entrypoint]   - Port: $PORT"
echo "[Entrypoint]   - Backend URL: $BACKEND_API_URL"

sed -i "s|LISTEN_PORT|$PORT|g" /etc/nginx/conf.d/default.conf
sed -i "s|BACKEND_URL_PLACEHOLDER|$BACKEND_API_URL|g" /etc/nginx/conf.d/default.conf

echo "[Entrypoint] Final nginx config:"
cat /etc/nginx/conf.d/default.conf

echo "[Entrypoint] Starting nginx..."

# Start nginx directly (don't call the default entrypoint which would run envsubst)
exec nginx -g "daemon off;"
