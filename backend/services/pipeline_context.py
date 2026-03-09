"""
Pipeline Context - Unified request context that flows through all generation stages.

This is the connective tissue of the preview pipeline. Every stage receives
and enriches the same PipelineContext, providing:
- Request tracing (request_id propagated everywhere)
- Time budget enforcement (stages respect remaining time)
- Stage telemetry (automatic timing per stage)
- Accumulated diagnostics (warnings, errors, quality signals)
- Progress tracking (unified callback abstraction)

Usage:
    ctx = PipelineContext.create(url="https://example.com", is_demo=True)
    with ctx.stage("capture") as stage:
        screenshot = capture_screenshot(url)
        stage.set_output("screenshot_bytes", len(screenshot))
    # ctx.timings["capture"] is now populated
    # ctx.remaining_budget() reflects elapsed time
"""

import time
import logging
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from backend.services.graceful_degradation import TimeoutBudget, OpenAICircuitBreaker, QualityTier

logger = logging.getLogger(__name__)


@dataclass
class StageResult:
    """Telemetry for a single pipeline stage."""
    name: str
    started_at: float = 0.0
    finished_at: float = 0.0
    duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    outputs: Dict[str, Any] = field(default_factory=dict)
    skipped: bool = False
    skip_reason: Optional[str] = None


class StageTimer:
    """Context manager that tracks a single stage's execution."""

    def __init__(self, ctx: 'PipelineContext', name: str):
        self._ctx = ctx
        self._name = name
        self._result = StageResult(name=name)

    def set_output(self, key: str, value: Any):
        self._result.outputs[key] = value

    def skip(self, reason: str):
        self._result.skipped = True
        self._result.skip_reason = reason
        self._result.success = True

    def __enter__(self):
        self._result.started_at = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._result.finished_at = time.time()
        self._result.duration_ms = (self._result.finished_at - self._result.started_at) * 1000

        if exc_type is not None:
            self._result.success = False
            self._result.error = str(exc_val)

        self._ctx._record_stage(self._result)
        return False  # Don't suppress exceptions


@dataclass
class PipelineContext:
    """
    Unified context that flows through all pipeline stages.

    Created once at the start of generate(), passed to every sub-service,
    and used to build the final telemetry summary.
    """
    request_id: str = ""
    url: str = ""
    is_demo: bool = False
    start_time: float = 0.0

    # Time budget enforcement
    budget: Optional[TimeoutBudget] = None

    # Circuit breaker reference (singleton, shared across requests)
    circuit_breaker: Optional[OpenAICircuitBreaker] = None

    # Quality tracking
    current_tier: QualityTier = QualityTier.TIER_1_FULL
    quality_scores: Dict[str, float] = field(default_factory=dict)

    # Stage telemetry
    stages: List[StageResult] = field(default_factory=list)
    _stage_order: List[str] = field(default_factory=list)

    # Diagnostics
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Progress callback
    _progress_callback: Optional[Callable[[float, str], None]] = None
    _last_progress: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    # Shared data between stages (avoids re-computation)
    shared: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        url: str,
        is_demo: bool = False,
        total_budget_seconds: float = 60.0,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> 'PipelineContext':
        """Create a new pipeline context for a generation request."""
        return cls(
            request_id=str(uuid4())[:12],
            url=url,
            is_demo=is_demo,
            start_time=time.time(),
            budget=TimeoutBudget(total_budget_seconds),
            circuit_breaker=OpenAICircuitBreaker.get_instance(),
            _progress_callback=progress_callback,
        )

    # -- Time budget ----------------------------------------------------------

    def remaining_budget(self) -> float:
        """Seconds remaining in the total time budget."""
        if self.budget:
            return self.budget.remaining()
        return 999.0

    def stage_budget(self, stage_name: str) -> float:
        """Get the allocated budget for a specific stage."""
        if self.budget:
            return self.budget.stage_budget(stage_name)
        return 30.0

    def is_expired(self) -> bool:
        if self.budget:
            return self.budget.is_expired()
        return False

    # -- Circuit breaker ------------------------------------------------------

    def ai_available(self) -> bool:
        """Check if AI services are available (circuit breaker closed)."""
        if self.circuit_breaker:
            return not self.circuit_breaker.is_open()
        return True

    def record_ai_success(self):
        if self.circuit_breaker:
            self.circuit_breaker.record_success()

    def record_ai_error(self):
        if self.circuit_breaker:
            self.circuit_breaker.record_error()

    # -- Stage tracking -------------------------------------------------------

    def stage(self, name: str) -> StageTimer:
        """Create a stage timer context manager.

        Usage:
            with ctx.stage("capture") as s:
                result = do_work()
                s.set_output("bytes", len(result))
        """
        return StageTimer(self, name)

    def _record_stage(self, result: StageResult):
        with self._lock:
            self.stages.append(result)
            self._stage_order.append(result.name)

            if not result.success and result.error:
                self.errors.append(f"[{result.name}] {result.error}")

            level = "SKIP" if result.skipped else ("OK" if result.success else "FAIL")
            logger.info(
                f"[{self.request_id}] stage={result.name} "
                f"status={level} "
                f"duration={result.duration_ms:.0f}ms"
            )

    # -- Progress -------------------------------------------------------------

    def update_progress(self, progress: float, message: str):
        """Update progress monotonically."""
        with self._lock:
            clamped = max(0.0, min(1.0, progress))
            if clamped < self._last_progress:
                return  # Never go backwards
            self._last_progress = clamped

        if self._progress_callback:
            try:
                self._progress_callback(clamped, message)
            except Exception:
                pass  # Never let progress callback kill the pipeline

    # -- Diagnostics ----------------------------------------------------------

    def warn(self, message: str):
        self.warnings.append(message)
        logger.warning(f"[{self.request_id}] {message}")

    def add_quality_score(self, name: str, score: float):
        self.quality_scores[name] = score

    # -- Summary --------------------------------------------------------------

    def elapsed_ms(self) -> int:
        return int((time.time() - self.start_time) * 1000)

    def telemetry_summary(self) -> Dict[str, Any]:
        """Build a telemetry dict for logging / tracing."""
        return {
            "request_id": self.request_id,
            "url": self.url[:80],
            "is_demo": self.is_demo,
            "total_ms": self.elapsed_ms(),
            "budget_remaining_s": round(self.remaining_budget(), 1),
            "tier": self.current_tier.value,
            "stages": {
                s.name: {
                    "ms": round(s.duration_ms),
                    "ok": s.success,
                    "skipped": s.skipped,
                }
                for s in self.stages
            },
            "quality": self.quality_scores,
            "warnings": len(self.warnings),
            "errors": len(self.errors),
        }
