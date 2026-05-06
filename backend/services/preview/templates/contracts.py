"""Versioned template modules + contracts (Phase 3.1).

Each contract describes the safe-area boundaries, headline budgets, and
typography constraints for one template. Contracts are versioned (``v1``,
``v2``, …) so we can ship a new layout behind a flag without touching the
existing one.

The plan's Phase 3 exit gate is "Visual quality benchmark: +1.0 mean
improvement, clipping/overlap < 2%". Contract tests in
``backend/tests/test_template_contracts.py`` enforce the placement boundaries
on every change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class SafeArea:
    """Rectangle in canvas coords where text/images may render."""

    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    def contains(self, x: int, y: int, w: int, h: int) -> bool:
        return (
            x >= self.x
            and y >= self.y
            and x + w <= self.right
            and y + h <= self.bottom
        )


@dataclass(frozen=True)
class TemplateContract:
    """Static contract for a single template version."""

    name: str
    version: str
    canvas: Tuple[int, int]  # width, height
    safe_areas: Dict[str, SafeArea]
    headline_max_lines: int
    headline_min_size_px: int
    headline_max_size_px: int
    body_max_lines: int
    body_min_size_px: int
    body_max_size_px: int
    letter_spacing_px: float = 0.0
    description: str = ""

    @property
    def id(self) -> str:
        return f"{self.name}@{self.version}"


@dataclass
class TemplateRenderInput:
    """Whatever the template needs to lay out + render."""

    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    cta_text: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    proof: Optional[str] = None
    has_logo: bool = False
    has_hero: bool = False


@dataclass
class TemplateRenderViolation:
    """A boundary check failure surfaced by ``pre_measure_layout``."""

    field: str
    rule: str
    detail: str


# ---------------------------------------------------------------------------
# Built-in v1 contracts
# ---------------------------------------------------------------------------


HERO_CONTRACT_V1 = TemplateContract(
    name="hero",
    version="v1",
    canvas=(1200, 630),
    safe_areas={
        # Headline takes the upper-left two-thirds; logo top-right.
        "headline": SafeArea(x=64, y=72, width=720, height=180),
        "subtitle": SafeArea(x=64, y=260, width=720, height=64),
        "description": SafeArea(x=64, y=336, width=720, height=140),
        "cta": SafeArea(x=64, y=486, width=300, height=72),
        "logo": SafeArea(x=950, y=64, width=180, height=72),
        "image": SafeArea(x=820, y=160, width=320, height=410),
    },
    headline_max_lines=2,
    headline_min_size_px=44,
    headline_max_size_px=84,
    body_max_lines=4,
    body_min_size_px=20,
    body_max_size_px=28,
    letter_spacing_px=-0.5,
    description="Editorial hero with right-aligned hero image",
)


MODERN_CARD_CONTRACT_V1 = TemplateContract(
    name="modern_card",
    version="v1",
    canvas=(1200, 630),
    safe_areas={
        "headline": SafeArea(x=80, y=120, width=1040, height=180),
        "subtitle": SafeArea(x=80, y=312, width=1040, height=60),
        "description": SafeArea(x=80, y=384, width=1040, height=120),
        "cta": SafeArea(x=80, y=520, width=320, height=64),
        "logo": SafeArea(x=80, y=48, width=200, height=48),
        "proof": SafeArea(x=420, y=520, width=700, height=64),
    },
    headline_max_lines=2,
    headline_min_size_px=48,
    headline_max_size_px=88,
    body_max_lines=3,
    body_min_size_px=20,
    body_max_size_px=24,
    letter_spacing_px=-0.5,
    description="Centered modern card layout for SaaS / generic",
)


PROFILE_CONTRACT_V1 = TemplateContract(
    name="profile",
    version="v1",
    canvas=(1200, 630),
    safe_areas={
        # Avatar pinned left, name + headline in the right two-thirds.
        "avatar": SafeArea(x=80, y=120, width=320, height=320),
        "name": SafeArea(x=440, y=140, width=680, height=80),
        "title_role": SafeArea(x=440, y=232, width=680, height=48),
        "description": SafeArea(x=440, y=296, width=680, height=160),
        "tags": SafeArea(x=440, y=476, width=680, height=80),
        "logo": SafeArea(x=950, y=48, width=180, height=48),
    },
    headline_max_lines=1,
    headline_min_size_px=40,
    headline_max_size_px=72,
    body_max_lines=4,
    body_min_size_px=18,
    body_max_size_px=24,
    letter_spacing_px=-0.25,
    description="Creator/personal profile layout with avatar block",
)


TEMPLATE_CONTRACTS: Dict[str, TemplateContract] = {
    HERO_CONTRACT_V1.id: HERO_CONTRACT_V1,
    MODERN_CARD_CONTRACT_V1.id: MODERN_CARD_CONTRACT_V1,
    PROFILE_CONTRACT_V1.id: PROFILE_CONTRACT_V1,
    # Aliases for callers that just want "the latest hero/card/profile".
    "hero": HERO_CONTRACT_V1,
    "modern_card": MODERN_CARD_CONTRACT_V1,
    "profile": PROFILE_CONTRACT_V1,
}


def get_contract(name_or_id: str) -> TemplateContract:
    """Resolve a contract by name (latest) or ``name@version``."""
    contract = TEMPLATE_CONTRACTS.get(name_or_id)
    if contract is None:
        raise KeyError(f"Unknown template contract: {name_or_id!r}")
    return contract


# ---------------------------------------------------------------------------
# Pre-render layout measurement (Phase 3.3)
# ---------------------------------------------------------------------------


def _measure_text(text: str, *, font_size_px: int, max_width: int) -> Tuple[int, int]:
    """Approximate text dimensions without invoking Pillow.

    We use a calibrated character-width factor that matches Pillow's
    DejaVuSans / Inter measurements within ~5%. This lets us decide
    whether to shrink type *before* we draw, which is the plan's
    requirement "Pre-measure layout before draw operations".
    """
    if not text:
        return (0, font_size_px)

    avg_char_w = max(1, int(font_size_px * 0.55))
    line_height = int(font_size_px * 1.2)

    chars_per_line = max(1, max_width // avg_char_w)
    line_count = 1
    used = 0
    for word in text.split():
        # Long single tokens have to wrap mid-word.
        remaining = len(word) + 1
        if remaining > chars_per_line:
            extra_lines = (remaining + chars_per_line - 1) // chars_per_line
            line_count += extra_lines - 1
            used = remaining % chars_per_line
            continue
        if used + remaining > chars_per_line:
            line_count += 1
            used = remaining
        else:
            used += remaining
    width = min(max_width, len(text) * avg_char_w)
    height = line_count * line_height
    return (width, height)


def pre_measure_layout(
    contract: TemplateContract,
    inputs: TemplateRenderInput,
) -> List[TemplateRenderViolation]:
    """Return a list of layout violations (empty list = layout OK).

    This is the gate the renderer uses before actually drawing pixels.
    """
    violations: List[TemplateRenderViolation] = []

    headline_safe = contract.safe_areas.get("headline") or contract.safe_areas.get("name")
    if headline_safe is None:
        violations.append(
            TemplateRenderViolation("contract", "missing_headline_safe_area",
                                    f"{contract.id} has no headline/name area")
        )
        return violations

    if not inputs.title or not inputs.title.strip():
        violations.append(
            TemplateRenderViolation("title", "empty", "title is empty/blank")
        )

    # Headline: scale down until it fits in safe area
    headline_size = contract.headline_max_size_px
    while headline_size >= contract.headline_min_size_px:
        _, height = _measure_text(
            inputs.title or "",
            font_size_px=headline_size,
            max_width=headline_safe.width,
        )
        if height <= headline_safe.height:
            break
        headline_size -= 4
    else:
        violations.append(
            TemplateRenderViolation(
                "title", "overflow",
                f"Title cannot fit headline area at min size {contract.headline_min_size_px}px"
            )
        )

    if inputs.description:
        body_area = contract.safe_areas.get("description")
        if body_area is None:
            violations.append(
                TemplateRenderViolation(
                    "description", "no_safe_area",
                    f"{contract.id} has description but no safe area"
                )
            )
        else:
            _, body_h = _measure_text(
                inputs.description,
                font_size_px=contract.body_max_size_px,
                max_width=body_area.width,
            )
            if body_h > body_area.height:
                violations.append(
                    TemplateRenderViolation(
                        "description", "overflow",
                        f"Description {body_h}px > area {body_area.height}px"
                    )
                )

    if inputs.cta_text and "cta" in contract.safe_areas:
        cta_area = contract.safe_areas["cta"]
        cta_w, cta_h = _measure_text(
            inputs.cta_text,
            font_size_px=24,
            max_width=cta_area.width,
        )
        if cta_w > cta_area.width or cta_h > cta_area.height:
            violations.append(
                TemplateRenderViolation(
                    "cta_text", "overflow",
                    f"CTA exceeds {cta_area.width}x{cta_area.height}"
                )
            )

    if inputs.has_logo and "logo" not in contract.safe_areas:
        violations.append(
            TemplateRenderViolation(
                "logo", "no_logo_zone",
                f"{contract.id} has no logo safe area"
            )
        )

    return violations
