"""3-stop perceptual gradients + adaptive overlays (Phase 3.2).

The plan calls for:
  - "Use 3-stop gradients with perceptual interpolation."
  - "Apply adaptive overlays based on local luminance."
  - "Add optional grain/noise at low opacity for depth."

We do all three in this module. Interpolation runs in Oklab (perceptually
uniform) so the middle stop doesn't go muddy on long ranges. The overlay is
luminance-aware: bright regions get a darker veil, dark regions get a lighter
gloss.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple


RGB = Tuple[int, int, int]


@dataclass
class GradientPalette:
    """Three colors used to build the gradient."""

    start: RGB
    middle: RGB
    end: RGB

    @classmethod
    def from_hex(cls, start: str, middle: str, end: str) -> "GradientPalette":
        return cls(_hex_to_rgb(start), _hex_to_rgb(middle), _hex_to_rgb(end))


@dataclass
class LuminanceOverlay:
    """Adaptive overlay parameters."""

    base_alpha: float = 0.35
    bright_threshold: float = 0.7
    dark_threshold: float = 0.3
    bright_alpha_boost: float = 0.25
    dark_alpha_boost: float = 0.15


# ---------------------------------------------------------------------------
# Color space helpers (Oklab)
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


def _srgb_to_linear(channel: float) -> float:
    c = channel / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(channel: float) -> int:
    c = channel
    if c <= 0.0031308:
        out = 12.92 * c
    else:
        out = 1.055 * (c ** (1 / 2.4)) - 0.055
    return max(0, min(255, int(round(out * 255))))


def _rgb_to_oklab(rgb: RGB) -> Tuple[float, float, float]:
    r = _srgb_to_linear(rgb[0])
    g = _srgb_to_linear(rgb[1])
    b = _srgb_to_linear(rgb[2])
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_ = l ** (1 / 3) if l >= 0 else -((-l) ** (1 / 3))
    m_ = m ** (1 / 3) if m >= 0 else -((-m) ** (1 / 3))
    s_ = s ** (1 / 3) if s >= 0 else -((-s) ** (1 / 3))
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b_ = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return (L, a, b_)


def _oklab_to_rgb(L: float, a: float, b: float) -> RGB:
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l = l_ ** 3
    m = m_ ** 3
    s = s_ ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b_lin = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return (
        _linear_to_srgb(max(0.0, r)),
        _linear_to_srgb(max(0.0, g)),
        _linear_to_srgb(max(0.0, b_lin)),
    )


def _interpolate_oklab(a: RGB, b: RGB, t: float) -> RGB:
    la, aa, ba = _rgb_to_oklab(a)
    lb, ab, bb = _rgb_to_oklab(b)
    return _oklab_to_rgb(
        la + (lb - la) * t,
        aa + (ab - aa) * t,
        ba + (bb - ba) * t,
    )


def _relative_luminance(rgb: RGB) -> float:
    r = _srgb_to_linear(rgb[0])
    g = _srgb_to_linear(rgb[1])
    b = _srgb_to_linear(rgb[2])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# ---------------------------------------------------------------------------
# Gradient construction
# ---------------------------------------------------------------------------


def build_three_stop_gradient(
    palette: GradientPalette,
    *,
    width: int,
    height: int,
    direction: str = "diagonal",
    overlay: Optional[LuminanceOverlay] = None,
    add_grain: bool = True,
    grain_strength: float = 0.012,
    seed: Optional[int] = None,
) -> bytes:
    """Render a 3-stop perceptual gradient as RGB bytes.

    Returns raw ``bytes`` of length ``width * height * 3`` so callers can
    construct a ``PIL.Image.frombytes("RGB", ...)``. Tests can also assert on
    the raw bytes without spinning up Pillow.
    """
    rng = random.Random(seed)
    overlay = overlay or LuminanceOverlay()

    pixels = bytearray(width * height * 3)

    if direction == "horizontal":
        coord_t = lambda x, y: x / max(1, width - 1)
    elif direction == "vertical":
        coord_t = lambda x, y: y / max(1, height - 1)
    elif direction == "radial":
        cx, cy = width / 2, height / 2
        max_d = math.hypot(cx, cy)
        coord_t = lambda x, y: min(1.0, math.hypot(x - cx, y - cy) / max_d)
    else:  # diagonal
        denom = max(1, width + height - 2)
        coord_t = lambda x, y: (x + y) / denom

    for y in range(height):
        for x in range(width):
            t = coord_t(x, y)
            if t <= 0.5:
                color = _interpolate_oklab(palette.start, palette.middle, t * 2)
            else:
                color = _interpolate_oklab(palette.middle, palette.end, (t - 0.5) * 2)

            if overlay:
                color = _apply_overlay(color, overlay)

            if add_grain and grain_strength > 0:
                noise = (rng.random() - 0.5) * grain_strength * 255
                color = (
                    max(0, min(255, int(color[0] + noise))),
                    max(0, min(255, int(color[1] + noise))),
                    max(0, min(255, int(color[2] + noise))),
                )

            offset = (y * width + x) * 3
            pixels[offset] = color[0]
            pixels[offset + 1] = color[1]
            pixels[offset + 2] = color[2]

    return bytes(pixels)


def _apply_overlay(color: RGB, overlay: LuminanceOverlay) -> RGB:
    """Per-pixel luminance overlay (very subtle to avoid muddying gradient)."""
    luminance = _relative_luminance(color)

    if luminance >= overlay.bright_threshold:
        alpha = overlay.base_alpha + overlay.bright_alpha_boost
        # Blend toward darker tone
        return _blend(color, (0, 0, 0), alpha * 0.25)
    if luminance <= overlay.dark_threshold:
        alpha = overlay.base_alpha + overlay.dark_alpha_boost
        return _blend(color, (255, 255, 255), alpha * 0.20)
    return color


def _blend(a: RGB, b: RGB, alpha: float) -> RGB:
    alpha = max(0.0, min(1.0, alpha))
    return (
        int(a[0] * (1 - alpha) + b[0] * alpha),
        int(a[1] * (1 - alpha) + b[1] * alpha),
        int(a[2] * (1 - alpha) + b[2] * alpha),
    )


# ---------------------------------------------------------------------------
# Sample helper for tests / quick previews without Pillow installed.
# ---------------------------------------------------------------------------


def gradient_signature(
    palette: GradientPalette,
    *,
    width: int = 8,
    height: int = 4,
    direction: str = "diagonal",
) -> List[List[RGB]]:
    """Lightweight sampler — same math, returns a tiny grid for unit tests."""
    grid: List[List[RGB]] = []
    for y in range(height):
        row: List[RGB] = []
        for x in range(width):
            t = (x + y) / max(1, width + height - 2)
            if direction == "horizontal":
                t = x / max(1, width - 1)
            elif direction == "vertical":
                t = y / max(1, height - 1)
            if t <= 0.5:
                row.append(_interpolate_oklab(palette.start, palette.middle, t * 2))
            else:
                row.append(_interpolate_oklab(palette.middle, palette.end, (t - 0.5) * 2))
        grid.append(row)
    return grid
