"""Developer-facing job diagnosis utility.

The plan exit gate for Phase 2 is:
"Any bad preview can be root-caused in <2 minutes from traces."

This module renders a JobTrace into a compact, human-readable diagnosis with
an explicit verdict (success / fallback / fail) and the smallest set of
signals needed to triage. The same data is exposed via API in
``backend/api/v1/preview_diagnosis.py`` (Phase 7).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.services.preview.observability.job_trace import (
    JobTrace,
    JobTraceStore,
)
from backend.services.preview.observability.reason_codes import (
    FailureReason,
    TerminalStatus,
)


def diagnose(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Reduce a trace payload to a triage view."""
    if not trace_payload:
        return {"verdict": "unknown", "reason": "trace_not_found"}

    terminal = trace_payload.get("terminal_status")
    failure_reason = trace_payload.get("failure_reason")
    retry_count = int(trace_payload.get("retry_count") or 0)
    palette_source = trace_payload.get("palette_source")
    template = trace_payload.get("template_selected")
    extraction_conf = trace_payload.get("extraction_confidence")
    quality = trace_payload.get("quality_subscores") or {}
    visual = trace_payload.get("visual_quality") or {}
    stages = trace_payload.get("stage_timings") or []

    if terminal == TerminalStatus.FINISHED.value and not failure_reason:
        verdict = "success"
    elif failure_reason and failure_reason != FailureReason.UNKNOWN.value:
        verdict = "fallback" if terminal == TerminalStatus.FINISHED.value else "fail"
    else:
        verdict = "unknown"

    bottleneck = _identify_bottleneck(stages)

    return {
        "job_id": trace_payload.get("job_id"),
        "url": trace_payload.get("url"),
        "verdict": verdict,
        "terminal_status": terminal,
        "failure_reason": failure_reason,
        "failure_detail": trace_payload.get("failure_detail"),
        "lane": trace_payload.get("lane"),
        "template": template,
        "palette_source": palette_source,
        "retry_count": retry_count,
        "extraction_confidence": extraction_conf,
        "quality_subscores": quality,
        "visual_quality": visual,
        "total_ms": trace_payload.get("total_ms"),
        "ai_tokens_total": int(trace_payload.get("ai_tokens_input", 0))
                           + int(trace_payload.get("ai_tokens_output", 0)),
        "ai_call_count": trace_payload.get("ai_call_count"),
        "bottleneck_stage": bottleneck,
        "warnings": trace_payload.get("warnings") or [],
    }


def _identify_bottleneck(stages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not stages:
        return None
    slowest = max(stages, key=lambda s: float(s.get("duration_ms") or 0))
    return {
        "name": slowest.get("name"),
        "duration_ms": int(slowest.get("duration_ms") or 0),
        "success": slowest.get("success", True),
    }


def diagnose_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Look up a job in the store and return its diagnosis."""
    payload = JobTraceStore.get_instance().get(job_id)
    if not payload:
        return None
    return diagnose(payload)


def diagnose_trace(trace: JobTrace) -> Dict[str, Any]:
    return diagnose(trace.to_dict())
