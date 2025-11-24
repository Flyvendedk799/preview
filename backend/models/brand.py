"""SQLAlchemy ORM model for BrandSettings."""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.db import Base


class BrandSettings(Base):
    """SQLAlchemy ORM model for brand_settings table."""
    __tablename__ = "brand_settings"

    id = Column(Integer, primary_key=True, index=True)
    primary_color = Column(String, nullable=False)
    secondary_color = Column(String, nullable=False)
    accent_color = Column(String, nullable=False)
    font_family = Column(String, nullable=False, default="Inter")
    logo_url = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), index=True, nullable=True)

    # Relationships
    user = relationship("User", back_populates="brand_settings")
    organization = relationship("Organization", back_populates="brand_settings")

