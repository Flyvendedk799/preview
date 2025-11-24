"""Stripe webhook handler."""
import stripe
from fastapi import APIRouter, Request, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime
from backend.core.config import settings
from backend.db.session import get_db
from backend.services.stripe_service import update_subscription_status
from backend.services.activity_logger import log_activity

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    
    Verifies webhook signature and processes subscription events.
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    # Get raw body
    body = await request.body()
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            body,
            stripe_signature,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payload: {str(e)}"
        )
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid signature: {str(e)}"
        )
    
    # Handle different event types
    event_type = event['type']
    event_data = event['data']['object']
    
    if event_type == 'customer.subscription.created':
        # New subscription created
        customer_id = event_data.get('customer')
        subscription_id = event_data.get('id')
        status_str = event_data.get('status', 'inactive')
        plan_name = None
        
        # Extract plan name from subscription items
        if 'items' in event_data and event_data['items']['data']:
            price_id = event_data['items']['data'][0]['price']['id']
            # Map price ID to plan name (basic, pro, agency)
            if price_id == settings.STRIPE_PRICE_TIER_BASIC:
                plan_name = 'basic'
            elif price_id == settings.STRIPE_PRICE_TIER_PRO:
                plan_name = 'pro'
            elif price_id == settings.STRIPE_PRICE_TIER_AGENCY:
                plan_name = 'agency'
        
        # Get trial end if exists
        trial_end = event_data.get('trial_end')
        trial_ends_at = None
        if trial_end:
            trial_ends_at = datetime.fromtimestamp(trial_end)
        
        # Find organization by customer_id
        from backend.models.organization import Organization
        org = db.query(Organization).filter(Organization.stripe_customer_id == customer_id).first()
        if org:
            update_subscription_status(
                db=db,
                organization_id=org.id,
                status=status_str,
                plan=plan_name,
                subscription_id=subscription_id,
                trial_ends_at=trial_ends_at
            )
            # Log subscription created
            log_activity(
                db,
                user_id=org.owner_user_id,
                action="billing.subscription.created",
                metadata={"organization_id": org.id, "subscription_id": subscription_id, "plan": plan_name, "status": status_str},
                request=request
            )
    
    elif event_type == 'customer.subscription.updated':
        # Subscription updated
        customer_id = event_data.get('customer')
        subscription_id = event_data.get('id')
        status_str = event_data.get('status', 'inactive')
        plan_name = None
        
        # Extract plan name
        if 'items' in event_data and event_data['items']['data']:
            price_id = event_data['items']['data'][0]['price']['id']
            if price_id == settings.STRIPE_PRICE_TIER_BASIC:
                plan_name = 'basic'
            elif price_id == settings.STRIPE_PRICE_TIER_PRO:
                plan_name = 'pro'
            elif price_id == settings.STRIPE_PRICE_TIER_AGENCY:
                plan_name = 'agency'
        
        trial_end = event_data.get('trial_end')
        trial_ends_at = None
        if trial_end:
            trial_ends_at = datetime.fromtimestamp(trial_end)
        
        from backend.models.organization import Organization
        org = db.query(Organization).filter(Organization.stripe_customer_id == customer_id).first()
        if org:
            update_subscription_status(
                db=db,
                organization_id=org.id,
                status=status_str,
                plan=plan_name,
                subscription_id=subscription_id,
                trial_ends_at=trial_ends_at
            )
            # Log subscription updated
            log_activity(
                db,
                user_id=org.owner_user_id,
                action="billing.subscription.updated",
                metadata={"organization_id": org.id, "subscription_id": subscription_id, "plan": plan_name, "status": status_str},
                request=request
            )
    
    elif event_type == 'customer.subscription.deleted':
        # Subscription canceled
        customer_id = event_data.get('customer')
        
        from backend.models.organization import Organization
        org = db.query(Organization).filter(Organization.stripe_customer_id == customer_id).first()
        if org:
            update_subscription_status(
                db=db,
                organization_id=org.id,
                status='canceled',
                plan=None,
                subscription_id=None
            )
            # Log subscription canceled
            log_activity(
                db,
                user_id=org.owner_user_id,
                action="billing.subscription.canceled",
                metadata={"organization_id": org.id, "customer_id": customer_id},
                request=request
            )
    
    elif event_type == 'invoice.payment_succeeded':
        # Payment succeeded - ensure subscription is active
        customer_id = event_data.get('customer')
        subscription_id = event_data.get('subscription')
        
        if subscription_id:
            from backend.models.organization import Organization
            org = db.query(Organization).filter(Organization.stripe_customer_id == customer_id).first()
            if org:
                # Get subscription details from Stripe
                try:
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    status_str = subscription.status
                    plan_name = None
                    
                    if subscription.items.data:
                        price_id = subscription.items.data[0].price.id
                        if price_id == settings.STRIPE_PRICE_TIER_BASIC:
                            plan_name = 'basic'
                        elif price_id == settings.STRIPE_PRICE_TIER_PRO:
                            plan_name = 'pro'
                        elif price_id == settings.STRIPE_PRICE_TIER_AGENCY:
                            plan_name = 'agency'
                    
                    update_subscription_status(
                        db=db,
                        organization_id=org.id,
                        status=status_str,
                        plan=plan_name,
                        subscription_id=subscription_id
                    )
                    # Log payment succeeded
                    log_activity(
                        db,
                        user_id=org.owner_user_id,
                        action="billing.payment.succeeded",
                        metadata={"organization_id": org.id, "subscription_id": subscription_id, "amount": event_data.get('amount_paid')},
                        request=request
                    )
                except Exception as e:
                    print(f"Error retrieving subscription: {e}")
    
    elif event_type == 'invoice.payment_failed':
        # Payment failed - mark as past_due
        customer_id = event_data.get('customer')
        subscription_id = event_data.get('subscription')
        
        if subscription_id:
            from backend.models.organization import Organization
            org = db.query(Organization).filter(Organization.stripe_customer_id == customer_id).first()
            if org:
                update_subscription_status(
                    db=db,
                    organization_id=org.id,
                    status='past_due',
                    subscription_id=subscription_id
                )
                # Log payment failed
                log_activity(
                    db,
                    user_id=org.owner_user_id,
                    action="billing.payment.failed",
                    metadata={"organization_id": org.id, "subscription_id": subscription_id, "amount_due": event_data.get('amount_due')},
                    request=request
                )
    
    return {"status": "success"}

