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

