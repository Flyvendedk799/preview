"""Pydantic schemas for public preview API."""
from typing import Optional
from pydantic import BaseModel


class PublicPreview(BaseModel):
    """Public preview metadata response."""
    url: str
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    site_name: Optional[str] = None
    type: Optional[str] = None
    # Preview generation status for reliability signals
    # 'fully_generated': Preview was fully generated with AI
    # 'pending_ai': Preview exists but AI generation is pending
    # 'fallback': Preview is using fallback/placeholder data
    status: Optional[str] = None
    # Version for A/B testing and CTR measurement (future use)
    version: Optional[str] = None

