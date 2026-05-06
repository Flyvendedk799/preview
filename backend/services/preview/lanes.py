"""Phase 6 — Dual-lane orchestration + per-job budgets.

The plan describes:
  - Fast lane for simple pages (reduced agent set)
  - Deep lane for complex pages (full analysis)
  - Per-job AI-token + stage-duration budgets
  - Early exit when confidence thresholds are satisfied
  - Hard timeout + graceful fallback for screenshot capture

This module exposes:
  - ``select_lane`` — decision function with explainable signals
  - ``LaneBudget`` — token/time budgets per lane
  - ``screenshot_capture_with_timeout`` — hard timeout + fallback hook
  - ``early_exit_threshold`` — confidence cutoff helper
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from backend.services.preview.observability.reason_codes import (
    FailureReason,
    PreviewLane,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lane selection
# ---------------------------------------------------------------------------


@dataclass
class LaneDecision:
    lane: PreviewLane
    reason: str
    signals: Dict[str, Any] = field(default_factory=dict)


def select_lane(
    *,
    has_rich_og_metadata: bool,
    html_size_bytes: int,
    is_demo: bool,
    is_ecommerce: bool = False,
    page_classification_confidence: Optional[float] = None,
) -> LaneDecision:
    """Pick the orchestration lane.

    The fast lane runs when the page is content-rich and our cheap signals
    already give us enough to populate a great preview. The deep lane runs
    when we need the full multi-agent pass to recover.
    """
    signals: Dict[str, Any] = {
        "rich_og": has_rich_og_metadata,
        "html_size": html_size_bytes,
        "is_demo": is_demo,
        "is_ecommerce": is_ecommerce,
        "classification_confidence": page_classification_confidence,
    }

    if is_ecommerce:
        return LaneDecision(
            PreviewLane.DEEP,
            reason="ecommerce_pages_use_deep_lane",
            signals=signals,
        )

    if has_rich_og_metadata and html_size_bytes < 800_000:
        return LaneDecision(
            PreviewLane.FAST,
            reason="og_rich_and_html_small",
            signals=signals,
        )

    if (
        page_classification_confidence is not None
        and page_classification_confidence >= 0.85
        and has_rich_og_metadata
    ):
        return LaneDecision(
            PreviewLane.FAST,
            reason="high_classification_confidence_and_og",
            signals=signals,
        )

    return LaneDecision(
        PreviewLane.DEEP,
        reason="needs_full_analysis",
        signals=signals,
    )


# ---------------------------------------------------------------------------
# Budgets
# ---------------------------------------------------------------------------


@dataclass
class LaneBudget:
    lane: PreviewLane
    max_ai_tokens: int
    max_stage_seconds: Dict[str, float]
    max_total_seconds: float
    early_exit_confidence: float

    def stage_budget(self, name: str) -> float:
        return self.max_stage_seconds.get(name, self.max_total_seconds * 0.4)


FAST_LANE_BUDGET = LaneBudget(
    lane=PreviewLane.FAST,
    max_ai_tokens=4_000,
    max_stage_seconds={
        "capture": 8.0,
        "classify": 2.0,
        "extract": 6.0,
        "analyze": 5.0,
        "compose": 5.0,
        "quality": 3.0,
    },
    max_total_seconds=22.0,
    early_exit_confidence=0.78,
)


DEEP_LANE_BUDGET = LaneBudget(
    lane=PreviewLane.DEEP,
    max_ai_tokens=14_000,
    max_stage_seconds={
        "capture": 15.0,
        "classify": 5.0,
        "extract": 18.0,
        "analyze": 22.0,
        "compose": 18.0,
        "quality": 12.0,
    },
    max_total_seconds=70.0,
    early_exit_confidence=0.88,
)


def budget_for(lane: PreviewLane) -> LaneBudget:
    return DEEP_LANE_BUDGET if lane == PreviewLane.DEEP else FAST_LANE_BUDGET


def early_exit_threshold(lane: PreviewLane) -> float:
    return budget_for(lane).early_exit_confidence


# ---------------------------------------------------------------------------
# Screenshot capture hardening (Phase 6 final bullet)
# ---------------------------------------------------------------------------


@dataclass
class CaptureFallback:
    """What to return when screenshot capture times out / fails."""

    reason: FailureReason
    detail: str
    placeholder_screenshot: bytes
    placeholder_html: str = ""


def screenshot_capture_with_timeout(
    capture_fn: Callable[[str], Any],
    url: str,
    *,
    timeout_seconds: float,
    on_fallback: Optional[Callable[[CaptureFallback], Any]] = None,
) -> Any:
    """Run a sync ``capture_fn`` under a hard timeout with graceful fallback.

    The plan demands "Hard timeout + graceful fallback path for screenshot
    capture". This wrapper enforces that without leaking threads.
    """
    started = time.time()
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="capture") as executor:
        future = executor.submit(capture_fn, url)
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeoutError:
            future.cancel()
            elapsed = time.time() - started
            fallback = CaptureFallback(
                reason=FailureReason.CAPTURE_TIMEOUT,
                detail=f"capture exceeded {timeout_seconds:.1f}s (took {elapsed:.1f}s)",
                placeholder_screenshot=_blank_png(1200, 630),
            )
            if on_fallback is not None:
                return on_fallback(fallback)
            raise TimeoutError(fallback.detail)


def _blank_png(width: int, height: int) -> bytes:
    """Produce a minimal solid-gray PNG without requiring Pillow at import time."""
    try:
        from PIL import Image
        from io import BytesIO

        image = Image.new("RGB", (width, height), color=(240, 240, 240))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception:  # noqa: BLE001 — last-resort literal PNG header
        # 1x1 gray PNG (84 bytes); the renderer can upscale.
        return bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108020000"
            "0090775388000000017352474200aece1ce90000000970485973"
            "0000004700000047000005b81f6500000010744558745469746c65"
            "626c616e6b2e706e6730e94db90000000c4944415478da63f0c0c0c0"
            "0000020001a17f44f10000000049454e44ae426082"
        )


# ---------------------------------------------------------------------------
# Token accounting
# ---------------------------------------------------------------------------


@dataclass
class TokenLedger:
    used_input: int = 0
    used_output: int = 0
    calls: int = 0

    def record(self, input_tokens: int, output_tokens: int) -> None:
        self.used_input += int(input_tokens or 0)
        self.used_output += int(output_tokens or 0)
        self.calls += 1

    @property
    def total(self) -> int:
        return self.used_input + self.used_output

    def has_budget(self, budget: LaneBudget) -> bool:
        return self.total < budget.max_ai_tokens
