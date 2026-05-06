"""Structured per-job trace object.

Implements the trace schema from Phase 2 of the plan:

    job_id, url, start_ts, end_ts
    stage timings (capture/classify/extract/analyze/compose/quality)
    extraction confidence and quality-gate sub-scores
    template selected + rationale
    palette source (sampled, derived, default)
    retry_count + retry_deltas
    terminal status + reason code

The store is in-memory (LRU) by default; callers can plug in Redis or any
KV store via ``JobTraceStore.set_backend(...)``. The point is that every
trace is queryable for the developer "job diagnosis" utility called out by
the plan and for the nightly regression dashboard (Phase 7).
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from backend.services.preview.observability.reason_codes import (
    FailureReason,
    PaletteSource,
    PreviewLane,
    TerminalStatus,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stage timing
# ---------------------------------------------------------------------------


@dataclass
class StageTiming:
    """Single stage measurement embedded in the JobTrace."""

    name: str
    started_at: float
    finished_at: float
    duration_ms: float
    success: bool = True
    skipped: bool = False
    error: Optional[str] = None
    outputs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryDelta:
    """Diff between two retry attempts (Phase 1 invariant)."""

    attempt: int
    changed_fields: List[str]
    overall_score: Optional[float] = None
    suggestions: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# JobTrace
# ---------------------------------------------------------------------------


@dataclass
class JobTrace:
    """Trace for a single preview generation job (Phase 2 schema)."""

    job_id: str = field(default_factory=lambda: str(uuid4()))
    url: str = ""
    start_ts: float = field(default_factory=time.time)
    end_ts: Optional[float] = None
    is_demo: bool = False
    lane: Optional[PreviewLane] = None

    # Stage timings, keyed by stage name for O(1) lookup, list preserves order.
    stage_timings: List[StageTiming] = field(default_factory=list)

    # Quality + extraction signals
    extraction_confidence: Optional[float] = None
    quality_subscores: Dict[str, float] = field(default_factory=dict)
    visual_quality: Dict[str, float] = field(default_factory=dict)

    # Template + palette provenance
    template_selected: Optional[str] = None
    template_rationale: Optional[str] = None
    palette_source: Optional[PaletteSource] = None

    # Retry audit
    retry_count: int = 0
    retry_deltas: List[RetryDelta] = field(default_factory=list)

    # Terminal status
    terminal_status: Optional[TerminalStatus] = None
    failure_reason: Optional[FailureReason] = None
    failure_detail: Optional[str] = None

    # Token / cost accounting (Phase 6)
    ai_tokens_input: int = 0
    ai_tokens_output: int = 0
    ai_call_count: int = 0

    # Free-form notes (kept short)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    # ---- mutators -------------------------------------------------------

    def add_stage(self, timing: StageTiming) -> None:
        self.stage_timings.append(timing)

    def add_retry(self, delta: RetryDelta) -> None:
        self.retry_count = max(self.retry_count, delta.attempt)
        self.retry_deltas.append(delta)

    def record_ai_usage(self, input_tokens: int, output_tokens: int) -> None:
        self.ai_tokens_input += int(input_tokens or 0)
        self.ai_tokens_output += int(output_tokens or 0)
        self.ai_call_count += 1

    def finalize_success(self) -> None:
        self.end_ts = time.time()
        self.terminal_status = TerminalStatus.FINISHED

    def finalize_failure(
        self,
        reason: FailureReason,
        detail: Optional[str] = None,
    ) -> None:
        self.end_ts = time.time()
        self.terminal_status = TerminalStatus.FAILED
        self.failure_reason = reason
        if detail:
            self.failure_detail = detail[:500]

    # ---- accessors ------------------------------------------------------

    @property
    def total_ms(self) -> int:
        end = self.end_ts or time.time()
        return int((end - self.start_ts) * 1000)

    def stage_lookup(self) -> Dict[str, StageTiming]:
        return {t.name: t for t in self.stage_timings}

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Enum serialization
        if self.lane:
            d["lane"] = self.lane.value
        if self.palette_source:
            d["palette_source"] = self.palette_source.value
        if self.terminal_status:
            d["terminal_status"] = self.terminal_status.value
        if self.failure_reason:
            d["failure_reason"] = self.failure_reason.value
        d["total_ms"] = self.total_ms
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str, indent=2)


# ---------------------------------------------------------------------------
# Pluggable store
# ---------------------------------------------------------------------------


class _LRUStore:
    """Simple thread-safe LRU used as the default backend."""

    def __init__(self, max_entries: int = 1024):
        self._max = max_entries
        self._data: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        self._lock = threading.Lock()

    def put(self, job_id: str, payload: Dict[str, Any]) -> None:
        with self._lock:
            self._data[job_id] = payload
            self._data.move_to_end(job_id)
            while len(self._data) > self._max:
                self._data.popitem(last=False)

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            payload = self._data.get(job_id)
            if payload:
                self._data.move_to_end(job_id)
            return payload

    def list_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self._data.values())[-limit:]
            return list(reversed(items))


class JobTraceStore:
    """Persists and reads JobTrace objects.

    Default backend is an in-process LRU. Production callers can wire a
    Redis or BigQuery sink by providing a ``writer`` callable that accepts a
    ``Dict[str, Any]`` payload. The store still keeps the LRU mirror so the
    in-process diagnosis tool keeps working.
    """

    _instance: Optional["JobTraceStore"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._lru = _LRUStore()
        self._writer: Optional[Callable[[Dict[str, Any]], None]] = None
        self._reader: Optional[Callable[[str], Optional[Dict[str, Any]]]] = None

    @classmethod
    def get_instance(cls) -> "JobTraceStore":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def set_backend(
        self,
        writer: Optional[Callable[[Dict[str, Any]], None]] = None,
        reader: Optional[Callable[[str], Optional[Dict[str, Any]]]] = None,
    ) -> None:
        self._writer = writer
        self._reader = reader

    def save(self, trace: JobTrace) -> None:
        payload = trace.to_dict()
        self._lru.put(trace.job_id, payload)
        if self._writer is not None:
            try:
                self._writer(payload)
            except Exception as exc:  # noqa: BLE001 — never crash the pipeline
                logger.warning("JobTrace external writer failed: %s", exc)

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        if self._reader is not None:
            try:
                payload = self._reader(job_id)
                if payload is not None:
                    return payload
            except Exception as exc:  # noqa: BLE001
                logger.warning("JobTrace external reader failed: %s", exc)
        return self._lru.get(job_id)

    def list_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._lru.list_recent(limit=limit)


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------


def new_job_trace(
    url: str,
    is_demo: bool = False,
    job_id: Optional[str] = None,
    lane: Optional[PreviewLane] = None,
) -> JobTrace:
    """Create a JobTrace with sensible defaults."""
    trace = JobTrace(url=url, is_demo=is_demo, lane=lane)
    if job_id:
        trace.job_id = job_id
    return trace
