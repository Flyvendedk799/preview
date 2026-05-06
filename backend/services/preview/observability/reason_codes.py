"""Reason-code taxonomy for terminal pipeline outcomes.

The plan requires every fallback branch to emit a reason code + reason detail
and every job to resolve terminally as ``finished`` or ``failed``. These
enums are the single source of truth used by ``JobTrace`` and surfaced in the
frontend error taxonomy (Phase 5).
"""

from __future__ import annotations

from enum import Enum


class TerminalStatus(str, Enum):
    """Plan invariant: every job ends in one of these terminal states."""

    FINISHED = "finished"
    FAILED = "failed"


class FailureReason(str, Enum):
    """Closed taxonomy for failure / fallback explanations.

    Backend pipelines must select one of these before terminating. The
    frontend (Phase 5) maps each to a user-facing message.
    """

    # External capture failures
    CAPTURE_TIMEOUT = "capture_timeout"
    CAPTURE_BLOCKED = "capture_blocked"
    CAPTURE_HTTP_ERROR = "capture_http_error"
    CAPTURE_NETWORK_ERROR = "capture_network_error"

    # Extraction failures
    EXTRACTION_LOW_CONFIDENCE = "extraction_low_confidence"
    EXTRACTION_INVALID_PAYLOAD = "extraction_invalid_payload"
    EXTRACTION_AI_RATE_LIMIT = "extraction_ai_rate_limit"
    EXTRACTION_AI_AUTH = "extraction_ai_auth"
    EXTRACTION_AI_TIMEOUT = "extraction_ai_timeout"

    # Composition / rendering
    RENDER_FONT_FALLBACK = "render_font_fallback"
    RENDER_PALETTE_FALLBACK = "render_palette_fallback"
    RENDER_CONTRAST_FAILED = "render_contrast_failed"
    RENDER_LAYOUT_OVERFLOW = "render_layout_overflow"
    RENDER_IMAGE_PIPELINE_ERROR = "render_image_pipeline_error"

    # Quality gate
    QUALITY_GATE_FAILED = "quality_gate_failed"
    QUALITY_BUDGET_EXCEEDED = "quality_budget_exceeded"

    # Status / transient
    STATUS_CHECK_TRANSIENT = "status_check_transient"

    # Catch-all (must be rare; tracked as a metric in Phase 7)
    UNKNOWN = "unknown"

    @property
    def user_message(self) -> str:
        """Default copy surfaced to the frontend (overridable per-locale)."""
        return _USER_MESSAGES.get(self, "Something went wrong generating your preview.")


_USER_MESSAGES = {
    FailureReason.CAPTURE_TIMEOUT:
        "The page took too long to load. We'll retry with a simpler capture.",
    FailureReason.CAPTURE_BLOCKED:
        "The site blocked our preview crawler. Try a public URL or contact us.",
    FailureReason.CAPTURE_HTTP_ERROR:
        "The page responded with an error. Double-check the URL and try again.",
    FailureReason.CAPTURE_NETWORK_ERROR:
        "We couldn't reach the page. Check the URL and try again.",
    FailureReason.EXTRACTION_LOW_CONFIDENCE:
        "We couldn't read enough from the page to build a preview.",
    FailureReason.EXTRACTION_INVALID_PAYLOAD:
        "The page returned content we couldn't parse. We'll try a fallback.",
    FailureReason.EXTRACTION_AI_RATE_LIMIT:
        "Our AI provider rate-limited us. Please retry in a moment.",
    FailureReason.EXTRACTION_AI_AUTH:
        "Authentication issue with the AI provider — engineering is on it.",
    FailureReason.EXTRACTION_AI_TIMEOUT:
        "AI analysis timed out. We'll show a structured fallback.",
    FailureReason.RENDER_FONT_FALLBACK:
        "We rendered the preview with a fallback font.",
    FailureReason.RENDER_PALETTE_FALLBACK:
        "We rendered the preview with a fallback palette.",
    FailureReason.RENDER_CONTRAST_FAILED:
        "We adjusted text contrast to keep the preview readable.",
    FailureReason.RENDER_LAYOUT_OVERFLOW:
        "We trimmed text that would have overflowed the preview.",
    FailureReason.RENDER_IMAGE_PIPELINE_ERROR:
        "Image rendering hit an error — we used the screenshot as a fallback.",
    FailureReason.QUALITY_GATE_FAILED:
        "Quality didn't meet our bar so we shipped a safe fallback.",
    FailureReason.QUALITY_BUDGET_EXCEEDED:
        "We hit our time budget and shipped the best result we had.",
    FailureReason.STATUS_CHECK_TRANSIENT:
        "Status check hiccup — refresh in a moment.",
    FailureReason.UNKNOWN:
        "Something went wrong generating your preview.",
}


class PaletteSource(str, Enum):
    """Per-job palette provenance, required by the plan's trace schema."""

    SAMPLED = "sampled"
    DERIVED = "derived"
    DEFAULT = "default"


class PreviewLane(str, Enum):
    """Phase 6 — Dual-lane orchestration."""

    FAST = "fast"
    DEEP = "deep"
