"""Security headers middleware."""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "0"  # Disabled (modern browsers handle XSS better)
        
        # Content Security Policy - basic safe default
        # Allow same-origin, your frontend domain, R2, and screenshot API
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "  # unsafe-inline needed for some frameworks
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "  # Allow images from anywhere (for previews)
            "font-src 'self' data:; "
            "connect-src 'self' https://api.openai.com https://*.r2.cloudflarestorage.com; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response

