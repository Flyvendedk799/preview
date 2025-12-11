#!/bin/sh
# Docker entrypoint script for nginx frontend
# This script does config substitution BEFORE nginx starts

set -e

echo "=============================================="
echo "[DEBUG] Container Starting at $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=============================================="

# Show environment
echo "[DEBUG] Environment Variables:"
echo "  PORT=${PORT:-NOT_SET}"
echo "  BACKEND_API_URL=${BACKEND_API_URL:-NOT_SET}"
echo "  VITE_API_BASE_URL=${VITE_API_BASE_URL:-NOT_SET}"

# If BACKEND_API_URL is not set, try to derive it from VITE_API_BASE_URL
if [ -z "$BACKEND_API_URL" ] && [ -n "$VITE_API_BASE_URL" ]; then
    BACKEND_API_URL=$(echo "$VITE_API_BASE_URL" | sed 's|/api/v1$||' | sed 's|/api/v1/.*$||')
    export BACKEND_API_URL
    echo "[DEBUG] Derived BACKEND_API_URL: $BACKEND_API_URL"
fi

# Set defaults
if [ -z "$BACKEND_API_URL" ]; then
    export BACKEND_API_URL="https://placeholder.invalid"
    echo "[WARN] BACKEND_API_URL not set, using placeholder"
fi

if [ -z "$PORT" ]; then
    export PORT=80
    echo "[WARN] PORT not set, defaulting to 80"
fi

echo "[DEBUG] Final PORT: $PORT"
echo "[DEBUG] Final BACKEND_API_URL: $BACKEND_API_URL"

# MANUALLY run envsubst on the template NOW (before nginx entrypoint)
# This ensures we control the substitution and can see the result
if [ -f /etc/nginx/templates/default.conf.template ]; then
    echo "[DEBUG] Running envsubst on template..."
    
    # Only substitute these specific variables (leave nginx $uri, $scheme, etc. alone)
    envsubst '${PORT} ${BACKEND_API_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf
    
    echo "[DEBUG] Generated /etc/nginx/conf.d/default.conf:"
    echo "--- BEGIN CONFIG (first 30 lines) ---"
    head -30 /etc/nginx/conf.d/default.conf
    echo "--- END CONFIG ---"
    
    # Verify the port substitution worked
    if grep -q "listen ${PORT}" /etc/nginx/conf.d/default.conf; then
        echo "[DEBUG] ✓ Port substitution VERIFIED: listening on $PORT"
    else
        echo "[ERROR] ✗ Port substitution FAILED! Check template."
        echo "[DEBUG] Actual listen line:"
        grep "listen" /etc/nginx/conf.d/default.conf || echo "(no listen line found)"
    fi
    
    # Remove template to prevent nginx entrypoint from running envsubst again
    rm -rf /etc/nginx/templates
    echo "[DEBUG] Removed templates dir to prevent double envsubst"
else
    echo "[ERROR] Template file not found!"
    ls -la /etc/nginx/templates/ 2>/dev/null || echo "(templates dir doesn't exist)"
fi

# Verify static files exist
echo "[DEBUG] Static files check:"
if [ -f /usr/share/nginx/html/index.html ]; then
    echo "  ✓ index.html exists"
else
    echo "  ✗ index.html MISSING!"
fi

echo "[DEBUG] Calling nginx entrypoint..."
echo "=============================================="

# Execute the original nginx entrypoint
exec /docker-entrypoint.sh "$@"
