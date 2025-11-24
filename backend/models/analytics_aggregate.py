"""SQLAlchemy ORM model for AnalyticsDailyAggregate."""
from datetime import date
from sqlalchemy import Column, Integer, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.db import Base


class AnalyticsDailyAggregate(Base):
    """SQLAlchemy ORM model for analytics_daily_aggregates table."""
    __tablename__ = "analytics_daily_aggregates"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=True, index=True)
    preview_id = Column(Integer, ForeignKey("previews.id"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    impressions = Column(Integer, default=0, nullable=False)
    clicks = Column(Integer, default=0, nullable=False)

    # Unique constraint: one row per (date, user_id, domain_id, preview_id, organization_id)
    __table_args__ = (
        UniqueConstraint('date', 'user_id', 'domain_id', 'preview_id', 'organization_id', name='uq_daily_aggregate'),
    )

    # Relationships
    user = relationship("User", back_populates="analytics_aggregates")
    domain = relationship("Domain", back_populates="analytics_aggregates")
    preview = relationship("Preview", back_populates="analytics_aggregates")
    organization = relationship("Organization", back_populates="analytics_aggregates")

