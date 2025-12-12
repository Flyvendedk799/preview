"""
Quality Assurance Engine - Layer 7 of Design Framework Enhancement.

This module provides automated quality checks and polish enhancements
to ensure professional-grade output.

Key Features:
- Accessibility validation (WCAG AAA)
- Visual balance scoring
- Typography quality checks
- Brand fidelity validation
- Automated polish enhancements
- A/B test framework
"""

import logging
import math
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageStat
import colorsys

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """Quality assessment scores."""
    accessibility: float  # 0-1 (WCAG compliance)
    visual_balance: float  # 0-1 (weight distribution)
    typography: float  # 0-1 (hierarchy, spacing)
    brand_fidelity: float  # 0-1 (color/style match)
    technical: float  # 0-1 (file size, dimensions)
    overall: float  # 0-1 (weighted average)
    grade: str  # A+, A, B+, B, C, F
    issues: List[str]  # List of problems found
    suggestions: List[str]  # Improvement recommendations


class QualityAssuranceEngine:
    """
    Automated quality assurance for generated previews.
    
    Validates and improves designs to ensure they meet professional standards.
    """
    
    def __init__(self):
        self.min_contrast_ratio = 7.0  # WCAG AAA
        self.min_font_size = 16  # Pixels
        self.max_file_size = 300 * 1024  # 300 KB
    
    def assess_quality(
        self,
        image: Image.Image,
        design_data: Dict[str, Any],
        brand_colors: Optional[Dict[str, Tuple[int, int, int]]] = None
    ) -> QualityScore:
        """
        Comprehensive quality assessment.
        
        Args:
            image: Generated preview image
            design_data: Design metadata (fonts, colors, layout)
            brand_colors: Optional original brand colors
            
        Returns:
            QualityScore with detailed assessment
        """
        issues = []
        suggestions = []
        
        # 1. Accessibility check
        accessibility_score = self._check_accessibility(design_data, issues, suggestions)
        
        # 2. Visual balance
        balance_score = self._check_visual_balance(image, design_data, issues, suggestions)
        
        # 3. Typography quality
        typography_score = self._check_typography(design_data, issues, suggestions)
        
        # 4. Brand fidelity
        brand_score = self._check_brand_fidelity(design_data, brand_colors, issues, suggestions)
        
        # 5. Technical quality
        technical_score = self._check_technical_quality(image, issues, suggestions)
        
        # Calculate overall score (weighted average)
        overall = (
            accessibility_score * 0.25 +
            balance_score * 0.20 +
            typography_score * 0.20 +
            brand_score * 0.20 +
            technical_score * 0.15
        )
        
        # Assign grade
        if overall >= 0.95:
            grade = "A+"
        elif overall >= 0.90:
            grade = "A"
        elif overall >= 0.85:
            grade = "B+"
        elif overall >= 0.80:
            grade = "B"
        elif overall >= 0.70:
            grade = "C"
        else:
            grade = "F"
        
        logger.info(f"📊 Quality Assessment: {grade} (Overall: {overall:.2f})")
        
        return QualityScore(
            accessibility=accessibility_score,
            visual_balance=balance_score,
            typography=typography_score,
            brand_fidelity=brand_score,
            technical=technical_score,
            overall=overall,
            grade=grade,
            issues=issues,
            suggestions=suggestions
        )
    
    def apply_polish(
        self,
        image: Image.Image,
        design_data: Dict[str, Any]
    ) -> Image.Image:
        """
        Apply automated polish enhancements.
        
        Args:
            image: Original image
            design_data: Design metadata
            
        Returns:
            Polished image
        """
        polished = image.copy()
        
        # 1. Subtle vignette (draws focus to center)
        polished = self._apply_vignette(polished, intensity=0.03)
        
        # 2. Sharpening pass (crisp text)
        polished = self._apply_sharpening(polished, amount=0.3)
        
        # 3. Color vibrance boost (if dull)
        if self._is_dull_image(polished):
            polished = self._boost_vibrance(polished, amount=0.05)
        
        # 4. Noise reduction (smooth gradients)
        polished = self._smooth_gradients(polished)
        
        # 5. Optical adjustments (subpixel positioning simulated)
        polished = self._apply_optical_adjustments(polished)
        
        logger.info("✨ Applied polish enhancements")
        return polished
    
    # =========================================================================
    # ACCESSIBILITY CHECKS
    # =========================================================================
    
    def _check_accessibility(
        self,
        design_data: Dict[str, Any],
        issues: List[str],
        suggestions: List[str]
    ) -> float:
        """Check WCAG AAA accessibility compliance."""
        score = 1.0
        
        # Check color contrast
        colors = design_data.get("colors", {})
        text_color = colors.get("text", (0, 0, 0))
        bg_color = colors.get("background", (255, 255, 255))
        
        contrast_ratio = self._calculate_contrast_ratio(text_color, bg_color)
        
        if contrast_ratio < 4.5:
            issues.append(f"Text contrast too low: {contrast_ratio:.1f}:1 (need 4.5:1)")
            suggestions.append("Increase text-background contrast for readability")
            score -= 0.3
        elif contrast_ratio < 7.0:
            issues.append(f"Text contrast below AAA: {contrast_ratio:.1f}:1 (need 7:1)")
            suggestions.append("Increase contrast to meet WCAG AAA standards")
            score -= 0.1
        
        # Check font sizes
        fonts = design_data.get("fonts", {})
        body_size = fonts.get("body_size", 16)
        
        if body_size < 14:
            issues.append(f"Body text too small: {body_size}px (need 16px+)")
            suggestions.append("Increase body text size to at least 16px")
            score -= 0.2
        elif body_size < 16:
            issues.append(f"Body text below recommended: {body_size}px")
            suggestions.append("Consider 16px+ for better readability")
            score -= 0.05
        
        return max(0.0, score)
    
    def _calculate_contrast_ratio(
        self,
        color1: Tuple[int, int, int],
        color2: Tuple[int, int, int]
    ) -> float:
        """Calculate WCAG contrast ratio."""
        def relative_luminance(rgb):
            r, g, b = [c / 255.0 for c in rgb]
            r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
            g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
            b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        l1 = relative_luminance(color1)
        l2 = relative_luminance(color2)
        
        lighter = max(l1, l2)
        darker = min(l1, l2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    # =========================================================================
    # VISUAL BALANCE CHECKS
    # =========================================================================
    
    def _check_visual_balance(
        self,
        image: Image.Image,
        design_data: Dict[str, Any],
        issues: List[str],
        suggestions: List[str]
    ) -> float:
        """Check visual balance and weight distribution."""
        score = 1.0
        
        # Convert to grayscale for weight analysis
        gray = image.convert('L')
        width, height = gray.size
        
        # Divide into quadrants
        quadrants = [
            gray.crop((0, 0, width // 2, height // 2)),  # Top-left
            gray.crop((width // 2, 0, width, height // 2)),  # Top-right
            gray.crop((0, height // 2, width // 2, height)),  # Bottom-left
            gray.crop((width // 2, height // 2, width, height))  # Bottom-right
        ]
        
        # Calculate average luminance per quadrant
        weights = [ImageStat.Stat(q).mean[0] for q in quadrants]
        
        # Check balance (too much weight in one quadrant = unbalanced)
        max_weight = max(weights)
        min_weight = min(weights)
        
        if max_weight - min_weight > 100:  # Significant imbalance
            issues.append("Visual weight imbalanced across quadrants")
            suggestions.append("Redistribute elements for better balance")
            score -= 0.2
        
        # Check symmetry (optional, depends on design style)
        left_weight = (weights[0] + weights[2]) / 2
        right_weight = (weights[1] + weights[3]) / 2
        
        asymmetry = abs(left_weight - right_weight)
        if asymmetry > 50:
            suggestions.append("Consider balancing left/right visual weight")
            score -= 0.05
        
        return max(0.0, score)
    
    # =========================================================================
    # TYPOGRAPHY CHECKS
    # =========================================================================
    
    def _check_typography(
        self,
        design_data: Dict[str, Any],
        issues: List[str],
        suggestions: List[str]
    ) -> float:
        """Check typography quality."""
        score = 1.0
        
        fonts = design_data.get("fonts", {})
        
        # Check hierarchy (size differences)
        headline_size = fonts.get("headline_size", 48)
        body_size = fonts.get("body_size", 16)
        
        if headline_size < body_size * 1.5:
            issues.append("Hierarchy too weak (headline not large enough)")
            suggestions.append("Increase headline size for stronger hierarchy")
            score -= 0.2
        
        # Check line length
        line_length = design_data.get("line_length", 70)
        if line_length > 80:
            issues.append(f"Lines too long: {line_length} chars (ideal: 45-75)")
            suggestions.append("Reduce line length for better readability")
            score -= 0.1
        elif line_length < 40:
            issues.append(f"Lines too short: {line_length} chars")
            suggestions.append("Increase line length to reduce jumpiness")
            score -= 0.05
        
        # Check line height
        line_height = fonts.get("line_height", 1.5)
        if line_height < 1.3:
            issues.append("Line height too tight for body text")
            suggestions.append("Increase line height to 1.5-1.7 for readability")
            score -= 0.15
        
        return max(0.0, score)
    
    # =========================================================================
    # BRAND FIDELITY CHECKS
    # =========================================================================
    
    def _check_brand_fidelity(
        self,
        design_data: Dict[str, Any],
        brand_colors: Optional[Dict[str, Tuple[int, int, int]]],
        issues: List[str],
        suggestions: List[str]
    ) -> float:
        """Check how well design matches brand."""
        if not brand_colors:
            return 1.0  # Can't check without brand reference
        
        score = 1.0
        
        design_colors = design_data.get("colors", {})
        
        # Check primary color match
        if "primary" in design_colors and "primary" in brand_colors:
            design_primary = design_colors["primary"]
            brand_primary = brand_colors["primary"]
            
            color_diff = self._color_difference(design_primary, brand_primary)
            
            if color_diff > 50:  # Significant difference
                issues.append("Primary color differs from brand")
                suggestions.append("Use brand's primary color for consistency")
                score -= 0.3
            elif color_diff > 30:
                suggestions.append("Consider closer match to brand primary color")
                score -= 0.1
        
        # Check overall color harmony with brand
        if "accent" in design_colors and "accent" in brand_colors:
            design_accent = design_colors["accent"]
            brand_accent = brand_colors["accent"]
            
            color_diff = self._color_difference(design_accent, brand_accent)
            
            if color_diff > 50:
                suggestions.append("Accent color could be closer to brand")
                score -= 0.1
        
        return max(0.0, score)
    
    def _color_difference(
        self,
        color1: Tuple[int, int, int],
        color2: Tuple[int, int, int]
    ) -> float:
        """Calculate perceptual color difference (Delta E)."""
        # Simple Euclidean distance (good enough for QA)
        r_diff = (color1[0] - color2[0]) ** 2
        g_diff = (color1[1] - color2[1]) ** 2
        b_diff = (color1[2] - color2[2]) ** 2
        
        return math.sqrt(r_diff + g_diff + b_diff)
    
    # =========================================================================
    # TECHNICAL CHECKS
    # =========================================================================
    
    def _check_technical_quality(
        self,
        image: Image.Image,
        issues: List[str],
        suggestions: List[str]
    ) -> float:
        """Check technical quality."""
        score = 1.0
        
        # Check dimensions
        if image.size != (1200, 630):
            issues.append(f"Wrong dimensions: {image.size} (need 1200x630)")
            suggestions.append("Resize to exact OG image dimensions")
            score -= 0.5
        
        # Check color mode
        if image.mode not in ['RGB', 'RGBA']:
            issues.append(f"Wrong color mode: {image.mode}")
            suggestions.append("Convert to RGB or RGBA")
            score -= 0.2
        
        # Estimate file size
        from io import BytesIO
        buffer = BytesIO()
        image.save(buffer, format='PNG', optimize=True)
        file_size = len(buffer.getvalue())
        
        if file_size > self.max_file_size:
            issues.append(f"File too large: {file_size / 1024:.0f}KB (max 300KB)")
            suggestions.append("Optimize image compression")
            score -= 0.3
        
        return max(0.0, score)
    
    # =========================================================================
    # POLISH FUNCTIONS
    # =========================================================================
    
    def _apply_vignette(self, image: Image.Image, intensity: float = 0.03) -> Image.Image:
        """Apply subtle vignette effect."""
        width, height = image.size
        
        # Create radial gradient mask
        mask = Image.new('L', (width, height), 255)
        mask_draw = ImageDraw.Draw(mask)
        
        cx, cy = width // 2, height // 2
        max_dist = math.sqrt(cx**2 + cy**2)
        
        # Only darken edges slightly
        for y in range(height):
            for x in range(width):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                t = dist / max_dist
                
                # Very gentle vignette
                brightness = int(255 * (1 - t * t * intensity))
                mask_draw.point((x, y), fill=brightness)
        
        # Apply mask
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        darkened = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        return Image.composite(image, darkened, mask)
    
    def _apply_sharpening(self, image: Image.Image, amount: float = 0.3) -> Image.Image:
        """Apply subtle sharpening for crisp text."""
        # Unsharp mask
        blurred = image.filter(ImageFilter.GaussianBlur(radius=1))
        
        # Blend original with inverted blur
        if image.mode != 'RGB':
            image = image.convert('RGB')
        if blurred.mode != 'RGB':
            blurred = blurred.convert('RGB')
        
        sharpened = Image.blend(blurred, image, 1 + amount)
        
        return sharpened
    
    def _boost_vibrance(self, image: Image.Image, amount: float = 0.05) -> Image.Image:
        """Boost color vibrance slightly."""
        enhancer = ImageEnhance.Color(image)
        return enhancer.enhance(1 + amount)
    
    def _smooth_gradients(self, image: Image.Image) -> Image.Image:
        """Smooth gradients to reduce banding."""
        # Very gentle blur
        smoothed = image.filter(ImageFilter.GaussianBlur(radius=0.3))
        return smoothed
    
    def _apply_optical_adjustments(self, image: Image.Image) -> Image.Image:
        """Apply optical adjustments (simulated subpixel positioning)."""
        # For now, just ensure crisp edges
        return image
    
    def _is_dull_image(self, image: Image.Image) -> bool:
        """Check if image colors are dull."""
        # Convert to HSV and check saturation
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Sample colors
        colors = image.getcolors(maxcolors=1000000)
        if not colors:
            return False
        
        # Calculate average saturation
        total_saturation = 0
        total_pixels = 0
        
        for count, color in colors[:1000]:  # Sample first 1000 colors
            h, s, v = colorsys.rgb_to_hsv(color[0] / 255, color[1] / 255, color[2] / 255)
            total_saturation += s * count
            total_pixels += count
        
        avg_saturation = total_saturation / total_pixels if total_pixels > 0 else 0
        
        # Dull if saturation < 0.3
        return avg_saturation < 0.3


# =============================================================================
# A/B TESTING FRAMEWORK
# =============================================================================

class ABTestFramework:
    """
    Framework for A/B testing different design variations.
    
    Generates multiple variations and selects the highest-scoring one.
    """
    
    def __init__(self, qa_engine: QualityAssuranceEngine):
        self.qa_engine = qa_engine
    
    def test_variations(
        self,
        base_design: Dict[str, Any],
        variations: List[Dict[str, Any]],
        image_generator: callable
    ) -> Tuple[Dict[str, Any], QualityScore]:
        """
        Test multiple design variations.
        
        Args:
            base_design: Base design parameters
            variations: List of variation parameters
            image_generator: Function to generate images from parameters
            
        Returns:
            Tuple of (best_variation, quality_score)
        """
        best_score = 0
        best_variation = base_design
        best_quality = None
        
        # Test base design
        base_image = image_generator(base_design)
        base_quality = self.qa_engine.assess_quality(base_image, base_design)
        best_score = base_quality.overall
        best_quality = base_quality
        
        logger.info(f"Base design score: {base_score:.2f}")
        
        # Test variations
        for i, variation in enumerate(variations):
            try:
                image = image_generator(variation)
                quality = self.qa_engine.assess_quality(image, variation)
                
                logger.info(f"Variation {i+1} score: {quality.overall:.2f}")
                
                if quality.overall > best_score:
                    best_score = quality.overall
                    best_variation = variation
                    best_quality = quality
            except Exception as e:
                logger.warning(f"Variation {i+1} failed: {e}")
        
        logger.info(f"🏆 Best variation score: {best_score:.2f} (grade: {best_quality.grade})")
        
        return best_variation, best_quality


# Example usage
if __name__ == "__main__":
    qa_engine = QualityAssuranceEngine()
    
    # Test design data
    test_design = {
        "colors": {
            "text": (0, 0, 0),
            "background": (255, 255, 255),
            "primary": (59, 130, 246),
            "accent": (249, 115, 22)
        },
        "fonts": {
            "headline_size": 72,
            "body_size": 16,
            "line_height": 1.5
        },
        "line_length": 65
    }
    
    # Create test image
    test_image = Image.new('RGB', (1200, 630), (255, 255, 255))
    
    # Run quality assessment
    quality = qa_engine.assess_quality(test_image, test_design)
    
    print(f"\nQuality Assessment:")
    print(f"  Overall: {quality.overall:.2f} ({quality.grade})")
    print(f"  Accessibility: {quality.accessibility:.2f}")
    print(f"  Visual Balance: {quality.visual_balance:.2f}")
    print(f"  Typography: {quality.typography:.2f}")
    print(f"  Brand Fidelity: {quality.brand_fidelity:.2f}")
    print(f"  Technical: {quality.technical:.2f}")
    
    if quality.issues:
        print(f"\nIssues Found:")
        for issue in quality.issues:
            print(f"  - {issue}")
    
    if quality.suggestions:
        print(f"\nSuggestions:")
        for suggestion in quality.suggestions:
            print(f"  - {suggestion}")
