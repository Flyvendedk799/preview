"""Activity logging utility service."""
import logging
from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.orm import Session
from backend.models.activity_log import ActivityLog

logger = logging.getLogger(__name__)


def get_client_ip(request: Optional[Request]) -> Optional[str]:
    """Extract client IP address from request."""
    if not request:
        return None
    
    # Check for forwarded IP (common in proxies/load balancers)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to client host
    if request.client:
        return request.client.host
    
    return None


def get_user_agent(request: Optional[Request]) -> Optional[str]:
    """Extract user agent from request."""
    if not request:
        return None
    
    return request.headers.get("User-Agent")


def log_activity(
    db: Session,
    *,
    user_id: Optional[int] = None,
    action: str,
    metadata: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
    organization_id: Optional[int] = None
) -> Optional[ActivityLog]:
    """
    Log an activity event safely without raising exceptions.
    
    Args:
        db: Database session
        user_id: User ID (nullable for system events)
        action: Action type string (e.g., 'user.login', 'domain.created')
        metadata: Additional metadata dictionary
        request: FastAPI Request object (optional, for IP/user agent extraction)
        organization_id: Organization ID (optional, for future team accounts)
    
    Returns:
        ActivityLog instance if successful, None if logging failed
    """
    try:
        # Extract IP and user agent from request if provided
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        # Create activity log entry
        activity_log = ActivityLog(
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            extra_metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(activity_log)
        db.commit()
        db.refresh(activity_log)
        
        return activity_log
    
    except Exception as e:
        # Log the error but don't raise - activity logging should never break the request
        logger.error(f"Failed to log activity '{action}': {e}", exc_info=True)
        # Rollback to prevent any partial state
        try:
            db.rollback()
        except Exception:
            pass
        
        return None

