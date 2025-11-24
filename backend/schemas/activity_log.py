"""Pydantic schemas for ActivityLog."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ActivityLogBase(BaseModel):
    """Base activity log schema."""
    action: str = Field(..., description="Action type (e.g., 'user.login', 'domain.created')")
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="extra_metadata", description="Additional metadata as JSON")


class ActivityLogCreate(ActivityLogBase):
    """Schema for creating a new activity log."""
    user_id: Optional[int] = Field(None, description="User ID (nullable for system events)")
    organization_id: Optional[int] = Field(None, description="Organization ID (for future team accounts)")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")


class ActivityLogPublic(ActivityLogBase):
    """Public activity log schema (user-facing)."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class AdminActivityLogDetail(ActivityLogPublic):
    """Admin activity log schema with full details."""
    user_id: Optional[int]
    organization_id: Optional[int]
    ip_address: Optional[str]
    user_agent: Optional[str]

    class Config:
        from_attributes = True

