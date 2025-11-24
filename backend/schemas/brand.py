"""Pydantic schemas for Brand Settings."""
from typing import Optional
from pydantic import BaseModel, Field


class BrandSettingsBase(BaseModel):
    """Base brand settings schema."""
    primary_color: str = Field(..., description="Primary brand color (hex)")
    secondary_color: str = Field(..., description="Secondary brand color (hex)")
    accent_color: str = Field(..., description="Accent brand color (hex)")
    font_family: str = Field(default="Inter", description="Font family name")
    logo_url: Optional[str] = Field(None, description="URL to logo image")


class BrandSettingsUpdate(BaseModel):
    """Schema for updating brand settings."""
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_family: Optional[str] = None
    logo_url: Optional[str] = None


class BrandSettings(BrandSettingsBase):
    """Brand settings schema with all fields."""
    id: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "primary_color": "#2979FF",
                "secondary_color": "#0A1A3C",
                "accent_color": "#3FFFD3",
                "font_family": "Inter",
                "logo_url": "https://example.com/logo.png",
            }
        }

