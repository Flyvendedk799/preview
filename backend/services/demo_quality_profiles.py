"""Shared quality profile selection for demo preview generation."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qsl, urlparse


@dataclass(frozen=True)
class DemoQualityProfile:
    quality_mode: str
    multi_agent: bool
    ui_extraction: bool
    threshold: float
    iterations: int
    allow_soft_pass: bool
    enforce_target_quality: bool
    min_soft_pass_overall: float
    min_soft_pass_visual: float
    min_soft_pass_fidelity: float


_QUALITY_PROFILES: dict[str, DemoQualityProfile] = {
    "fast": DemoQualityProfile(
        quality_mode="fast",
        multi_agent=False,
        ui_extraction=False,
        threshold=0.78,
        iterations=2,
        allow_soft_pass=True,
        enforce_target_quality=False,
        min_soft_pass_overall=0.66,
        min_soft_pass_visual=0.52,
        min_soft_pass_fidelity=0.50,
    ),
    "balanced": DemoQualityProfile(
        quality_mode="balanced",
        multi_agent=True,
        ui_extraction=True,
        threshold=0.82,
        iterations=3,
        allow_soft_pass=True,
        enforce_target_quality=False,
        min_soft_pass_overall=0.74,
        min_soft_pass_visual=0.62,
        min_soft_pass_fidelity=0.60,
    ),
    "ultra": DemoQualityProfile(
        quality_mode="ultra",
        multi_agent=True,
        ui_extraction=True,
        threshold=0.88,
        iterations=4,
        allow_soft_pass=False,
        enforce_target_quality=True,
        min_soft_pass_overall=0.85,
        min_soft_pass_visual=0.75,
        min_soft_pass_fidelity=0.72,
    ),
}


def resolve_quality_mode(requested_mode: str | None, url: str | None = None) -> str:
    """Resolve requested mode to one of fast/balanced/ultra with auto fallback."""
    normalized = (requested_mode or "auto").strip().lower()
    if normalized in _QUALITY_PROFILES:
        return normalized
    if normalized != "auto":
        return "ultra"
    complexity = estimate_url_complexity(url or "")
    if complexity >= 8:
        return "ultra"
    if complexity >= 4:
        return "balanced"
    return "fast"


def get_quality_profile(requested_mode: str | None, url: str | None = None) -> DemoQualityProfile:
    resolved_mode = resolve_quality_mode(requested_mode, url=url)
    return _QUALITY_PROFILES[resolved_mode]


def get_cache_prefix_for_mode(requested_mode: str | None, url: str | None = None) -> str:
    resolved_mode = resolve_quality_mode(requested_mode, url=url)
    return f"demo:preview:v3:{resolved_mode}:"


def estimate_url_complexity(url: str) -> int:
    """
    Lightweight heuristic to pick a quality profile before heavy processing starts.

    Higher scores indicate pages that typically need deeper extraction and iteration.
    """
    if not url:
        return 6
    parsed = urlparse(url)
    score = 0

    path = (parsed.path or "").lower()
    path_parts = [segment for segment in path.split("/") if segment]
    depth = len(path_parts)
    score += min(depth, 4)

    query_count = len(parse_qsl(parsed.query or "", keep_blank_values=True))
    if query_count >= 3:
        score += 2
    elif query_count > 0:
        score += 1

    long_path_bonus = 1 if len(path) > 28 else 0
    score += long_path_bonus

    high_complexity_tokens = {
        "pricing",
        "features",
        "product",
        "products",
        "solutions",
        "platform",
        "integrations",
        "compare",
        "comparison",
        "enterprise",
        "developer",
        "docs",
        "documentation",
        "blog",
        "case-study",
        "customers",
    }
    medium_complexity_tokens = {"about", "services", "service", "category", "search"}

    for token in path_parts:
        if token in high_complexity_tokens:
            score += 2
        elif token in medium_complexity_tokens:
            score += 1

    if parsed.fragment:
        score += 1

    return min(score, 12)
