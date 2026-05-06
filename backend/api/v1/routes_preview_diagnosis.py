"""Phase 2 / Phase 7 — JobTrace diagnosis API.

Internal admin-only endpoints that surface the structured per-job trace
described in ``DEMO_PREVIEW_ENGINE_FINAL_PLAN.md``. The frontend regression
dashboard polls these endpoints to render the metric trend charts.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.core.deps import get_admin_user  # type: ignore
from backend.models.user import User  # type: ignore
from backend.services.preview.observability.diagnosis import (
    diagnose,
    diagnose_job,
)
from backend.services.preview.observability.job_trace import JobTraceStore
from backend.services.preview.observability.reason_codes import FailureReason


router = APIRouter(prefix="/preview-diagnosis", tags=["preview-diagnosis"])


class DiagnosisResponse(BaseModel):
    job_id: Optional[str]
    url: Optional[str]
    verdict: str
    terminal_status: Optional[str]
    failure_reason: Optional[str]
    failure_detail: Optional[str]
    lane: Optional[str]
    template: Optional[str]
    palette_source: Optional[str]
    retry_count: int = 0
    extraction_confidence: Optional[float] = None
    quality_subscores: Dict[str, Any] = {}
    visual_quality: Dict[str, Any] = {}
    total_ms: Optional[int] = None
    ai_tokens_total: Optional[int] = None
    ai_call_count: Optional[int] = None
    bottleneck_stage: Optional[Dict[str, Any]] = None
    warnings: List[str] = []


@router.get("/jobs/{job_id}", response_model=DiagnosisResponse)
def diagnose_job_route(
    job_id: str,
    _admin: User = Depends(get_admin_user),
) -> DiagnosisResponse:
    diag = diagnose_job(job_id)
    if diag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return DiagnosisResponse(**diag)


@router.get("/recent")
def recent_jobs_route(
    limit: int = Query(default=25, ge=1, le=200),
    _admin: User = Depends(get_admin_user),
) -> Dict[str, Any]:
    store = JobTraceStore.get_instance()
    payloads = store.list_recent(limit=limit)
    return {
        "jobs": [diagnose(p) for p in payloads],
        "count": len(payloads),
    }


@router.get("/failure-reasons")
def failure_reasons_route(
    _admin: User = Depends(get_admin_user),
) -> Dict[str, Dict[str, str]]:
    """Stable taxonomy + user-facing copy for the frontend."""
    return {
        reason.value: {
            "user_message": reason.user_message,
            "code": reason.value,
        }
        for reason in FailureReason
    }
