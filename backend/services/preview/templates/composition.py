"""Composition blending polish (Phase 3.4).

The plan asks us to:
  - "Replace linear fades with eased masks."
  - "Tune screenshot blend widths and separator styling."

We expose pure-math helpers here so both the renderer and the tests can use
the identical curves. The cubic-bezier easing matches the CSS
``cubic-bezier(0.4, 0.0, 0.2, 1)`` curve (Material's "standard easing").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple


def _bezier(t: float, p1: float, p2: float) -> float:
    """Approximate ``cubic-bezier(p1, 0, p2, 1)`` easing for t in [0, 1]."""
    t = max(0.0, min(1.0, t))
    one_minus = 1 - t
    return (3 * one_minus**2 * t * p1) + (3 * one_minus * t**2 * p2) + t**3


def eased_mask(width: int, *, p1: float = 0.4, p2: float = 0.2) -> List[float]:
    """Return per-pixel alpha values across an eased fade band."""
    if width <= 0:
        return []
    if width == 1:
        return [1.0]
    return [_bezier(i / (width - 1), p1, p2) for i in range(width)]


@dataclass
class Separator:
    """Description of a separator strip between two regions."""

    width_px: int
    color_start: Tuple[int, int, int]
    color_end: Tuple[int, int, int]
    style: str = "fade"  # 'fade' | 'line' | 'dual'


def apply_blend_separator(
    base: Sequence[Tuple[int, int, int]],
    overlay: Sequence[Tuple[int, int, int]],
    separator: Separator,
) -> List[Tuple[int, int, int]]:
    """Blend ``overlay`` onto ``base`` along an eased separator strip.

    ``base`` and ``overlay`` are flat sequences of RGB triples; the strip is
    centered on the midpoint and ``separator.width_px`` wide.
    """
    if len(base) != len(overlay):
        raise ValueError("base/overlay length mismatch")

    width = separator.width_px
    if width <= 0:
        return list(base)

    midpoint = len(base) // 2
    half = width // 2
    start = max(0, midpoint - half)
    stop = min(len(base), midpoint + half)
    band = stop - start
    if band <= 0:
        return list(base)

    mask = eased_mask(band)

    out: List[Tuple[int, int, int]] = list(base)
    for i, alpha in enumerate(mask):
        idx = start + i
        b = base[idx]
        o = overlay[idx]
        out[idx] = (
            int(b[0] * (1 - alpha) + o[0] * alpha),
            int(b[1] * (1 - alpha) + o[1] * alpha),
            int(b[2] * (1 - alpha) + o[2] * alpha),
        )

    return out


def screenshot_blend_band(
    canvas_width: int,
    *,
    target_fraction: float = 0.18,
    minimum_px: int = 64,
    maximum_px: int = 240,
) -> int:
    """Compute the recommended blend-band width for screenshot composites.

    Plan calls for "Tune screenshot blend widths". We default to ~18% of the
    canvas width with hard floors and ceilings so very short or very wide
    canvases still get a reasonable band.
    """
    target = int(canvas_width * target_fraction)
    return max(minimum_px, min(maximum_px, target))
