"""SQLAlchemy ORM model for Newsletter Subscriber."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from backend.db import Base


class NewsletterSubscriber(Base):
    """SQLAlchemy ORM model for newsletter_subscribers table."""
    __tablename__ = "newsletter_subscribers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    source = Column(String, nullable=False, default="demo")  # 'demo', 'blog', 'ads', etc.
    subscribed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    consent_given = Column(Boolean, default=True, nullable=False)  # GDPR compliance
    ip_address = Column(String, nullable=True)  # For tracking source
    user_agent = Column(String, nullable=True)  # For tracking source

