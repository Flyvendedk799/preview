"""
Readability Auto-Fixer - Automatic Readability Issue Resolution.

PHASE 1 IMPLEMENTATION:
When quality validation detects issues, this service automatically
FIXES them instead of just flagging. Provides:
- Text contrast adjustment
- Gradient/blur overlay injection for text areas
- Background contrast optimization
- Smart text shadow application
- Automatic color adjustment to meet WCAG standards

This is the "auto-fix" layer that runs after rendering and validation.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import math

from .color_psychology import (
    get_luminance, get_contrast_ratio, lighten_color, darken_color,
    hex_to_rgb, rgb_to_hex, get_optimal_text_color, ensure_contrast
)
from .visual_quality_validator import (
    VisualQualityScore, CONTRAST_AA_LARGE, CONTRAST_AA_NORMAL
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Minimum contrast ratios
MIN_CONTRAST_LARGE_TEXT = 3.0  # WCAG AA for large text
MIN_CONTRAST_NORMAL_TEXT = 4.5  # WCAG AA for normal text
TARGET_CONTRAST = 7.0  # WCAG AAA for best readability

# Text region detection (approximate zones)
TEXT_ZONES = {
    "headline": {"y_start": 0.15, "y_end": 0.45, "weight": 1.0},
    "subtitle": {"y_start": 0.40, "y_end": 0.60, "weight": 0.8},
    "description": {"y_start": 0.55, "y_end": 0.80, "weight": 0.7},
    "footer": {"y_start": 0.85, "y_end": 1.0, "weight": 0.5}
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FixResult:
    """Result of an auto-fix operation."""
    was_fixed: bool
    fix_type: str
    before_score: float
    after_score: float
    details: str


@dataclass
class ReadabilityFixReport:
    """Complete report of all fixes applied."""
    image: Image.Image
    fixes_applied: List[FixResult]
    overall_improvement: float
    final_contrast_ratio: float
    meets_wcag_aa: bool
    meets_wcag_aaa: bool


# =============================================================================
# READABILITY AUTO-FIXER
# =============================================================================

class ReadabilityAutoFixer:
    """
    Automatically fixes readability issues in rendered preview images.
    
    When the VisualQualityValidator detects issues, this service
    applies targeted fixes to resolve them.
    """
    
    def __init__(
        self,
        target_contrast: float = MIN_CONTRAST_NORMAL_TEXT,
        max_adjustment_steps: int = 10,
        overlay_opacity_max: float = 0.7
    ):
        """
        Initialize auto-fixer with thresholds.
        
        Args:
            target_contrast: Target contrast ratio to achieve
            max_adjustment_steps: Maximum color adjustment iterations
            overlay_opacity_max: Maximum opacity for text overlays
        """
        self.target_contrast = target_contrast
        self.max_adjustment_steps = max_adjustment_steps
        self.overlay_opacity_max = overlay_opacity_max
        
        logger.info(
            f"ReadabilityAutoFixer initialized: "
            f"target_contrast={target_contrast}, "
            f"max_steps={max_adjustment_steps}"
        )
    
    def fix_image(
        self,
        image: Image.Image,
        quality_score: Optional[VisualQualityScore] = None,
        text_color: Optional[Tuple[int, int, int]] = None,
        background_color: Optional[Tuple[int, int, int]] = None,
        text_regions: Optional[List[Dict[str, Any]]] = None
    ) -> ReadabilityFixReport:
        """
        Automatically fix readability issues in an image.
        
        Args:
            image: PIL Image to fix
            quality_score: Optional pre-computed quality score
            text_color: Known text color (if available)
            background_color: Known background color (if available)
            text_regions: List of text region dicts with x, y, width, height
            
        Returns:
            ReadabilityFixReport with fixed image and details
        """
        logger.info(f"🔧 Auto-fixing readability issues: {image.size}")
        
        fixes_applied = []
        working_image = image.copy()
        
        # Detect colors if not provided
        if text_color is None or background_color is None:
            detected_bg, detected_text = self._detect_dominant_colors(working_image)
            background_color = background_color or detected_bg
            text_color = text_color or detected_text
        
        initial_contrast = get_contrast_ratio(text_color, background_color)
        
        # 1. Check if contrast fix is needed
        if initial_contrast < self.target_contrast:
            working_image, contrast_fix = self._fix_contrast(
                working_image, text_color, background_color, text_regions
            )
            if contrast_fix.was_fixed:
                fixes_applied.append(contrast_fix)
        
        # 2. Apply text shadows if still below target
        current_contrast = self._estimate_current_contrast(working_image)
        if current_contrast < self.target_contrast:
            working_image, shadow_fix = self._apply_text_shadows(
                working_image, text_regions, background_color
            )
            if shadow_fix.was_fixed:
                fixes_applied.append(shadow_fix)
        
        # 3. Inject gradient overlay for text areas if needed
        current_contrast = self._estimate_current_contrast(working_image)
        if current_contrast < MIN_CONTRAST_LARGE_TEXT:
            working_image, overlay_fix = self._inject_text_overlay(
                working_image, text_regions, background_color
            )
            if overlay_fix.was_fixed:
                fixes_applied.append(overlay_fix)
        
        # 4. Final contrast boost if still problematic
        current_contrast = self._estimate_current_contrast(working_image)
        if current_contrast < MIN_CONTRAST_LARGE_TEXT:
            working_image, boost_fix = self._boost_overall_contrast(working_image)
            if boost_fix.was_fixed:
                fixes_applied.append(boost_fix)
        
        # Calculate final metrics
        final_contrast = self._estimate_current_contrast(working_image)
        improvement = final_contrast - initial_contrast
        
        report = ReadabilityFixReport(
            image=working_image,
            fixes_applied=fixes_applied,
            overall_improvement=improvement,
            final_contrast_ratio=final_contrast,
            meets_wcag_aa=final_contrast >= MIN_CONTRAST_NORMAL_TEXT,
            meets_wcag_aaa=final_contrast >= TARGET_CONTRAST
        )
        
        logger.info(
            f"✅ Auto-fix complete: {len(fixes_applied)} fixes applied, "
            f"contrast {initial_contrast:.2f} → {final_contrast:.2f} "
            f"(improvement: {improvement:+.2f})"
        )
        
        return report
    
    def fix_from_bytes(
        self,
        image_bytes: bytes,
        quality_score: Optional[VisualQualityScore] = None,
        text_color: Optional[Tuple[int, int, int]] = None,
        background_color: Optional[Tuple[int, int, int]] = None
    ) -> Tuple[bytes, ReadabilityFixReport]:
        """
        Fix image from bytes and return fixed bytes.
        
        Args:
            image_bytes: PNG/JPEG image bytes
            quality_score: Optional pre-computed quality score
            text_color: Known text color
            background_color: Known background color
            
        Returns:
            Tuple of (fixed_image_bytes, report)
        """
        try:
            image = Image.open(BytesIO(image_bytes))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            report = self.fix_image(image, quality_score, text_color, background_color)
            
            # Convert back to bytes
            buffer = BytesIO()
            report.image.save(buffer, format='PNG', quality=95)
            fixed_bytes = buffer.getvalue()
            
            return fixed_bytes, report
            
        except Exception as e:
            logger.error(f"Failed to fix image bytes: {e}")
            return image_bytes, ReadabilityFixReport(
                image=Image.open(BytesIO(image_bytes)),
                fixes_applied=[],
                overall_improvement=0.0,
                final_contrast_ratio=0.0,
                meets_wcag_aa=False,
                meets_wcag_aaa=False
            )
    
    def _detect_dominant_colors(
        self,
        image: Image.Image
    ) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
        """
        Detect dominant background and text colors from image.
        
        Returns:
            Tuple of (background_color, text_color)
        """
        # Resize for faster processing
        small = image.resize((100, 100), Image.Resampling.LANCZOS)
        pixels = list(small.getdata())
        
        # Simple color clustering
        from collections import Counter
        
        # Quantize colors
        quantized = [
            (r // 32 * 32, g // 32 * 32, b // 32 * 32) 
            for r, g, b in pixels
        ]
        color_counts = Counter(quantized)
        
        # Get top 2 colors
        top_colors = color_counts.most_common(2)
        
        if len(top_colors) >= 2:
            color1 = top_colors[0][0]
            color2 = top_colors[1][0]
            
            # Lighter color is likely background
            if get_luminance(color1) > get_luminance(color2):
                return color1, color2
            else:
                return color2, color1
        elif len(top_colors) == 1:
            bg = top_colors[0][0]
            text = (0, 0, 0) if get_luminance(bg) > 0.5 else (255, 255, 255)
            return bg, text
        else:
            return (255, 255, 255), (0, 0, 0)
    
    def _estimate_current_contrast(self, image: Image.Image) -> float:
        """Estimate current contrast ratio from image."""
        bg, text = self._detect_dominant_colors(image)
        return get_contrast_ratio(text, bg)
    
    def _fix_contrast(
        self,
        image: Image.Image,
        text_color: Tuple[int, int, int],
        background_color: Tuple[int, int, int],
        text_regions: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[Image.Image, FixResult]:
        """
        Fix contrast by adjusting background in text areas.
        
        For light backgrounds with light text: darken background
        For dark backgrounds with dark text: lighten background
        """
        initial_contrast = get_contrast_ratio(text_color, background_color)
        
        if initial_contrast >= self.target_contrast:
            return image, FixResult(
                was_fixed=False,
                fix_type="contrast",
                before_score=initial_contrast,
                after_score=initial_contrast,
                details="Contrast already sufficient"
            )
        
        working_image = image.copy()
        draw = ImageDraw.Draw(working_image, 'RGBA')
        
        width, height = working_image.size
        
        # Determine overlay color based on text color
        text_luminance = get_luminance(text_color)
        
        if text_luminance > 0.5:
            # Light text needs dark overlay
            overlay_color = (0, 0, 0)
        else:
            # Dark text needs light overlay
            overlay_color = (255, 255, 255)
        
        # Calculate needed opacity to achieve target contrast
        opacity = self._calculate_needed_opacity(
            text_color, background_color, overlay_color
        )
        opacity = min(opacity, self.overlay_opacity_max)
        
        # Apply overlay to text regions
        if text_regions:
            for region in text_regions:
                x = int(region.get("x", 0) * width)
                y = int(region.get("y", 0) * height)
                w = int(region.get("width", 1.0) * width)
                h = int(region.get("height", 0.2) * height)
                
                # Add padding around text
                padding = 20
                x = max(0, x - padding)
                y = max(0, y - padding)
                w = min(width - x, w + padding * 2)
                h = min(height - y, h + padding * 2)
                
                overlay_rgba = (*overlay_color, int(opacity * 255))
                draw.rectangle([x, y, x + w, y + h], fill=overlay_rgba)
        else:
            # Apply to default text zones
            for zone_name, zone in TEXT_ZONES.items():
                y_start = int(zone["y_start"] * height)
                y_end = int(zone["y_end"] * height)
                zone_opacity = int(opacity * zone["weight"] * 255)
                overlay_rgba = (*overlay_color, zone_opacity)
                draw.rectangle([0, y_start, width, y_end], fill=overlay_rgba)
        
        # Convert back to RGB
        if working_image.mode == 'RGBA':
            rgb_image = Image.new('RGB', working_image.size, (255, 255, 255))
            rgb_image.paste(working_image, mask=working_image.split()[3])
            working_image = rgb_image
        
        final_contrast = self._estimate_current_contrast(working_image)
        
        return working_image, FixResult(
            was_fixed=True,
            fix_type="contrast_overlay",
            before_score=initial_contrast,
            after_score=final_contrast,
            details=f"Applied {overlay_color} overlay at {opacity:.0%} opacity"
        )
    
    def _calculate_needed_opacity(
        self,
        text_color: Tuple[int, int, int],
        background_color: Tuple[int, int, int],
        overlay_color: Tuple[int, int, int]
    ) -> float:
        """Calculate opacity needed to achieve target contrast."""
        current = get_contrast_ratio(text_color, background_color)
        
        if current >= self.target_contrast:
            return 0.0
        
        # Binary search for needed opacity
        low, high = 0.0, 1.0
        
        for _ in range(10):
            mid = (low + high) / 2
            
            # Blend background with overlay
            blended = tuple(
                int(bg * (1 - mid) + ov * mid)
                for bg, ov in zip(background_color, overlay_color)
            )
            
            ratio = get_contrast_ratio(text_color, blended)
            
            if ratio < self.target_contrast:
                low = mid
            else:
                high = mid
        
        return high
    
    def _apply_text_shadows(
        self,
        image: Image.Image,
        text_regions: Optional[List[Dict[str, Any]]],
        background_color: Tuple[int, int, int]
    ) -> Tuple[Image.Image, FixResult]:
        """
        Apply subtle text shadows/glow to improve readability.
        
        This simulates the effect of text-shadow CSS property.
        """
        initial_contrast = self._estimate_current_contrast(image)
        
        # Create a slightly blurred version for shadow effect
        working_image = image.copy()
        
        # Detect if we need light or dark shadow
        bg_luminance = get_luminance(background_color)
        
        if bg_luminance > 0.5:
            # Light background - use subtle dark shadow
            shadow_image = ImageEnhance.Brightness(working_image).enhance(0.85)
        else:
            # Dark background - use subtle glow
            shadow_image = ImageEnhance.Brightness(working_image).enhance(1.15)
        
        # Blur the shadow layer
        shadow_blurred = shadow_image.filter(ImageFilter.GaussianBlur(radius=2))
        
        # Blend original with shadow (original on top)
        working_image = Image.blend(shadow_blurred, working_image, alpha=0.85)
        
        final_contrast = self._estimate_current_contrast(working_image)
        
        return working_image, FixResult(
            was_fixed=True,
            fix_type="text_shadow",
            before_score=initial_contrast,
            after_score=final_contrast,
            details="Applied subtle shadow/glow effect"
        )
    
    def _inject_text_overlay(
        self,
        image: Image.Image,
        text_regions: Optional[List[Dict[str, Any]]],
        background_color: Tuple[int, int, int]
    ) -> Tuple[Image.Image, FixResult]:
        """
        Inject gradient overlay behind text areas.
        
        Creates a smooth gradient that improves text visibility
        without being visually jarring.
        """
        initial_contrast = self._estimate_current_contrast(image)
        
        width, height = image.size
        working_image = image.copy().convert('RGBA')
        
        # Create gradient overlay
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Determine overlay color
        bg_luminance = get_luminance(background_color)
        base_color = (0, 0, 0) if bg_luminance > 0.3 else (255, 255, 255)
        
        # Apply gradient to text zones
        for zone_name, zone in TEXT_ZONES.items():
            y_start = int(zone["y_start"] * height)
            y_end = int(zone["y_end"] * height)
            zone_height = y_end - y_start
            
            # Create gradient within zone
            for y in range(y_start, y_end):
                # Calculate position within zone (0 to 1)
                t = (y - y_start) / zone_height
                
                # Bell curve opacity (stronger in middle)
                opacity = math.sin(t * math.pi) * zone["weight"] * 0.4
                opacity = int(opacity * 255)
                
                draw.line([(0, y), (width, y)], fill=(*base_color, opacity))
        
        # Composite overlay onto image
        working_image = Image.alpha_composite(working_image, overlay)
        working_image = working_image.convert('RGB')
        
        final_contrast = self._estimate_current_contrast(working_image)
        
        return working_image, FixResult(
            was_fixed=True,
            fix_type="gradient_overlay",
            before_score=initial_contrast,
            after_score=final_contrast,
            details=f"Injected {base_color} gradient overlay"
        )
    
    def _boost_overall_contrast(
        self,
        image: Image.Image
    ) -> Tuple[Image.Image, FixResult]:
        """
        Last resort: boost overall image contrast.
        """
        initial_contrast = self._estimate_current_contrast(image)
        
        enhancer = ImageEnhance.Contrast(image)
        working_image = enhancer.enhance(1.2)  # 20% boost
        
        final_contrast = self._estimate_current_contrast(working_image)
        
        return working_image, FixResult(
            was_fixed=True,
            fix_type="contrast_boost",
            before_score=initial_contrast,
            after_score=final_contrast,
            details="Applied 20% overall contrast boost"
        )


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_fixer_instance: Optional[ReadabilityAutoFixer] = None


def get_readability_auto_fixer() -> ReadabilityAutoFixer:
    """Get singleton ReadabilityAutoFixer instance."""
    global _fixer_instance
    
    if _fixer_instance is None:
        _fixer_instance = ReadabilityAutoFixer()
    
    return _fixer_instance


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def auto_fix_readability(
    image: Image.Image,
    quality_score: Optional[VisualQualityScore] = None,
    text_color: Optional[Tuple[int, int, int]] = None,
    background_color: Optional[Tuple[int, int, int]] = None
) -> ReadabilityFixReport:
    """
    Convenience function to auto-fix readability issues.
    
    Args:
        image: PIL Image to fix
        quality_score: Optional pre-computed quality score
        text_color: Known text color
        background_color: Known background color
        
    Returns:
        ReadabilityFixReport with fixed image
    """
    return get_readability_auto_fixer().fix_image(
        image, quality_score, text_color, background_color
    )


def auto_fix_readability_bytes(
    image_bytes: bytes,
    quality_score: Optional[VisualQualityScore] = None
) -> Tuple[bytes, ReadabilityFixReport]:
    """
    Convenience function to auto-fix readability from bytes.
    
    Args:
        image_bytes: PNG/JPEG image bytes
        quality_score: Optional pre-computed quality score
        
    Returns:
        Tuple of (fixed_bytes, report)
    """
    return get_readability_auto_fixer().fix_from_bytes(
        image_bytes, quality_score
    )


def calculate_optimal_text_color(
    background_color: Tuple[int, int, int],
    prefer_light: bool = True
) -> Tuple[int, int, int]:
    """
    Calculate optimal text color for a given background.
    
    Args:
        background_color: Background RGB color
        prefer_light: Prefer light text if possible
        
    Returns:
        Optimal text color RGB
    """
    return get_optimal_text_color(background_color, prefer_light)


def adjust_color_for_contrast(
    foreground: Tuple[int, int, int],
    background: Tuple[int, int, int],
    min_ratio: float = MIN_CONTRAST_NORMAL_TEXT
) -> Tuple[int, int, int]:
    """
    Adjust foreground color to meet minimum contrast.
    
    Args:
        foreground: Foreground/text color
        background: Background color
        min_ratio: Minimum contrast ratio to achieve
        
    Returns:
        Adjusted foreground color
    """
    return ensure_contrast(foreground, background, min_ratio)

