#!/bin/sh
# Docker entrypoint script for nginx frontend
# This script substitutes LISTEN_PORT and BACKEND_API_URL in nginx config
# We do this manually with sed instead of envsubst to avoid breaking nginx internal variables ($uri, $scheme, etc.)

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
    # Set a placeholder that will fail gracefully
    BACKEND_API_URL="https://placeholder.invalid"
fi

# Substitute our custom placeholders in nginx config
# We use LISTEN_PORT and leave nginx $variables untouched
echo "[Entrypoint] Configuring nginx to listen on port $PORT"
sed -i "s|LISTEN_PORT|$PORT|g" /etc/nginx/conf.d/default.conf

# Also substitute in the template if envsubst hasn't run yet
if [ -f /etc/nginx/templates/default.conf.template ]; then
    sed -i "s|LISTEN_PORT|$PORT|g" /etc/nginx/templates/default.conf.template
fi

echo "[Entrypoint] Configuration complete"

# Execute the original nginx entrypoint
exec /docker-entrypoint.sh "$@"

