#!/bin/sh
# Custom entrypoint that sets BACKEND_API_URL from VITE_API_BASE_URL if needed

# If BACKEND_API_URL is not set, derive from VITE_API_BASE_URL
if [ -z "$BACKEND_API_URL" ] && [ -n "$VITE_API_BASE_URL" ]; then
    export BACKEND_API_URL=$(echo "$VITE_API_BASE_URL" | sed 's|/api/v1$||' | sed 's|/api/v1/.*$||')
    echo "Set BACKEND_API_URL from VITE_API_BASE_URL: $BACKEND_API_URL"
fi

if [ -z "$BACKEND_API_URL" ]; then
    export BACKEND_API_URL="http://localhost:8080"
    echo "WARNING: BACKEND_API_URL not set, using default"
fi

# Run the original nginx entrypoint
exec /docker-entrypoint.sh "$@"
