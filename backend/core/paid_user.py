"""Dependency for paid user access enforcement."""
from fastapi import Depends, HTTPException, status
from backend.models.user import User
from backend.models.organization import Organization
from backend.core.deps import get_current_user, get_current_org


def get_paid_user(
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org)
) -> User:
    """
    Dependency that ensures organization has an active subscription.
    
    Raises 403 if subscription is not active.
    """
    # Check organization subscription status
    if current_org.subscription_status not in ['active', 'trialing']:
        # Also check trial period
        if current_org.trial_ends_at:
            from datetime import datetime
            if datetime.utcnow() < current_org.trial_ends_at:
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription required. Please upgrade your plan to access this feature."
        )
    return current_user

