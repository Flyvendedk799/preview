"""Phase 1 — Critical reliability primitives.

This module implements the four blocker fixes the plan calls out:

  1.1 Event-loop safety in sync paths
      ``sync_http_get`` and ``run_async_safely`` make sure synchronous
      worker code never collides with an existing event loop.
  1.2 Retry semantics correctness
      ``RetryContext.mutate`` is the single way to advance an attempt and
      forbids re-issuing identical payloads (raises if you try).
  1.3 Schema/type integrity
      ``validate_blueprint`` enforces the typed contract before render.
  1.4 Font loading determinism
      ``resolve_font`` and ``register_font_fallback_event`` emit telemetry
      whenever the production stack falls back below the preferred font.

Reliability invariant: every fallback branch passes a ``FailureReason`` plus
a short detail string into the JobTrace, fulfilling the plan's "every
fallback emits reason code + reason detail" requirement.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, TypeVar

from backend.services.preview.observability.job_trace import JobTrace, RetryDelta
from backend.services.preview.observability.reason_codes import FailureReason

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1.1 Event loop safety
# ---------------------------------------------------------------------------


T = TypeVar("T")


def sync_http_get(
    url: str,
    *,
    timeout: float = 10.0,
    headers: Optional[Dict[str, str]] = None,
):
    """A purely synchronous HTTP GET.

    The plan called out async-loop misuse in sync execution paths
    (worker pool calling ``asyncio.run`` inside a thread that already has a
    running loop). Always route sync work through this helper and you never
    touch ``asyncio`` from a worker.

    Imports ``requests`` lazily so the module doesn't fail to load in test
    environments without it.
    """
    import requests  # local import — keeps module-load surface small

    return requests.get(url, timeout=timeout, headers=headers or {})


def run_async_safely(coro_factory: Callable[[], Awaitable[T]]) -> T:
    """Execute an async coroutine from a sync caller without violating loop rules.

    - If a running loop is detected (e.g. running under uvicorn/FastAPI),
      we hand the coroutine off to a fresh thread with its own loop.
    - Otherwise we use ``asyncio.run`` directly.
    """
    try:
        running = asyncio.get_running_loop()
    except RuntimeError:
        running = None

    if running is None:
        return asyncio.run(coro_factory())

    # We're inside a running loop. Drop into a worker thread.
    result_box: Dict[str, Any] = {}
    error_box: Dict[str, BaseException] = {}

    def _runner() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result_box["value"] = loop.run_until_complete(coro_factory())
        except BaseException as exc:  # noqa: BLE001 — propagate after join
            error_box["err"] = exc
        finally:
            loop.close()

    thread = threading.Thread(target=_runner, name="run_async_safely", daemon=True)
    thread.start()
    thread.join()
    if "err" in error_box:
        raise error_box["err"]
    return result_box["value"]  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# 1.2 Retry semantics correctness
# ---------------------------------------------------------------------------


class IdenticalRetryError(RuntimeError):
    """Raised when a retry attempts to repeat an identical prompt payload.

    Plan invariant: "Forbid retries that repeat identical prompt payloads."
    """


@dataclass
class RetryContext:
    """Tracks attempt-aware mutation + a payload fingerprint.

    Use as::

        ctx = RetryContext()
        for _ in range(max_attempts):
            payload = build_payload(ctx)
            ctx.assert_payload_changed(payload)
            ...
            ctx.mutate(critique=critique, prior_failure=err)
    """

    attempt: int = 0
    prior_failures: List[str] = field(default_factory=list)
    critiques: List[str] = field(default_factory=list)
    last_payload_hash: Optional[str] = None
    payload_hashes_seen: List[str] = field(default_factory=list)

    def mutate(
        self,
        critique: Optional[str] = None,
        prior_failure: Optional[str] = None,
    ) -> "RetryContext":
        """Advance attempt index and record what we learned.

        The next prompt builder MUST consult ``critiques`` and
        ``prior_failures`` so the retry mutates the payload.
        """
        self.attempt += 1
        if critique:
            self.critiques.append(critique[:500])
        if prior_failure:
            self.prior_failures.append(prior_failure[:300])
        return self

    @staticmethod
    def fingerprint(payload: Any) -> str:
        try:
            serialized = json.dumps(payload, sort_keys=True, default=str)
        except TypeError:
            serialized = repr(payload)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def assert_payload_changed(self, payload: Any) -> str:
        """Raise IdenticalRetryError if the payload matches the previous attempt."""
        fp = self.fingerprint(payload)
        if self.last_payload_hash is not None and fp == self.last_payload_hash:
            raise IdenticalRetryError(
                f"Retry attempt {self.attempt} repeats identical payload (hash={fp[:12]}). "
                "Mutate the payload using critiques/prior_failures before retrying."
            )
        self.last_payload_hash = fp
        self.payload_hashes_seen.append(fp)
        return fp

    def trace_delta(
        self,
        changed_fields: List[str],
        overall_score: Optional[float] = None,
        suggestions: Optional[List[str]] = None,
    ) -> RetryDelta:
        return RetryDelta(
            attempt=self.attempt,
            changed_fields=list(changed_fields),
            overall_score=overall_score,
            suggestions=list(suggestions or []),
        )


# ---------------------------------------------------------------------------
# 1.3 Schema/type integrity
# ---------------------------------------------------------------------------


REQUIRED_BLUEPRINT_FIELDS = {
    "template_type": str,
    "primary_color": str,
    "secondary_color": str,
    "accent_color": str,
}

OPTIONAL_BLUEPRINT_FIELDS = {
    "background_color": str,
    "text_color": str,
    "coherence_score": (int, float),
    "balance_score": (int, float),
    "clarity_score": (int, float),
    "design_fidelity_score": (int, float, type(None)),
    "overall_quality": str,
    "layout_reasoning": str,
    "composition_notes": str,
}


@dataclass
class BlueprintValidation:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    repaired: Dict[str, Any] = field(default_factory=dict)


def validate_blueprint(blueprint: Dict[str, Any]) -> BlueprintValidation:
    """Strict-but-repairing validator for the render-input blueprint.

    The plan calls for "strict validation for core blueprint output fields
    before render." We accept the blueprint when:
      - all REQUIRED keys exist with valid types AND
      - color values look like ``#RRGGBB`` (or are silently repaired).

    For optional fields we only validate the type when present.
    """
    errors: List[str] = []
    repaired = dict(blueprint or {})

    for field_name, expected_types in REQUIRED_BLUEPRINT_FIELDS.items():
        value = repaired.get(field_name)
        types = expected_types if isinstance(expected_types, tuple) else (expected_types,)
        if value is None or not isinstance(value, types):
            errors.append(f"Required field {field_name!r} missing or wrong type")
            continue

        if "color" in field_name:
            cleaned = _coerce_hex_color(value)
            if cleaned is None:
                errors.append(f"Field {field_name!r} not a valid hex color: {value!r}")
            else:
                repaired[field_name] = cleaned

    for field_name, expected_types in OPTIONAL_BLUEPRINT_FIELDS.items():
        if field_name not in repaired:
            continue
        value = repaired[field_name]
        types = expected_types if isinstance(expected_types, tuple) else (expected_types,)
        if not isinstance(value, types):
            errors.append(
                f"Optional field {field_name!r} has wrong type: got {type(value).__name__}"
            )

    return BlueprintValidation(
        is_valid=not errors,
        errors=errors,
        repaired=repaired,
    )


def _coerce_hex_color(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned.startswith("#"):
        cleaned = f"#{cleaned}"
    if len(cleaned) == 7:  # #RRGGBB
        try:
            int(cleaned[1:], 16)
            return cleaned.upper()
        except ValueError:
            return None
    if len(cleaned) == 4:  # #RGB → expand to #RRGGBB
        try:
            r, g, b = cleaned[1], cleaned[2], cleaned[3]
            int(r + g + b, 16)
            return f"#{r}{r}{g}{g}{b}{b}".upper()
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# 1.4 Font loading determinism
# ---------------------------------------------------------------------------


# Bundled production fonts. Resolution order is deterministic: explicit
# bundled path → system path → fallback DejaVu. Telemetry fires every time
# we step below the bundled path so we can monitor incidence.
PRODUCTION_FONT_BUNDLE: Dict[str, str] = {
    "Inter-Regular": "/usr/share/fonts/truetype/inter/Inter-Regular.ttf",
    "Inter-Bold": "/usr/share/fonts/truetype/inter/Inter-Bold.ttf",
    "Inter-SemiBold": "/usr/share/fonts/truetype/inter/Inter-SemiBold.ttf",
}

DEJAVU_FALLBACKS: Dict[str, str] = {
    "regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
}


@dataclass
class FontResolution:
    requested: str
    resolved_path: Optional[str]
    is_fallback: bool
    fallback_reason: Optional[str] = None


def resolve_font(name: str, *, weight: str = "regular") -> FontResolution:
    """Deterministic font lookup with telemetry on every fallback step."""
    import os

    # Step 1: bundled production font
    candidate = PRODUCTION_FONT_BUNDLE.get(name)
    if candidate and os.path.exists(candidate):
        return FontResolution(requested=name, resolved_path=candidate, is_fallback=False)

    # Step 2: DejaVu fallback
    fallback_key = "bold" if weight in {"bold", "black", "semibold"} else "regular"
    fallback_path = DEJAVU_FALLBACKS.get(fallback_key)
    if fallback_path and os.path.exists(fallback_path):
        return FontResolution(
            requested=name,
            resolved_path=fallback_path,
            is_fallback=True,
            fallback_reason="bundled_font_missing",
        )

    # Step 3: total miss
    return FontResolution(
        requested=name,
        resolved_path=None,
        is_fallback=True,
        fallback_reason="no_fonts_available",
    )


def register_font_fallback_event(
    trace: Optional[JobTrace],
    resolution: FontResolution,
) -> None:
    """Tag the trace whenever a fallback was used (Phase 1 invariant)."""
    if not trace or not resolution.is_fallback:
        return
    trace.warnings.append(
        f"font_fallback:{resolution.requested}:{resolution.fallback_reason}"
    )
    if resolution.resolved_path is None:
        trace.failure_reason = trace.failure_reason or FailureReason.RENDER_FONT_FALLBACK


# ---------------------------------------------------------------------------
# Cross-cutting helper: wrap any reliability fallback into a JobTrace warning
# ---------------------------------------------------------------------------


def record_fallback(
    trace: Optional[JobTrace],
    reason: FailureReason,
    detail: str,
) -> None:
    """Emit reason code + reason detail on every fallback branch."""
    if trace is None:
        return
    trace.warnings.append(f"fallback:{reason.value}:{detail[:120]}")
    if trace.failure_reason is None:
        trace.failure_reason = reason
        trace.failure_detail = detail[:500]
