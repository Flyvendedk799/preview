"""SQLAlchemy ORM model for PreviewVariant."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.db import Base


class PreviewVariant(Base):
    """SQLAlchemy ORM model for preview_variants table."""
    __tablename__ = "preview_variants"

    id = Column(Integer, primary_key=True, index=True)
    preview_id = Column(Integer, ForeignKey("previews.id"), nullable=False, index=True)
    variant_key = Column(String, nullable=False)  # "a", "b", or "c"
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    tone = Column(String, nullable=True)
    keywords = Column(String, nullable=True)  # Comma-separated
    image_url = Column(String, nullable=True)  # Reuses highlight_image_url by default
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    preview = relationship("Preview", back_populates="variants")

