#!/bin/sh
# Docker entrypoint script for nginx frontend
# This script ensures BACKEND_API_URL is set before nginx starts

# If BACKEND_API_URL is not set, try to derive it from VITE_API_BASE_URL
if [ -z "$BACKEND_API_URL" ] && [ -n "$VITE_API_BASE_URL" ]; then
    # Extract base URL from VITE_API_BASE_URL (remove /api/v1 if present)
    BACKEND_API_URL=$(echo "$VITE_API_BASE_URL" | sed 's|/api/v1$||' | sed 's|/api/v1/.*$||')
    export BACKEND_API_URL
    echo "Set BACKEND_API_URL from VITE_API_BASE_URL: $BACKEND_API_URL"
fi

# If still not set, use a default (this will cause a 502 but nginx will start)
if [ -z "$BACKEND_API_URL" ]; then
    echo "WARNING: BACKEND_API_URL is not set. Please set it in Railway environment variables."
    echo "WARNING: The /docs proxy will not work until BACKEND_API_URL is configured."
    # Set a placeholder that will fail gracefully
    export BACKEND_API_URL="https://placeholder.invalid"
fi

# Execute the original nginx entrypoint
exec /docker-entrypoint.sh "$@"

