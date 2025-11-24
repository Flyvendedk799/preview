"""Billing routes for Stripe integration."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.models.user import User
from backend.db.session import get_db
from backend.core.deps import get_current_user, get_current_org, role_required
from backend.models.organization import Organization
from backend.models.organization_member import OrganizationRole
from backend.services.stripe_service import (
    create_checkout_session,
    create_billing_portal,
    update_subscription_status
)

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    """Schema for checkout session request."""
    price_id: str = Field(..., description="Stripe Price ID")


class CheckoutResponse(BaseModel):
    """Schema for checkout session response."""
    checkout_url: str


class PortalResponse(BaseModel):
    """Schema for billing portal response."""
    portal_url: str


class BillingStatusResponse(BaseModel):
    """Schema for billing status response."""
    subscription_status: str
    subscription_plan: Optional[str] = None
    trial_ends_at: Optional[str] = None


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(
    request: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN]))
):
    """
    Create a Stripe Checkout session for subscription (owner/admin only).
    
    Returns checkout URL that user should be redirected to.
    """
    try:
        # Update org stripe_customer_id if needed
        if not current_org.stripe_customer_id:
            from backend.db.session import SessionLocal
            db_session = SessionLocal()
            try:
                db_org = db_session.query(Organization).filter(Organization.id == current_org.id).first()
                if db_org:
                    from backend.services.stripe_service import create_stripe_customer
                    from backend.models.user import User as UserModel
                    owner = db_session.query(UserModel).filter(UserModel.id == db_org.owner_user_id).first()
                    if owner:
                        customer_id = create_stripe_customer(owner.email, db_org.id)
                        db_org.stripe_customer_id = customer_id
                        db_session.commit()
                        db_session.refresh(db_org)
                        current_org.stripe_customer_id = customer_id
            finally:
                db_session.close()
        
        result = create_checkout_session(current_org, request.price_id)
        db.commit()
        return CheckoutResponse(checkout_url=result["checkout_url"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/portal", response_model=PortalResponse)
def create_portal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN]))
):
    """
    Create a Stripe Billing Portal session (owner/admin only).
    
    Returns portal URL that user should be redirected to.
    """
    try:
        result = create_billing_portal(current_org)
        return PortalResponse(portal_url=result["portal_url"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/status", response_model=BillingStatusResponse)
def get_billing_status(
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org)
):
    """
    Get current organization's billing/subscription status.
    """
    return BillingStatusResponse(
        subscription_status=current_org.subscription_status,
        subscription_plan=current_org.subscription_plan,
        trial_ends_at=current_org.trial_ends_at.isoformat() if current_org.trial_ends_at else None
    )

