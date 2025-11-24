"""Request ID middleware for tracking requests across the system."""
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add a unique request ID to each request."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Generate or use existing request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


request_id_middleware = RequestIDMiddleware

