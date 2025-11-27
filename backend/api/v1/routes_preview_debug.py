"""
Preview debug and verification endpoints.

For internal testing and proof of AI visual focus improvement.
These endpoints are admin-only.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.core.deps import get_admin_user
from backend.models.user import User

logger = logging.getLogger("preview_worker")

router = APIRouter(prefix="/preview-debug", tags=["preview-debug"])


# =============================================================================
# SCHEMAS
# =============================================================================

class DebugComparisonRequest(BaseModel):
    """Request to run debug comparison on a URL."""
    url: str


class FocusRegionSchema(BaseModel):
    """Focus region coordinates."""
    x: float
    y: float
    width: float
    height: float


class AIAnalysisSchema(BaseModel):
    """AI analysis result."""
    focus_region: Optional[FocusRegionSchema] = None
    intent_type: Optional[str] = None
    confidence: Optional[float] = None
    primary_reason: Optional[str] = None
    secondary_elements: Optional[List[str]] = None
    fallback_used: Optional[str] = None
    processing_time_ms: Optional[int] = None


class DebugComparisonResponse(BaseModel):
    """Response with comparison results."""
    url: str
    timestamp: str
    raw_screenshot_size: int
    ai: dict
    heuristic: dict


class VerificationSuiteRequest(BaseModel):
    """Request to run verification suite."""
    urls: Optional[List[str]] = None  # If None, uses default test URLs


class VerificationResultSchema(BaseModel):
    """Single verification result."""
    url: str
    ai_crop_success: bool
    heuristic_crop_success: bool
    ai_confidence: Optional[float] = None
    ai_intent: Optional[str] = None
    ai_reason: Optional[str] = None
    error: Optional[str] = None


class VerificationSuiteResponse(BaseModel):
    """Response with verification suite results."""
    total_urls: int
    ai_success_count: int
    heuristic_success_count: int
    high_confidence_count: int
    results: List[VerificationResultSchema]


class CacheStatsResponse(BaseModel):
    """Cache statistics response."""
    enabled: bool
    preview_entries: Optional[int] = None
    analysis_entries: Optional[int] = None
    total_hits: Optional[int] = None
    total_misses: Optional[int] = None
    memory_used: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/compare", response_model=DebugComparisonResponse)
def run_debug_comparison(
    request: DebugComparisonRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Run side-by-side comparison of AI vs heuristic crop for a single URL.
    
    Admin only. For debugging and verification.
    """
    from backend.jobs.screenshot_generation import generate_debug_comparison
    
    try:
        result = generate_debug_comparison(request.url)
        return DebugComparisonResponse(**result)
    except Exception as e:
        logger.error(f"Debug comparison failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(e)}"
        )


@router.post("/verify-suite", response_model=VerificationSuiteResponse)
def run_verification_suite(
    request: VerificationSuiteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Run verification suite on multiple URLs.
    
    Admin only. For proving AI improvement over heuristics.
    
    If no URLs provided, uses default test set covering:
    - Landing pages with CTAs
    - Blog/articles
    - Product pages
    - SaaS dashboards
    """
    from backend.services.ai_visual_focus import run_verification_suite as run_suite, TEST_URLS
    
    urls = request.urls or TEST_URLS[:10]  # Limit to 10 for performance
    
    try:
        raw_results = run_suite(urls)
        
        # Process results
        results = []
        high_confidence_count = 0
        
        for r in raw_results:
            comparison = r.get("comparison", {})
            ai_confidence = comparison.get("ai_confidence")
            
            if ai_confidence and ai_confidence >= 0.7:
                high_confidence_count += 1
            
            results.append(VerificationResultSchema(
                url=r.get("url", ""),
                ai_crop_success=r.get("ai_crop_success", False),
                heuristic_crop_success=r.get("heuristic_crop_success", False),
                ai_confidence=ai_confidence,
                ai_intent=comparison.get("ai_intent"),
                ai_reason=comparison.get("ai_reason"),
                error=r.get("ai_error") or r.get("heuristic_error")
            ))
        
        return VerificationSuiteResponse(
            total_urls=len(results),
            ai_success_count=sum(1 for r in results if r.ai_crop_success),
            heuristic_success_count=sum(1 for r in results if r.heuristic_crop_success),
            high_confidence_count=high_confidence_count,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Verification suite failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )


@router.get("/cache-stats", response_model=CacheStatsResponse)
def get_cache_statistics(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get cache statistics for monitoring.
    
    Admin only.
    """
    from backend.services.preview_cache import get_cache_stats
    
    stats = get_cache_stats()
    return CacheStatsResponse(**stats)


@router.post("/invalidate-cache")
def invalidate_url_cache(
    request: DebugComparisonRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Invalidate cache for a specific URL.
    
    Admin only. Use when preview needs to be regenerated.
    """
    from backend.services.preview_cache import invalidate_cache
    
    success = invalidate_cache(request.url)
    return {"success": success, "url": request.url}


@router.get("/fallback-order")
def get_fallback_order(
    current_user: User = Depends(get_admin_user)
):
    """
    Get the current fallback order configuration.
    
    Returns the explicit, deterministic fallback order used when
    AI analysis fails or returns low confidence.
    """
    from backend.jobs.screenshot_generation import FALLBACK_ORDER
    from backend.services.ai_visual_focus import FocusConfig
    
    return {
        "fallback_order": FALLBACK_ORDER,
        "confidence_thresholds": {
            "high": FocusConfig.HIGH_CONFIDENCE_THRESHOLD,
            "relaxed": FocusConfig.RELAXED_CONFIDENCE_THRESHOLD
        },
        "timeouts": {
            "ai_call_seconds": FocusConfig.AI_CALL_TIMEOUT,
            "total_processing_seconds": FocusConfig.TOTAL_PROCESSING_TIMEOUT
        },
        "retries": {
            "max_attempts": FocusConfig.MAX_RETRIES,
            "delay_seconds": FocusConfig.RETRY_DELAY
        }
    }


@router.get("/supported-intents")
def get_supported_intents(
    current_user: User = Depends(get_admin_user)
):
    """
    Get supported page intent types and their crop strategies.
    """
    from backend.services.ai_visual_focus import PageIntent, get_crop_strategy
    
    intents = {}
    for intent in PageIntent:
        strategy = get_crop_strategy(intent)
        intents[intent.value] = {
            "description": strategy.get("description", ""),
            "priority_elements": strategy.get("priority_elements", []),
            "prefer_region": strategy.get("prefer_region", "")
        }
    
    return {"intents": intents}

