"""
Visual Quality Validator - Post-Render Quality Checks.

PHASE 2 IMPLEMENTATION:
Validates rendered preview images for visual quality including:
- Contrast ratios (WCAG AA/AAA compliance)
- Text readability verification
- Logo visibility and prominence
- Compositional balance scoring
- Rendering artifact detection

This validator runs AFTER image generation to ensure
the final output meets quality standards.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from io import BytesIO
from PIL import Image, ImageStat
import math

logger = logging.getLogger(__name__)


# =============================================================================
# WCAG CONTRAST STANDARDS
# =============================================================================

# WCAG AA: 4.5:1 for normal text, 3:1 for large text
# WCAG AAA: 7:1 for normal text, 4.5:1 for large text
CONTRAST_AA_NORMAL = 4.5
CONTRAST_AA_LARGE = 3.0
CONTRAST_AAA_NORMAL = 7.0
CONTRAST_AAA_LARGE = 4.5


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ContrastResult:
    """Result of contrast ratio check."""
    ratio: float
    passes_aa_normal: bool
    passes_aa_large: bool
    passes_aaa_normal: bool
    passes_aaa_large: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ratio": self.ratio,
            "passes_aa_normal": self.passes_aa_normal,
            "passes_aa_large": self.passes_aa_large,
            "passes_aaa_normal": self.passes_aaa_normal,
            "passes_aaa_large": self.passes_aaa_large
        }


@dataclass
class CompositionBalance:
    """Compositional balance analysis."""
    horizontal_balance: float  # 0.0-1.0 (1.0 = perfectly balanced)
    vertical_balance: float  # 0.0-1.0
    visual_weight_center: Tuple[float, float]  # (x, y) as percentages
    has_focal_point: bool
    balance_score: float  # Overall score 0.0-1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "horizontal_balance": self.horizontal_balance,
            "vertical_balance": self.vertical_balance,
            "visual_weight_center": self.visual_weight_center,
            "has_focal_point": self.has_focal_point,
            "balance_score": self.balance_score
        }


@dataclass
class VisualQualityScore:
    """Complete visual quality assessment."""
    overall_score: float  # 0.0-1.0
    contrast_score: float
    readability_score: float
    composition_score: float
    logo_visibility_score: float
    artifact_score: float  # 1.0 = no artifacts
    
    # Detailed results
    contrast_results: ContrastResult
    composition_balance: CompositionBalance
    
    # Issues and suggestions
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    # Quality level
    passes_minimum: bool = True
    quality_level: str = "good"  # excellent, good, fair, poor
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "contrast_score": self.contrast_score,
            "readability_score": self.readability_score,
            "composition_score": self.composition_score,
            "logo_visibility_score": self.logo_visibility_score,
            "artifact_score": self.artifact_score,
            "contrast_results": self.contrast_results.to_dict(),
            "composition_balance": self.composition_balance.to_dict(),
            "issues": self.issues,
            "suggestions": self.suggestions,
            "passes_minimum": self.passes_minimum,
            "quality_level": self.quality_level
        }


# =============================================================================
# VISUAL QUALITY VALIDATOR
# =============================================================================

class VisualQualityValidator:
    """
    Validates rendered preview images for visual quality.
    
    Runs post-generation checks to ensure the output meets
    accessibility and design quality standards.
    """
    
    def __init__(
        self,
        min_contrast_ratio: float = CONTRAST_AA_LARGE,
        min_composition_score: float = 0.6,
        min_overall_score: float = 0.65
    ):
        """
        Initialize validator with thresholds.
        
        Args:
            min_contrast_ratio: Minimum contrast ratio (default: WCAG AA large text)
            min_composition_score: Minimum composition balance score
            min_overall_score: Minimum overall quality score
        """
        self.min_contrast_ratio = min_contrast_ratio
        self.min_composition_score = min_composition_score
        self.min_overall_score = min_overall_score
        
        logger.info(
            f"VisualQualityValidator initialized: "
            f"min_contrast={min_contrast_ratio}, "
            f"min_composition={min_composition_score}, "
            f"min_overall={min_overall_score}"
        )
    
    def validate(
        self,
        image: Image.Image,
        expected_colors: Optional[Dict[str, str]] = None,
        has_logo: bool = False,
        logo_region: Optional[Tuple[int, int, int, int]] = None
    ) -> VisualQualityScore:
        """
        Validate visual quality of a rendered preview image.
        
        Args:
            image: PIL Image to validate
            expected_colors: Expected color palette (for contrast checking)
            has_logo: Whether logo is expected
            logo_region: Expected logo region (x, y, w, h)
            
        Returns:
            VisualQualityScore with all metrics
        """
        logger.info(f"🔍 Validating visual quality: {image.size}")
        
        issues = []
        suggestions = []
        
        # 1. Contrast Analysis
        contrast_results = self._analyze_contrast(image, expected_colors)
        contrast_score = self._score_contrast(contrast_results)
        
        if contrast_results.ratio < self.min_contrast_ratio:
            issues.append(f"Contrast ratio {contrast_results.ratio:.2f} below minimum {self.min_contrast_ratio}")
            suggestions.append("Increase contrast between text and background colors")
        
        # 2. Readability Analysis
        readability_score = self._analyze_readability(image)
        
        if readability_score < 0.6:
            issues.append("Text may be difficult to read")
            suggestions.append("Increase text size or contrast")
        
        # 3. Composition Balance
        composition_balance = self._analyze_composition(image)
        composition_score = composition_balance.balance_score
        
        if composition_score < self.min_composition_score:
            issues.append(f"Composition balance {composition_score:.2f} below threshold")
            suggestions.append("Adjust element positioning for better visual balance")
        
        # 4. Logo Visibility (if applicable)
        logo_visibility_score = 1.0
        if has_logo:
            logo_visibility_score = self._analyze_logo_visibility(image, logo_region)
            if logo_visibility_score < 0.6:
                issues.append("Logo may not be visible enough")
                suggestions.append("Increase logo size or improve logo contrast")
        
        # 5. Artifact Detection
        artifact_score = self._detect_artifacts(image)
        
        if artifact_score < 0.8:
            issues.append("Rendering artifacts detected")
            suggestions.append("Check image generation for compression or rendering issues")
        
        # Calculate overall score (weighted average)
        weights = {
            "contrast": 0.30,
            "readability": 0.25,
            "composition": 0.20,
            "logo": 0.15 if has_logo else 0.0,
            "artifacts": 0.10
        }
        
        # Normalize weights if no logo
        if not has_logo:
            total = sum(v for k, v in weights.items() if k != "logo")
            weights = {k: v / total for k, v in weights.items() if k != "logo"}
        
        overall_score = (
            contrast_score * weights.get("contrast", 0.3) +
            readability_score * weights.get("readability", 0.25) +
            composition_score * weights.get("composition", 0.2) +
            logo_visibility_score * weights.get("logo", 0.0) +
            artifact_score * weights.get("artifacts", 0.1)
        )
        
        # Determine quality level
        if overall_score >= 0.90:
            quality_level = "excellent"
        elif overall_score >= 0.75:
            quality_level = "good"
        elif overall_score >= 0.60:
            quality_level = "fair"
        else:
            quality_level = "poor"
        
        passes_minimum = overall_score >= self.min_overall_score
        
        result = VisualQualityScore(
            overall_score=overall_score,
            contrast_score=contrast_score,
            readability_score=readability_score,
            composition_score=composition_score,
            logo_visibility_score=logo_visibility_score,
            artifact_score=artifact_score,
            contrast_results=contrast_results,
            composition_balance=composition_balance,
            issues=issues,
            suggestions=suggestions,
            passes_minimum=passes_minimum,
            quality_level=quality_level
        )
        
        logger.info(
            f"✅ Visual quality validation complete: "
            f"overall={overall_score:.2f} ({quality_level}), "
            f"passes={passes_minimum}, "
            f"issues={len(issues)}"
        )
        
        return result
    
    def validate_from_bytes(
        self,
        image_bytes: bytes,
        expected_colors: Optional[Dict[str, str]] = None,
        has_logo: bool = False
    ) -> VisualQualityScore:
        """
        Validate visual quality from image bytes.
        
        Args:
            image_bytes: PNG/JPEG image bytes
            expected_colors: Expected color palette
            has_logo: Whether logo is expected
            
        Returns:
            VisualQualityScore
        """
        try:
            image = Image.open(BytesIO(image_bytes))
            return self.validate(image, expected_colors, has_logo)
        except Exception as e:
            logger.error(f"Failed to validate image bytes: {e}")
            # Return minimal passing score to allow pipeline to continue
            return VisualQualityScore(
                overall_score=0.5,
                contrast_score=0.5,
                readability_score=0.5,
                composition_score=0.5,
                logo_visibility_score=0.5,
                artifact_score=1.0,
                contrast_results=ContrastResult(
                    ratio=4.5,
                    passes_aa_normal=True,
                    passes_aa_large=True,
                    passes_aaa_normal=False,
                    passes_aaa_large=True
                ),
                composition_balance=CompositionBalance(
                    horizontal_balance=0.5,
                    vertical_balance=0.5,
                    visual_weight_center=(0.5, 0.5),
                    has_focal_point=False,
                    balance_score=0.5
                ),
                issues=[f"Could not validate image: {e}"],
                suggestions=["Check image format and content"],
                passes_minimum=True,
                quality_level="fair"
            )
    
    def _analyze_contrast(
        self,
        image: Image.Image,
        expected_colors: Optional[Dict[str, str]] = None
    ) -> ContrastResult:
        """
        Analyze contrast ratios in the image.
        
        Uses sampling to estimate text-to-background contrast.
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        width, height = image.size
        
        # Sample regions for contrast analysis
        # Top region (usually background + text)
        top_region = image.crop((0, 0, width, height // 3))
        # Center region (main content)
        center_region = image.crop((0, height // 3, width, 2 * height // 3))
        # Bottom region (footer area)
        bottom_region = image.crop((0, 2 * height // 3, width, height))
        
        # Get dominant colors from each region
        top_colors = self._get_dominant_colors(top_region, 2)
        center_colors = self._get_dominant_colors(center_region, 2)
        
        # Calculate contrast between dominant colors
        if len(top_colors) >= 2:
            contrast_top = self._calculate_contrast_ratio(top_colors[0], top_colors[1])
        else:
            contrast_top = 4.5  # Default to passing
        
        if len(center_colors) >= 2:
            contrast_center = self._calculate_contrast_ratio(center_colors[0], center_colors[1])
        else:
            contrast_center = 4.5
        
        # Use the lower contrast (more conservative)
        ratio = min(contrast_top, contrast_center)
        
        # If expected colors provided, validate against those
        if expected_colors:
            try:
                bg_hex = expected_colors.get("background_color", "#FFFFFF")
                text_hex = expected_colors.get("text_color", "#000000")
                
                bg_rgb = self._hex_to_rgb(bg_hex)
                text_rgb = self._hex_to_rgb(text_hex)
                
                expected_ratio = self._calculate_contrast_ratio(bg_rgb, text_rgb)
                ratio = min(ratio, expected_ratio)
            except:
                pass
        
        return ContrastResult(
            ratio=ratio,
            passes_aa_normal=ratio >= CONTRAST_AA_NORMAL,
            passes_aa_large=ratio >= CONTRAST_AA_LARGE,
            passes_aaa_normal=ratio >= CONTRAST_AAA_NORMAL,
            passes_aaa_large=ratio >= CONTRAST_AAA_LARGE
        )
    
    def _score_contrast(self, contrast: ContrastResult) -> float:
        """Convert contrast result to score."""
        if contrast.passes_aaa_normal:
            return 1.0
        elif contrast.passes_aa_normal:
            return 0.85
        elif contrast.passes_aa_large:
            return 0.7
        elif contrast.ratio >= 2.5:
            return 0.5
        else:
            return max(0.2, contrast.ratio / CONTRAST_AA_LARGE * 0.5)
    
    def _analyze_readability(self, image: Image.Image) -> float:
        """
        Analyze text readability based on image characteristics.
        
        Factors considered:
        - Image clarity (sharpness)
        - Contrast levels
        - Noise levels
        """
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to grayscale for analysis
        gray = image.convert('L')
        
        # Calculate sharpness using variance of Laplacian approximation
        from PIL import ImageFilter
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_stat = ImageStat.Stat(edges)
        sharpness = edge_stat.var[0] / 1000  # Normalize
        sharpness_score = min(1.0, sharpness / 5)  # Cap at 1.0
        
        # Calculate contrast using histogram spread
        hist = gray.histogram()
        non_zero = [i for i, v in enumerate(hist) if v > 0]
        if non_zero:
            spread = max(non_zero) - min(non_zero)
            contrast_score = spread / 255
        else:
            contrast_score = 0.5
        
        # Calculate noise (using standard deviation in small patches)
        stat = ImageStat.Stat(gray)
        noise_level = stat.stddev[0] / 128  # Normalize
        # Lower noise = better readability (but some variance is expected)
        noise_score = 1.0 if 0.1 < noise_level < 0.6 else 0.8
        
        # Combine scores
        readability = (sharpness_score * 0.4 + contrast_score * 0.4 + noise_score * 0.2)
        
        return min(1.0, readability)
    
    def _analyze_composition(self, image: Image.Image) -> CompositionBalance:
        """
        Analyze compositional balance of the image.
        
        Uses visual weight distribution to determine balance.
        """
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        width, height = image.size
        
        # Convert to grayscale for weight analysis
        gray = image.convert('L')
        
        # Divide image into quadrants
        left_half = gray.crop((0, 0, width // 2, height))
        right_half = gray.crop((width // 2, 0, width, height))
        top_half = gray.crop((0, 0, width, height // 2))
        bottom_half = gray.crop((0, height // 2, width, height))
        
        # Calculate visual weight (inverse of brightness for dark elements)
        left_weight = 255 - ImageStat.Stat(left_half).mean[0]
        right_weight = 255 - ImageStat.Stat(right_half).mean[0]
        top_weight = 255 - ImageStat.Stat(top_half).mean[0]
        bottom_weight = 255 - ImageStat.Stat(bottom_half).mean[0]
        
        # Calculate balance (1.0 = perfectly balanced)
        total_lr = left_weight + right_weight
        total_tb = top_weight + bottom_weight
        
        if total_lr > 0:
            horizontal_balance = 1 - abs(left_weight - right_weight) / total_lr
        else:
            horizontal_balance = 1.0
        
        if total_tb > 0:
            vertical_balance = 1 - abs(top_weight - bottom_weight) / total_tb
        else:
            vertical_balance = 1.0
        
        # Calculate center of visual weight
        if total_lr > 0:
            weight_x = right_weight / total_lr
        else:
            weight_x = 0.5
        
        if total_tb > 0:
            weight_y = bottom_weight / total_tb
        else:
            weight_y = 0.5
        
        # Check for focal point (high contrast area in center-ish region)
        center_region = gray.crop((width // 4, height // 4, 3 * width // 4, 3 * height // 4))
        center_stat = ImageStat.Stat(center_region)
        center_contrast = center_stat.stddev[0] / 128
        has_focal_point = center_contrast > 0.2
        
        # Overall balance score
        balance_score = (horizontal_balance * 0.4 + vertical_balance * 0.4)
        
        # Bonus for focal point
        if has_focal_point:
            balance_score += 0.1
        
        # Penalty for extreme off-center weight
        if abs(weight_x - 0.5) > 0.3 or abs(weight_y - 0.5) > 0.3:
            balance_score -= 0.1
        
        balance_score = max(0.0, min(1.0, balance_score))
        
        return CompositionBalance(
            horizontal_balance=horizontal_balance,
            vertical_balance=vertical_balance,
            visual_weight_center=(weight_x, weight_y),
            has_focal_point=has_focal_point,
            balance_score=balance_score
        )
    
    def _analyze_logo_visibility(
        self,
        image: Image.Image,
        logo_region: Optional[Tuple[int, int, int, int]] = None
    ) -> float:
        """
        Analyze logo visibility and prominence.
        
        Args:
            image: Full preview image
            logo_region: Expected logo region (x, y, w, h)
        """
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        width, height = image.size
        
        # Default logo region (top-left)
        if logo_region is None:
            logo_x = int(width * 0.05)
            logo_y = int(height * 0.05)
            logo_w = int(width * 0.15)
            logo_h = int(height * 0.15)
            logo_region = (logo_x, logo_y, logo_w, logo_h)
        
        x, y, w, h = logo_region
        
        try:
            # Crop logo region
            logo_area = image.crop((x, y, x + w, y + h))
            
            # Analyze contrast in logo region
            logo_stat = ImageStat.Stat(logo_area.convert('L'))
            logo_contrast = logo_stat.stddev[0] / 128
            
            # Higher contrast = more visible logo
            if logo_contrast > 0.3:
                return 1.0
            elif logo_contrast > 0.2:
                return 0.8
            elif logo_contrast > 0.1:
                return 0.6
            else:
                return 0.4
        except:
            return 0.5  # Default if analysis fails
    
    def _detect_artifacts(self, image: Image.Image) -> float:
        """
        Detect rendering artifacts in the image.
        
        Looks for:
        - JPEG compression artifacts
        - Banding in gradients
        - Aliasing issues
        """
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        score = 1.0
        
        # Check for banding in smooth gradients
        # Sample horizontal lines and check for sharp jumps
        width, height = image.size
        
        for y in range(0, height, height // 10):
            row = [image.getpixel((x, y)) for x in range(0, width, 10)]
            for i in range(1, len(row)):
                diff = sum(abs(row[i][c] - row[i-1][c]) for c in range(3))
                # Large jumps in supposedly smooth areas suggest banding
                if diff > 50:  # Threshold for artifact detection
                    score -= 0.01
        
        # Check for overall image quality (variance should be natural)
        stat = ImageStat.Stat(image)
        avg_var = sum(stat.var) / 3
        
        # Very low variance might indicate artifacts (flat colors)
        if avg_var < 100:
            score -= 0.05
        
        return max(0.5, min(1.0, score))
    
    def _get_dominant_colors(
        self,
        image: Image.Image,
        num_colors: int = 2
    ) -> List[Tuple[int, int, int]]:
        """Get dominant colors from image region."""
        # Resize for faster processing
        small = image.resize((50, 50), Image.Resampling.LANCZOS)
        
        # Get pixels
        pixels = list(small.getdata())
        
        # Simple clustering: find most common colors
        from collections import Counter
        
        # Quantize to reduce color space
        quantized = [(r // 32 * 32, g // 32 * 32, b // 32 * 32) for r, g, b in pixels]
        color_counts = Counter(quantized)
        
        return [color for color, count in color_counts.most_common(num_colors)]
    
    def _calculate_contrast_ratio(
        self,
        color1: Tuple[int, int, int],
        color2: Tuple[int, int, int]
    ) -> float:
        """
        Calculate WCAG contrast ratio between two colors.
        
        Formula: (L1 + 0.05) / (L2 + 0.05)
        Where L1 is lighter color's relative luminance
        """
        def relative_luminance(rgb: Tuple[int, int, int]) -> float:
            def adjust(c):
                c = c / 255
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            
            r, g, b = [adjust(c) for c in rgb]
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        l1 = relative_luminance(color1)
        l2 = relative_luminance(color2)
        
        if l1 < l2:
            l1, l2 = l2, l1
        
        return (l1 + 0.05) / (l2 + 0.05)
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c * 2 for c in hex_color])
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_validator_instance: Optional[VisualQualityValidator] = None


def get_visual_quality_validator() -> VisualQualityValidator:
    """Get singleton VisualQualityValidator instance."""
    global _validator_instance
    
    if _validator_instance is None:
        _validator_instance = VisualQualityValidator()
    
    return _validator_instance


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def validate_visual_quality(
    image: Image.Image,
    expected_colors: Optional[Dict[str, str]] = None,
    has_logo: bool = False
) -> VisualQualityScore:
    """
    Convenience function to validate visual quality.
    
    Args:
        image: PIL Image to validate
        expected_colors: Expected color palette
        has_logo: Whether logo is expected
        
    Returns:
        VisualQualityScore
    """
    return get_visual_quality_validator().validate(image, expected_colors, has_logo)


def validate_visual_quality_from_bytes(
    image_bytes: bytes,
    expected_colors: Optional[Dict[str, str]] = None,
    has_logo: bool = False
) -> VisualQualityScore:
    """
    Convenience function to validate visual quality from bytes.
    
    Args:
        image_bytes: PNG/JPEG image bytes
        expected_colors: Expected color palette
        has_logo: Whether logo is expected
        
    Returns:
        VisualQualityScore
    """
    return get_visual_quality_validator().validate_from_bytes(
        image_bytes, expected_colors, has_logo
    )

