"""Domain verification routes."""
from datetime import datetime
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.models.domain import Domain as DomainModel
from backend.models.user import User
from backend.db.session import get_db
from backend.core.deps import get_current_user, get_current_org, role_required
from backend.models.organization import Organization
from backend.models.organization_member import OrganizationRole
from backend.schemas.domain import Domain
from backend.utils.verification_tokens import (
    generate_verification_token,
    get_dns_instructions,
    get_html_file_instructions,
    get_meta_tag_instructions
)
from backend.services.domain_verification import verify_domain
from backend.services.activity_logger import log_activity

router = APIRouter(prefix="/domains", tags=["verification"])


class VerificationStartRequest(BaseModel):
    """Schema for starting verification."""
    method: str = Field(..., description="Verification method: dns, html, or meta")


class VerificationStartResponse(BaseModel):
    """Schema for verification start response."""
    domain_id: int
    method: str
    token: str
    instructions: Dict[str, str]


@router.post("/{domain_id}/verification/start", response_model=VerificationStartResponse)
def start_verification(
    domain_id: int,
    request: VerificationStartRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN]))
):
    """
    Start domain verification process (owner/admin only).
    
    Generates a verification token and returns instructions based on the chosen method.
    """
    # Validate method
    if request.method not in ['dns', 'html', 'meta']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification method. Must be 'dns', 'html', or 'meta'"
        )
    
    # Get domain and verify ownership
    domain = db.query(DomainModel).filter(
        DomainModel.id == domain_id,
        DomainModel.organization_id == current_org.id
    ).first()
    
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found or not owned by this organization"
        )
    
    # Generate token
    token = generate_verification_token()
    
    # Save token and method to domain
    domain.verification_method = request.method
    domain.verification_token = token
    db.commit()
    db.refresh(domain)
    
    # Get instructions based on method
    if request.method == 'dns':
        instructions = get_dns_instructions(domain.name, token)
    elif request.method == 'html':
        instructions = get_html_file_instructions(domain.name, token)
    else:  # meta
        instructions = get_meta_tag_instructions(domain.name, token)
    
    # Log verification start
    log_activity(
        db,
        user_id=current_user.id,
        action="domain.verification.started",
        metadata={"domain_id": domain.id, "domain_name": domain.name, "method": request.method},
        request=http_request
    )
    
    return VerificationStartResponse(
        domain_id=domain.id,
        method=request.method,
        token=token,
        instructions=instructions
    )


@router.get("/{domain_id}/verification/check", response_model=Domain)
def check_verification(
    domain_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN]))
):
    """
    Check if domain verification is successful (owner/admin only).
    
    Performs the actual verification check based on the domain's verification method.
    """
    # Get domain and verify ownership
    domain = db.query(DomainModel).filter(
        DomainModel.id == domain_id,
        DomainModel.organization_id == current_org.id
    ).first()
    
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found or not owned by this organization"
        )
    
    # Check if verification is already in progress
    if not domain.verification_method or not domain.verification_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verification in progress. Start verification first."
        )
    
    # Perform verification check
    is_verified, error_message = verify_domain(
        domain.name,
        domain.verification_method,
        domain.verification_token
    )
    
    if is_verified:
        # Update domain status
        domain.status = "verified"
        domain.verified_at = datetime.utcnow()
        db.commit()
        db.refresh(domain)
        
        # Log verification success
        log_activity(
            db,
            user_id=current_user.id,
            action="domain.verification.succeeded",
            metadata={"domain_id": domain.id, "domain_name": domain.name, "method": domain.verification_method},
            request=request
        )
        
        return domain
    else:
        # Log verification failure
        log_activity(
            db,
            user_id=current_user.id,
            action="domain.verification.failed",
            metadata={"domain_id": domain.id, "domain_name": domain.name, "method": domain.verification_method, "error": error_message},
            request=request
        )
        
        # Return domain with current status (not verified yet)
        return domain

