"""SQLAlchemy ORM model for preview job failures (DLQ)."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from backend.db import Base


class PreviewJobFailure(Base):
    """SQLAlchemy ORM model for preview_job_failures table (Dead Letter Queue)."""
    __tablename__ = "preview_job_failures"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, nullable=True, index=True)  # RQ job ID if available
    preview_id = Column(Integer, ForeignKey("previews.id"), nullable=True, index=True)
    url = Column(String, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    error_message = Column(Text, nullable=False)
    stacktrace = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

