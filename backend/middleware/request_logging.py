"""Request logging middleware for tracking request metrics."""
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request metrics with structured logging."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Get request context
        request_id = getattr(request.state, 'request_id', None)
        user_id = getattr(request.state, 'user_id', None) if hasattr(request.state, 'user_id') else None
        org_id = None
        org_id_header = request.headers.get('X-Organization-ID')
        if org_id_header:
            try:
                org_id = int(org_id_header)
            except ValueError:
                pass
        
        # Process request
        response = await call_next(request)
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Log request (skip health checks and static files)
        if request.url.path not in ['/health', '/'] and not request.url.path.startswith('/static'):
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "organization_id": org_id,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                }
            )
        
        return response


request_logging_middleware = RequestLoggingMiddleware

