"""SQLAlchemy ORM model for OrganizationMember."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from backend.db import Base


class OrganizationRole(str, enum.Enum):
    """Organization member roles."""
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class OrganizationMember(Base):
    """SQLAlchemy ORM model for organization_members table."""
    __tablename__ = "organization_members"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(Enum(OrganizationRole), nullable=False, default=OrganizationRole.VIEWER)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organization_memberships")

