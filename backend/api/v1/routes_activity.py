"""Activity log routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.db.session import get_db
from backend.core.deps import get_current_user, get_admin_user
from backend.models.user import User
from backend.models.activity_log import ActivityLog
from backend.schemas.activity_log import ActivityLogPublic, AdminActivityLogDetail

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=List[ActivityLogPublic])
def get_user_activity(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get activity logs for the current user."""
    logs = db.query(ActivityLog).filter(
        ActivityLog.user_id == current_user.id
    ).order_by(desc(ActivityLog.created_at)).offset(skip).limit(limit).all()
    
    return logs


@router.get("/admin", response_model=List[AdminActivityLogDetail])
def get_admin_activity(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Get all activity logs (admin only) with optional filters."""
    query = db.query(ActivityLog)
    
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    
    if action:
        query = query.filter(ActivityLog.action == action)
    
    logs = query.order_by(desc(ActivityLog.created_at)).offset(skip).limit(limit).all()
    
    return logs

