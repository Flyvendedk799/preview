#!/bin/sh
# Docker entrypoint script for nginx frontend
# Substitutes __NGINX_PORT__ and __BACKEND_URL__ in nginx config using sed
# This avoids using envsubst which would corrupt nginx's internal $variables

set -e

# Get PORT from environment (Railway sets this), default to 80
NGINX_PORT="${PORT:-80}"
echo "[Entrypoint] PORT: $NGINX_PORT"

# Get BACKEND_API_URL, try to derive from VITE_API_BASE_URL if not set
if [ -z "$BACKEND_API_URL" ] && [ -n "$VITE_API_BASE_URL" ]; then
    BACKEND_API_URL=$(echo "$VITE_API_BASE_URL" | sed 's|/api/v1$||' | sed 's|/api/v1/.*$||')
    echo "[Entrypoint] Derived BACKEND_API_URL from VITE_API_BASE_URL: $BACKEND_API_URL"
fi

if [ -z "$BACKEND_API_URL" ]; then
    echo "[Entrypoint] WARNING: BACKEND_API_URL not set, using placeholder"
    BACKEND_API_URL="https://placeholder.invalid"
else
    echo "[Entrypoint] BACKEND_API_URL: $BACKEND_API_URL"
fi

# Substitute placeholders in nginx config
echo "[Entrypoint] Configuring nginx..."
sed -i "s|__NGINX_PORT__|$NGINX_PORT|g" /etc/nginx/conf.d/default.conf
sed -i "s|__BACKEND_URL__|$BACKEND_API_URL|g" /etc/nginx/conf.d/default.conf

echo "[Entrypoint] Final nginx config:"
head -20 /etc/nginx/conf.d/default.conf

echo "[Entrypoint] Starting nginx..."
exec nginx -g "daemon off;"
