"""SQLAlchemy ORM model for Error logs."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from backend.db import Base


class Error(Base):
    """SQLAlchemy ORM model for errors table."""
    __tablename__ = "errors"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    source = Column(String, nullable=False, index=True)  # e.g., 'webhook', 'job', 'api'
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)  # Optional JSON/details

