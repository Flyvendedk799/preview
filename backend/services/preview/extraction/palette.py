"""Palette quality rules (Phase 4.3).

Plan requirements:
  - Increase screenshot sampling diversity.
  - Enforce minimum perceptual distance between primary/secondary/accent.
  - If near-duplicate colors, derive complementary/triadic accent
    programmatically.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

from backend.services.preview.observability.reason_codes import PaletteSource


RGB = Tuple[int, int, int]


# ---------------------------------------------------------------------------
# Color space conversions used for distance + harmony
# ---------------------------------------------------------------------------


def _hex_to_rgb(hex_str: str) -> RGB:
    cleaned = hex_str.lstrip("#")
    if len(cleaned) == 3:
        cleaned = "".join(c * 2 for c in cleaned)
    if len(cleaned) != 6:
        return (37, 99, 235)
    return (
        int(cleaned[0:2], 16),
        int(cleaned[2:4], 16),
        int(cleaned[4:6], 16),
    )


def _rgb_to_hex(rgb: RGB) -> str:
    return "#{:02X}{:02X}{:02X}".format(*[max(0, min(255, int(c))) for c in rgb])


def _rgb_to_hsl(rgb: RGB) -> Tuple[float, float, float]:
    r, g, b = [c / 255 for c in rgb]
    high = max(r, g, b)
    low = min(r, g, b)
    h = s = 0.0
    l = (high + low) / 2
    if high != low:
        d = high - low
        s = d / (2 - high - low) if l > 0.5 else d / (high + low)
        if high == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif high == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h /= 6
    return (h * 360, s, l)


def _hsl_to_rgb(h: float, s: float, l: float) -> RGB:
    h = (h % 360) / 360
    if s == 0:
        c = int(round(l * 255))
        return (c, c, c)

    def hue_to_rgb(p: float, q: float, t: float) -> float:
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    q = l + s - (l * s) if l < 0.5 else l + s - (l * s)
    p = 2 * l - q
    r = hue_to_rgb(p, q, h + 1 / 3)
    g = hue_to_rgb(p, q, h)
    b = hue_to_rgb(p, q, h - 1 / 3)
    return (int(r * 255), int(g * 255), int(b * 255))


def perceptual_distance(a: RGB, b: RGB) -> float:
    """Approximate ΔE via redmean. Cheap, no Pillow dep, ~CIE76 quality."""
    rmean = (a[0] + b[0]) / 2
    dr = a[0] - b[0]
    dg = a[1] - b[1]
    db = a[2] - b[2]
    return math.sqrt(
        (2 + rmean / 256) * dr * dr
        + 4 * dg * dg
        + (2 + (255 - rmean) / 256) * db * db
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


# Minimum redmean ΔE between any two role colors. Empirically ~30 separates
# colors that read as different on screen at preview sizes; below that the
# preview looks tonally flat.
MIN_PERCEPTUAL_DISTANCE = 30.0


@dataclass
class PaletteValidationResult:
    primary_hex: str
    secondary_hex: str
    accent_hex: str
    source: PaletteSource
    fallbacks_applied: List[str] = field(default_factory=list)


def enforce_palette_distance(
    *,
    primary: str,
    secondary: Optional[str],
    accent: Optional[str],
    sampled: bool = True,
) -> PaletteValidationResult:
    """Make sure the three role colors are perceptually distinct."""
    fallbacks: List[str] = []

    primary_rgb = _hex_to_rgb(primary)

    # Secondary: derive from primary if missing or too close
    secondary_rgb = _hex_to_rgb(secondary) if secondary else None
    if secondary_rgb is None or perceptual_distance(primary_rgb, secondary_rgb) < MIN_PERCEPTUAL_DISTANCE:
        secondary_rgb = _shift_lightness(primary_rgb, -0.18)
        fallbacks.append("secondary_derived_from_primary")

    # Accent: derive triadic if missing or too close to either
    accent_rgb = _hex_to_rgb(accent) if accent else None
    if (
        accent_rgb is None
        or perceptual_distance(primary_rgb, accent_rgb) < MIN_PERCEPTUAL_DISTANCE
        or perceptual_distance(secondary_rgb, accent_rgb) < MIN_PERCEPTUAL_DISTANCE
    ):
        accent_rgb = _triadic(primary_rgb)
        fallbacks.append("accent_derived_triadic")

    # If derivations still violate the rule (super-low chroma palette),
    # fall back to a complementary pair so we always meet the contract.
    if perceptual_distance(primary_rgb, accent_rgb) < MIN_PERCEPTUAL_DISTANCE:
        accent_rgb = _complement(primary_rgb)
        fallbacks.append("accent_derived_complementary")

    if (
        perceptual_distance(primary_rgb, secondary_rgb) < MIN_PERCEPTUAL_DISTANCE
        and perceptual_distance(primary_rgb, accent_rgb) >= MIN_PERCEPTUAL_DISTANCE
    ):
        secondary_rgb = _shift_lightness(primary_rgb, -0.32)
        fallbacks.append("secondary_dark_lightness")

    source = PaletteSource.SAMPLED if sampled and not fallbacks else (
        PaletteSource.DERIVED if sampled else PaletteSource.DEFAULT
    )

    return PaletteValidationResult(
        primary_hex=_rgb_to_hex(primary_rgb),
        secondary_hex=_rgb_to_hex(secondary_rgb),
        accent_hex=_rgb_to_hex(accent_rgb),
        source=source,
        fallbacks_applied=fallbacks,
    )


# ---------------------------------------------------------------------------
# Harmony helpers
# ---------------------------------------------------------------------------


def _shift_lightness(rgb: RGB, delta: float) -> RGB:
    h, s, l = _rgb_to_hsl(rgb)
    return _hsl_to_rgb(h, s, max(0.0, min(1.0, l + delta)))


def _triadic(rgb: RGB) -> RGB:
    h, s, l = _rgb_to_hsl(rgb)
    return _hsl_to_rgb((h + 120) % 360, max(s, 0.5), max(l, 0.45))


def _complement(rgb: RGB) -> RGB:
    h, s, l = _rgb_to_hsl(rgb)
    return _hsl_to_rgb((h + 180) % 360, max(s, 0.45), max(l, 0.45))


# ---------------------------------------------------------------------------
# Diverse sampling helpers used by the screenshot palette extractor
# ---------------------------------------------------------------------------


def diverse_sample(
    candidates: Iterable[RGB],
    *,
    target_count: int = 5,
    minimum_distance: float = MIN_PERCEPTUAL_DISTANCE,
) -> List[RGB]:
    """Greedy selection of perceptually distinct colors.

    The plan calls for "Increase screenshot sampling diversity" — instead of
    picking the top-N most-frequent colors (which are often near-identical
    site backgrounds), we keep colors that are at least ``minimum_distance``
    from everything we've already kept.
    """
    selected: List[RGB] = []
    for color in candidates:
        if all(perceptual_distance(color, kept) >= minimum_distance for kept in selected):
            selected.append(color)
        if len(selected) >= target_count:
            break
    return selected
