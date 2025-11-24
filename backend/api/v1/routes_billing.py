"""Billing routes for Stripe integration."""
import logging
import stripe
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.models.user import User
from backend.db.session import get_db
from backend.core.deps import get_current_user, get_current_org, role_required
from backend.core.config import settings
from backend.models.organization import Organization
from backend.models.organization_member import OrganizationRole
from backend.services.stripe_service import (
    create_checkout_session,
    create_billing_portal,
    update_subscription_status
)

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

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
    # Validate price_id is not empty
    if not request.price_id or not request.price_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price ID is required and cannot be empty"
        )
    
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


@router.post("/sync", response_model=BillingStatusResponse)
def sync_subscription_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN]))
):
    """
    Manually sync subscription status from Stripe (owner/admin only).
    
    This is useful when webhooks haven't been configured yet or to force a refresh.
    """
    if not current_org.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization does not have a Stripe customer ID"
        )
    
    try:
        # Get customer's subscriptions from Stripe
        subscriptions = stripe.Subscription.list(
            customer=current_org.stripe_customer_id,
            status='all',
            limit=1
        )
        
        if not subscriptions.data:
            # No active subscription found
            update_subscription_status(
                db=db,
                organization_id=current_org.id,
                status='inactive',
                plan=None,
                subscription_id=None
            )
            db.refresh(current_org)
            return BillingStatusResponse(
                subscription_status='inactive',
                subscription_plan=None,
                trial_ends_at=None
            )
        
        # Get the most recent subscription
        subscription = subscriptions.data[0]
        status_str = subscription.status
        plan_name = None
        
        # Extract plan name from subscription items
        if subscription.items.data:
            price_id = subscription.items.data[0].price.id
            if price_id == settings.STRIPE_PRICE_TIER_BASIC:
                plan_name = 'basic'
            elif price_id == settings.STRIPE_PRICE_TIER_PRO:
                plan_name = 'pro'
            elif price_id == settings.STRIPE_PRICE_TIER_AGENCY:
                plan_name = 'agency'
        
        # Get trial end if exists
        trial_ends_at = None
        if subscription.trial_end:
            trial_ends_at = datetime.fromtimestamp(subscription.trial_end)
        
        # Update organization subscription status
        update_subscription_status(
            db=db,
            organization_id=current_org.id,
            status=status_str,
            plan=plan_name,
            subscription_id=subscription.id,
            trial_ends_at=trial_ends_at
        )
        
        db.refresh(current_org)
        
        logger.info(f"Synced subscription status for org {current_org.id}: {status_str}, plan: {plan_name}")
        
        return BillingStatusResponse(
            subscription_status=current_org.subscription_status,
            subscription_plan=current_org.subscription_plan,
            trial_ends_at=current_org.trial_ends_at.isoformat() if current_org.trial_ends_at else None
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error syncing subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync subscription status: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error syncing subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync subscription status: {str(e)}"
        )

