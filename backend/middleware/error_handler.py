"""Error handling middleware for FastAPI."""
import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.models.error import Error as ErrorModel

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """
    Middleware to catch unhandled exceptions and log them to Error model.
    
    This middleware should never crash requests further - it's a safety net.
    """
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        # Log to Error model
        db: Session = None
        try:
            db = SessionLocal()
            
            # Extract user/org info from request if available
            user_id = None
            org_id = None
            
            # Try to get user_id from request state (set by auth dependencies)
            if hasattr(request.state, 'user_id'):
                user_id = request.state.user_id
            
            # Try to get org_id from headers
            org_id_header = request.headers.get('X-Organization-ID')
            if org_id_header:
                try:
                    org_id = int(org_id_header)
                except ValueError:
                    pass
            
            # Get request ID from request state (set by RequestIDMiddleware)
            request_id = getattr(request.state, 'request_id', None) or request.headers.get('X-Request-ID') or f"req_{id(request)}"
            
            # Create error record (Error model uses source, message, details)
            # Redact sensitive information from error message
            import json
            import re
            
            error_message = str(e)
            # Redact common sensitive patterns
            error_message = re.sub(r'(?i)(password|token|secret|key|authorization|bearer)\s*[:=]\s*[\w\-\.]+', r'\1: [REDACTED]', error_message)
            error_message = re.sub(r'(?i)(api[_-]?key|access[_-]?token|secret[_-]?key)\s*[:=]\s*[\w\-\.]+', r'\1: [REDACTED]', error_message)
            
            # Truncate very large error messages
            if len(error_message) > 1000:
                error_message = error_message[:1000] + "... [truncated]"
            
            stacktrace = traceback.format_exc()
            # Redact sensitive info from stacktrace
            stacktrace = re.sub(r'(?i)(password|token|secret|key|authorization|bearer)\s*[:=]\s*[\w\-\.]+', r'\1: [REDACTED]', stacktrace)
            # Truncate very large stacktraces
            if len(stacktrace) > 5000:
                stacktrace = stacktrace[:5000] + "... [truncated]"
            
            error_record = ErrorModel(
                source="api",
                message=error_message,
                details=json.dumps({
                    "path": request.url.path,
                    "method": request.method,
                    "user_id": user_id,
                    "organization_id": org_id,
                    "stacktrace": stacktrace,
                    "request_id": request_id,
                })
            )
            db.add(error_record)
            db.commit()
        except Exception as log_error:
            # Don't fail if logging fails
            logger.error(f"Failed to log error to database: {log_error}", exc_info=True)
        finally:
            if db:
                db.close()
        
        # Log to application logger
        logger.error(
            f"Unhandled exception: {str(e)}",
            exc_info=True,
            extra={
                "path": request.url.path,
                "method": request.method,
                "user_id": user_id,
                "org_id": org_id,
            }
        )
        
        # Return generic error response (don't expose internal details)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal error occurred. Please try again later.",
                "error_id": request_id if 'request_id' in locals() else None
            }
        )

