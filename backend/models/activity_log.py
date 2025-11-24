"""SQLAlchemy ORM model for ActivityLog."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.db import Base


class ActivityLog(Base):
    """SQLAlchemy ORM model for activity_logs table."""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    organization_id = Column(Integer, nullable=True, index=True)  # For future team accounts
    action = Column(String, nullable=False, index=True)
    metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="activity_logs")

