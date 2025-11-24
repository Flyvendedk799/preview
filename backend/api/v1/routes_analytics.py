"""Analytics routes."""
from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.schemas.analytics import AnalyticsSummary, TopDomain
from backend.models.preview import Preview as PreviewModel
from backend.models.domain import Domain as DomainModel
from backend.models.user import User
from backend.db.session import get_db
from backend.core.deps import get_current_user, get_paid_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    period: str = Query("7d", description="Time period: '7d' or '30d'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_paid_user)
):
    """Get analytics summary for the current user for a given period."""
    if period not in ["7d", "30d"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period must be '7d' or '30d'"
        )
    
    # Calculate total clicks from previews for this user only
    total_clicks_result = db.query(func.sum(PreviewModel.monthly_clicks)).filter(
        PreviewModel.user_id == current_user.id
    ).scalar()
    total_clicks = int(total_clicks_result) if total_clicks_result else 0
    
    # Count total previews for this user only
    total_previews = db.query(func.count(PreviewModel.id)).filter(
        PreviewModel.user_id == current_user.id
    ).scalar() or 0
    
    # Count active domains for this user only
    total_domains = db.query(func.count(DomainModel.id)).filter(
        DomainModel.user_id == current_user.id,
        DomainModel.status == "active"
    ).scalar() or 0
    
    # Calculate brand score (simple formula: based on this user's domains and previews)
    brand_score = min(100, 85 + (total_domains * 2) + (total_previews // 2))
    
    # Get top domains by clicks for this user only (group by domain name and sum clicks)
    top_domains_query = db.query(
        PreviewModel.domain,
        func.sum(PreviewModel.monthly_clicks).label('clicks')
    ).filter(
        PreviewModel.user_id == current_user.id
    ).group_by(PreviewModel.domain).order_by(
        func.sum(PreviewModel.monthly_clicks).desc()
    ).limit(4).all()
    
    top_domains = []
    for domain_name, clicks in top_domains_query:
        clicks_int = int(clicks) if clicks else 0
        # Mock CTR calculation (in real app, this would come from impressions data)
        ctr = (clicks_int / (clicks_int * 10)) * 100 if clicks_int > 0 else 0.0
        top_domains.append(
            TopDomain(
                domain=domain_name,
                clicks=clicks_int,
                ctr=round(ctr, 1)
            )
        )
    
    return AnalyticsSummary(
        period=period,
        total_clicks=total_clicks,
        total_previews=total_previews,
        total_domains=total_domains,
        brand_score=int(brand_score),
        top_domains=top_domains,
    )

