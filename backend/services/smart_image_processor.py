"""
Smart Image Processor - Intelligent Image Quality & Enhancement.

PHASE 3 IMPLEMENTATION:
Goes beyond simple image extraction to provide:
- Image quality scoring (blur, resolution, composition)
- Focus region detection (faces, products, text areas)
- Intelligent cropping for target aspect ratios
- Automatic image enhancement (color, contrast, sharpness)
- Stock photo detection and filtering

This is the "image intelligence" layer that ensures only
high-quality, relevant images are used in previews.
"""

import logging
import math
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from io import BytesIO
from PIL import Image, ImageFilter, ImageStat, ImageEnhance, ImageOps
import base64

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Quality thresholds
MIN_IMAGE_WIDTH = 200
MIN_IMAGE_HEIGHT = 200
IDEAL_MIN_WIDTH = 400
IDEAL_MIN_HEIGHT = 300

# Quality score weights
QUALITY_WEIGHTS = {
    "resolution": 0.25,
    "sharpness": 0.25,
    "composition": 0.20,
    "color_quality": 0.15,
    "uniqueness": 0.15
}

# Common aspect ratios
ASPECT_RATIOS = {
    "og_image": 1200 / 630,  # 1.905
    "twitter": 1200 / 600,   # 2.0
    "square": 1.0,
    "portrait": 4 / 5,       # 0.8
    "landscape": 16 / 9      # 1.778
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FocusRegion:
    """Detected focus region in image."""
    x: float  # 0.0-1.0 relative position
    y: float
    width: float
    height: float
    type: str  # face, product, text, logo, generic
    confidence: float
    importance: float  # 0.0-1.0


@dataclass
class ImageQualityScore:
    """Complete image quality assessment."""
    overall_score: float  # 0.0-1.0
    resolution_score: float
    sharpness_score: float
    composition_score: float
    color_quality_score: float
    uniqueness_score: float  # How unique/non-stock the image is
    
    # Detailed metrics
    width: int
    height: int
    blur_amount: float
    contrast_level: float
    saturation_level: float
    
    # Focus regions
    focus_regions: List[FocusRegion] = field(default_factory=list)
    
    # Recommendations
    is_usable: bool = True
    is_stock_photo: bool = False
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "resolution_score": self.resolution_score,
            "sharpness_score": self.sharpness_score,
            "composition_score": self.composition_score,
            "color_quality_score": self.color_quality_score,
            "uniqueness_score": self.uniqueness_score,
            "width": self.width,
            "height": self.height,
            "blur_amount": self.blur_amount,
            "contrast_level": self.contrast_level,
            "saturation_level": self.saturation_level,
            "is_usable": self.is_usable,
            "is_stock_photo": self.is_stock_photo,
            "recommendations": self.recommendations
        }


@dataclass
class EnhancementResult:
    """Result of image enhancement."""
    image: Image.Image
    enhancements_applied: List[str]
    quality_improvement: float
    before_score: float
    after_score: float


# =============================================================================
# SMART IMAGE PROCESSOR
# =============================================================================

class SmartImageProcessor:
    """
    Intelligent image processing for preview generation.
    
    Scores, selects, crops, and enhances images to ensure
    high-quality visual content in previews.
    """
    
    def __init__(
        self,
        min_quality_score: float = 0.4,
        enable_enhancement: bool = True,
        detect_stock_photos: bool = True
    ):
        """
        Initialize processor.
        
        Args:
            min_quality_score: Minimum quality score to accept image
            enable_enhancement: Whether to auto-enhance low-quality images
            detect_stock_photos: Whether to try detecting stock photos
        """
        self.min_quality_score = min_quality_score
        self.enable_enhancement = enable_enhancement
        self.detect_stock_photos = detect_stock_photos
        
        logger.info(
            f"SmartImageProcessor initialized: "
            f"min_quality={min_quality_score}, "
            f"enhancement={enable_enhancement}"
        )
    
    def score_image(
        self,
        image: Image.Image,
        expected_type: str = "generic"
    ) -> ImageQualityScore:
        """
        Score image quality comprehensively.
        
        Args:
            image: PIL Image to score
            expected_type: Expected content type (face, product, logo, generic)
            
        Returns:
            ImageQualityScore with all metrics
        """
        logger.info(f"📊 Scoring image quality: {image.size}")
        
        # Ensure RGB mode
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        width, height = image.size
        recommendations = []
        
        # 1. Resolution score
        resolution_score = self._score_resolution(width, height)
        if resolution_score < 0.5:
            recommendations.append("Consider using a higher resolution image")
        
        # 2. Sharpness score (blur detection)
        sharpness_score, blur_amount = self._score_sharpness(image)
        if sharpness_score < 0.5:
            recommendations.append("Image appears blurry")
        
        # 3. Composition score
        composition_score = self._score_composition(image)
        if composition_score < 0.5:
            recommendations.append("Image composition could be improved")
        
        # 4. Color quality score
        color_quality_score, contrast, saturation = self._score_color_quality(image)
        if color_quality_score < 0.5:
            recommendations.append("Color quality is low")
        
        # 5. Uniqueness score (stock photo detection)
        uniqueness_score = 1.0
        is_stock = False
        if self.detect_stock_photos:
            uniqueness_score, is_stock = self._score_uniqueness(image)
            if is_stock:
                recommendations.append("Image appears to be a stock photo")
        
        # 6. Detect focus regions
        focus_regions = self._detect_focus_regions(image, expected_type)
        
        # Calculate overall score
        overall_score = (
            resolution_score * QUALITY_WEIGHTS["resolution"] +
            sharpness_score * QUALITY_WEIGHTS["sharpness"] +
            composition_score * QUALITY_WEIGHTS["composition"] +
            color_quality_score * QUALITY_WEIGHTS["color_quality"] +
            uniqueness_score * QUALITY_WEIGHTS["uniqueness"]
        )
        
        # Determine if usable
        is_usable = (
            overall_score >= self.min_quality_score and
            width >= MIN_IMAGE_WIDTH and
            height >= MIN_IMAGE_HEIGHT
        )
        
        return ImageQualityScore(
            overall_score=overall_score,
            resolution_score=resolution_score,
            sharpness_score=sharpness_score,
            composition_score=composition_score,
            color_quality_score=color_quality_score,
            uniqueness_score=uniqueness_score,
            width=width,
            height=height,
            blur_amount=blur_amount,
            contrast_level=contrast,
            saturation_level=saturation,
            focus_regions=focus_regions,
            is_usable=is_usable,
            is_stock_photo=is_stock,
            recommendations=recommendations
        )
    
    def score_from_bytes(
        self,
        image_bytes: bytes,
        expected_type: str = "generic"
    ) -> ImageQualityScore:
        """Score image quality from bytes."""
        try:
            image = Image.open(BytesIO(image_bytes))
            return self.score_image(image, expected_type)
        except Exception as e:
            logger.error(f"Failed to score image bytes: {e}")
            return ImageQualityScore(
                overall_score=0.0,
                resolution_score=0.0,
                sharpness_score=0.0,
                composition_score=0.0,
                color_quality_score=0.0,
                uniqueness_score=0.0,
                width=0,
                height=0,
                blur_amount=0.0,
                contrast_level=0.0,
                saturation_level=0.0,
                is_usable=False,
                recommendations=["Could not analyze image"]
            )
    
    def smart_crop(
        self,
        image: Image.Image,
        target_ratio: float = ASPECT_RATIOS["og_image"],
        focus_region: Optional[FocusRegion] = None
    ) -> Image.Image:
        """
        Intelligently crop image to target aspect ratio.
        
        Preserves important content by focusing on detected regions.
        
        Args:
            image: PIL Image to crop
            target_ratio: Target width/height ratio
            focus_region: Optional focus region to preserve
            
        Returns:
            Cropped PIL Image
        """
        width, height = image.size
        current_ratio = width / height
        
        # If already correct ratio, return as-is
        if abs(current_ratio - target_ratio) < 0.01:
            return image
        
        # Detect focus if not provided
        if focus_region is None:
            score = self.score_image(image)
            if score.focus_regions:
                focus_region = max(score.focus_regions, key=lambda r: r.importance)
        
        # Calculate crop dimensions
        if current_ratio > target_ratio:
            # Image is too wide - crop width
            new_width = int(height * target_ratio)
            new_height = height
            
            # Center on focus region if available
            if focus_region:
                focus_center_x = int(focus_region.x * width + focus_region.width * width / 2)
                left = focus_center_x - new_width // 2
            else:
                left = (width - new_width) // 2
            
            left = max(0, min(left, width - new_width))
            top = 0
            
        else:
            # Image is too tall - crop height
            new_width = width
            new_height = int(width / target_ratio)
            
            # Center on focus region if available
            if focus_region:
                focus_center_y = int(focus_region.y * height + focus_region.height * height / 2)
                top = focus_center_y - new_height // 2
            else:
                # Rule of thirds - crop from bottom (usually more interesting at top)
                top = int((height - new_height) * 0.3)
            
            top = max(0, min(top, height - new_height))
            left = 0
        
        cropped = image.crop((left, top, left + new_width, top + new_height))
        
        logger.info(
            f"Smart crop: {width}x{height} → {new_width}x{new_height}, "
            f"focus={focus_region.type if focus_region else 'center'}"
        )
        
        return cropped
    
    def enhance_image(
        self,
        image: Image.Image,
        quality_score: Optional[ImageQualityScore] = None
    ) -> EnhancementResult:
        """
        Automatically enhance image quality.
        
        Args:
            image: PIL Image to enhance
            quality_score: Optional pre-computed quality score
            
        Returns:
            EnhancementResult with enhanced image
        """
        if not self.enable_enhancement:
            return EnhancementResult(
                image=image,
                enhancements_applied=[],
                quality_improvement=0.0,
                before_score=0.0,
                after_score=0.0
            )
        
        logger.info("🎨 Enhancing image quality...")
        
        # Get initial score
        if quality_score is None:
            quality_score = self.score_image(image)
        before_score = quality_score.overall_score
        
        enhanced = image.copy()
        enhancements = []
        
        # 1. Sharpening (if blurry)
        if quality_score.sharpness_score < 0.6:
            enhanced = self._apply_sharpening(enhanced, quality_score.blur_amount)
            enhancements.append("sharpening")
        
        # 2. Contrast adjustment
        if quality_score.contrast_level < 0.4:
            enhanced = self._adjust_contrast(enhanced)
            enhancements.append("contrast")
        
        # 3. Saturation boost (if dull)
        if quality_score.saturation_level < 0.3:
            enhanced = self._boost_saturation(enhanced)
            enhancements.append("saturation")
        
        # 4. Auto color correction
        if quality_score.color_quality_score < 0.5:
            enhanced = self._auto_color_correct(enhanced)
            enhancements.append("color_correction")
        
        # 5. Noise reduction (subtle)
        if quality_score.sharpness_score < 0.4:
            enhanced = self._reduce_noise(enhanced)
            enhancements.append("noise_reduction")
        
        # Calculate improvement
        after_quality = self.score_image(enhanced)
        after_score = after_quality.overall_score
        improvement = after_score - before_score
        
        logger.info(
            f"✅ Enhancement complete: {len(enhancements)} applied, "
            f"score {before_score:.2f} → {after_score:.2f} "
            f"({improvement:+.2f})"
        )
        
        return EnhancementResult(
            image=enhanced,
            enhancements_applied=enhancements,
            quality_improvement=improvement,
            before_score=before_score,
            after_score=after_score
        )
    
    def select_best_image(
        self,
        images: List[Image.Image],
        expected_type: str = "generic"
    ) -> Tuple[Optional[Image.Image], Optional[ImageQualityScore]]:
        """
        Select the best image from a list.
        
        Args:
            images: List of PIL Images to choose from
            expected_type: Expected content type
            
        Returns:
            Tuple of (best_image, quality_score) or (None, None)
        """
        if not images:
            return None, None
        
        best_image = None
        best_score = None
        best_overall = 0.0
        
        for image in images:
            score = self.score_image(image, expected_type)
            
            if score.is_usable and score.overall_score > best_overall:
                best_overall = score.overall_score
                best_image = image
                best_score = score
        
        if best_image:
            logger.info(f"Selected best image: score={best_overall:.2f}")
        else:
            logger.warning("No usable images found")
        
        return best_image, best_score
    
    def process_for_preview(
        self,
        image: Image.Image,
        target_size: Tuple[int, int] = (1200, 630),
        enhance: bool = True
    ) -> Tuple[Image.Image, ImageQualityScore]:
        """
        Complete processing pipeline for preview images.
        
        Args:
            image: Input PIL Image
            target_size: Target dimensions (width, height)
            enhance: Whether to enhance the image
            
        Returns:
            Tuple of (processed_image, quality_score)
        """
        target_ratio = target_size[0] / target_size[1]
        
        # 1. Score the image
        score = self.score_image(image)
        
        # 2. Smart crop to target ratio
        cropped = self.smart_crop(image, target_ratio, 
                                  score.focus_regions[0] if score.focus_regions else None)
        
        # 3. Enhance if needed
        if enhance and score.overall_score < 0.7:
            result = self.enhance_image(cropped, score)
            cropped = result.image
            score = self.score_image(cropped)
        
        # 4. Resize to target dimensions
        resized = cropped.resize(target_size, Image.Resampling.LANCZOS)
        
        return resized, score
    
    # =========================================================================
    # SCORING METHODS
    # =========================================================================
    
    def _score_resolution(self, width: int, height: int) -> float:
        """Score image resolution."""
        pixels = width * height
        ideal_pixels = IDEAL_MIN_WIDTH * IDEAL_MIN_HEIGHT
        
        if pixels >= ideal_pixels:
            return 1.0
        elif pixels >= MIN_IMAGE_WIDTH * MIN_IMAGE_HEIGHT:
            return 0.5 + 0.5 * (pixels / ideal_pixels)
        else:
            return max(0.0, pixels / (MIN_IMAGE_WIDTH * MIN_IMAGE_HEIGHT) * 0.5)
    
    def _score_sharpness(self, image: Image.Image) -> Tuple[float, float]:
        """
        Score image sharpness and detect blur.
        
        Returns:
            Tuple of (score, blur_amount)
        """
        # Convert to grayscale
        gray = image.convert('L')
        
        # Apply Laplacian-like edge detection
        edges = gray.filter(ImageFilter.FIND_EDGES)
        
        # Calculate variance of edge image
        stat = ImageStat.Stat(edges)
        variance = stat.var[0]
        
        # Higher variance = sharper image
        # Typical ranges: <100 (very blurry), 100-500 (moderate), >500 (sharp)
        blur_amount = 1.0 - min(1.0, variance / 500)
        
        if variance > 500:
            score = 1.0
        elif variance > 200:
            score = 0.7 + (variance - 200) / 1000
        elif variance > 100:
            score = 0.4 + (variance - 100) / 333
        else:
            score = max(0.1, variance / 250)
        
        return score, blur_amount
    
    def _score_composition(self, image: Image.Image) -> float:
        """Score image composition using rule of thirds and balance."""
        width, height = image.size
        gray = image.convert('L')
        
        # Divide into 9 regions (3x3 grid)
        region_weights = []
        for row in range(3):
            for col in range(3):
                x1 = col * width // 3
                x2 = (col + 1) * width // 3
                y1 = row * height // 3
                y2 = (row + 1) * height // 3
                
                region = gray.crop((x1, y1, x2, y2))
                stat = ImageStat.Stat(region)
                
                # Visual weight = contrast/variance
                weight = stat.stddev[0]
                region_weights.append(weight)
        
        # Check if visual interest is at rule-of-thirds intersections
        # Intersection indices: 0, 2, 6, 8 (corners), 1, 3, 5, 7 (edges), 4 (center)
        corner_weight = (region_weights[0] + region_weights[2] + 
                        region_weights[6] + region_weights[8]) / 4
        edge_weight = (region_weights[1] + region_weights[3] + 
                      region_weights[5] + region_weights[7]) / 4
        center_weight = region_weights[4]
        
        # Good composition: some activity at thirds intersections
        total_weight = sum(region_weights)
        if total_weight < 1:
            return 0.5  # Very low contrast image
        
        thirds_ratio = corner_weight / (total_weight / 9)
        
        # Balance check
        left_weight = sum(region_weights[0:3:1]) + sum(region_weights[3:6:1]) + sum(region_weights[6:9:1])
        right_weight = sum(region_weights[0:9:3])  # This is wrong, fix:
        left_side = region_weights[0] + region_weights[3] + region_weights[6]
        right_side = region_weights[2] + region_weights[5] + region_weights[8]
        balance = 1 - abs(left_side - right_side) / max(left_side + right_side, 1)
        
        score = 0.5 * min(1.0, thirds_ratio) + 0.5 * balance
        
        return score
    
    def _score_color_quality(self, image: Image.Image) -> Tuple[float, float, float]:
        """
        Score color quality.
        
        Returns:
            Tuple of (score, contrast_level, saturation_level)
        """
        # Get image statistics
        stat = ImageStat.Stat(image)
        
        # Calculate contrast (using standard deviation across channels)
        contrast = sum(stat.stddev) / (3 * 128)  # Normalize to 0-1 range
        
        # Calculate saturation
        # Convert a sample to HSV and check saturation
        small = image.resize((50, 50), Image.Resampling.LANCZOS)
        pixels = list(small.getdata())
        
        saturations = []
        for r, g, b in pixels:
            max_c = max(r, g, b)
            min_c = min(r, g, b)
            if max_c > 0:
                saturation = (max_c - min_c) / max_c
                saturations.append(saturation)
        
        avg_saturation = sum(saturations) / len(saturations) if saturations else 0
        
        # Score based on balanced contrast and saturation
        contrast_score = min(1.0, contrast * 2)  # Normalize
        saturation_score = min(1.0, avg_saturation * 2)  # Some saturation is good
        
        # Penalize extreme values
        if avg_saturation > 0.8:  # Over-saturated
            saturation_score *= 0.8
        if contrast > 0.8:  # Too much contrast
            contrast_score *= 0.9
        
        score = 0.6 * contrast_score + 0.4 * saturation_score
        
        return score, contrast, avg_saturation
    
    def _score_uniqueness(self, image: Image.Image) -> Tuple[float, bool]:
        """
        Detect if image is likely a stock photo.
        
        Returns:
            Tuple of (uniqueness_score, is_stock_photo)
        """
        # Simple heuristics for stock photo detection
        width, height = image.size
        
        # Stock photos often have very specific aspect ratios
        ratio = width / height
        stock_ratios = [16/9, 4/3, 3/2, 1.0, 2/3, 3/4]
        is_stock_ratio = any(abs(ratio - sr) < 0.02 for sr in stock_ratios)
        
        # Check for excessive uniformity (often in studio shots)
        small = image.resize((50, 50), Image.Resampling.LANCZOS)
        stat = ImageStat.Stat(small)
        uniformity = 1 - (sum(stat.stddev) / (3 * 128))
        
        # Check for typical stock photo color profiles
        # (Very clean, well-lit, often cooler tones)
        avg_brightness = sum(stat.mean) / 3
        is_well_lit = 100 < avg_brightness < 200
        
        # Calculate score
        stock_indicators = 0
        if is_stock_ratio:
            stock_indicators += 1
        if uniformity > 0.7:
            stock_indicators += 1
        if is_well_lit and uniformity > 0.5:
            stock_indicators += 1
        
        is_stock = stock_indicators >= 2
        uniqueness_score = 1.0 - (stock_indicators * 0.2)
        
        return uniqueness_score, is_stock
    
    def _detect_focus_regions(
        self,
        image: Image.Image,
        expected_type: str
    ) -> List[FocusRegion]:
        """Detect focus regions in image."""
        regions = []
        width, height = image.size
        gray = image.convert('L')
        
        # Simple edge-based focus detection
        edges = gray.filter(ImageFilter.FIND_EDGES)
        
        # Divide image into grid and find high-activity regions
        grid_size = 4
        cell_width = width // grid_size
        cell_height = height // grid_size
        
        max_variance = 0
        activities = []
        
        for row in range(grid_size):
            for col in range(grid_size):
                x1 = col * cell_width
                y1 = row * cell_height
                x2 = min((col + 1) * cell_width, width)
                y2 = min((row + 1) * cell_height, height)
                
                cell = edges.crop((x1, y1, x2, y2))
                stat = ImageStat.Stat(cell)
                variance = stat.var[0]
                
                activities.append({
                    "row": row,
                    "col": col,
                    "x": x1 / width,
                    "y": y1 / height,
                    "width": (x2 - x1) / width,
                    "height": (y2 - y1) / height,
                    "variance": variance
                })
                max_variance = max(max_variance, variance)
        
        # Find high-activity regions
        if max_variance > 0:
            for act in activities:
                importance = act["variance"] / max_variance
                if importance > 0.3:
                    regions.append(FocusRegion(
                        x=act["x"],
                        y=act["y"],
                        width=act["width"],
                        height=act["height"],
                        type=expected_type,
                        confidence=0.7,
                        importance=importance
                    ))
        
        # Sort by importance
        regions.sort(key=lambda r: r.importance, reverse=True)
        
        return regions[:5]  # Return top 5 regions
    
    # =========================================================================
    # ENHANCEMENT METHODS
    # =========================================================================
    
    def _apply_sharpening(self, image: Image.Image, blur_amount: float) -> Image.Image:
        """Apply sharpening based on blur amount."""
        # Stronger sharpening for blurrier images
        if blur_amount > 0.6:
            return image.filter(ImageFilter.SHARPEN).filter(ImageFilter.SHARPEN)
        elif blur_amount > 0.3:
            return image.filter(ImageFilter.SHARPEN)
        else:
            return image.filter(ImageFilter.UnsharpMask(radius=1, percent=50))
    
    def _adjust_contrast(self, image: Image.Image) -> Image.Image:
        """Adjust contrast."""
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(1.2)  # 20% boost
    
    def _boost_saturation(self, image: Image.Image) -> Image.Image:
        """Boost color saturation."""
        enhancer = ImageEnhance.Color(image)
        return enhancer.enhance(1.15)  # 15% boost
    
    def _auto_color_correct(self, image: Image.Image) -> Image.Image:
        """Apply automatic color correction."""
        # Use autocontrast for per-channel adjustment
        return ImageOps.autocontrast(image, cutoff=1)
    
    def _reduce_noise(self, image: Image.Image) -> Image.Image:
        """Apply subtle noise reduction."""
        return image.filter(ImageFilter.MedianFilter(size=3))


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_processor_instance: Optional[SmartImageProcessor] = None


def get_smart_image_processor() -> SmartImageProcessor:
    """Get singleton SmartImageProcessor instance."""
    global _processor_instance
    
    if _processor_instance is None:
        _processor_instance = SmartImageProcessor()
    
    return _processor_instance


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def score_image_quality(
    image: Image.Image,
    expected_type: str = "generic"
) -> ImageQualityScore:
    """
    Score image quality.
    
    Args:
        image: PIL Image to score
        expected_type: Expected content type
        
    Returns:
        ImageQualityScore
    """
    return get_smart_image_processor().score_image(image, expected_type)


def score_image_quality_from_bytes(
    image_bytes: bytes,
    expected_type: str = "generic"
) -> ImageQualityScore:
    """
    Score image quality from bytes.
    
    Args:
        image_bytes: Image bytes
        expected_type: Expected content type
        
    Returns:
        ImageQualityScore
    """
    return get_smart_image_processor().score_from_bytes(image_bytes, expected_type)


def smart_crop_image(
    image: Image.Image,
    target_ratio: float = ASPECT_RATIOS["og_image"]
) -> Image.Image:
    """
    Smart crop image to target ratio.
    
    Args:
        image: PIL Image
        target_ratio: Target aspect ratio
        
    Returns:
        Cropped PIL Image
    """
    return get_smart_image_processor().smart_crop(image, target_ratio)


def enhance_image(image: Image.Image) -> EnhancementResult:
    """
    Enhance image quality.
    
    Args:
        image: PIL Image
        
    Returns:
        EnhancementResult
    """
    return get_smart_image_processor().enhance_image(image)


def process_image_for_preview(
    image: Image.Image,
    target_size: Tuple[int, int] = (1200, 630)
) -> Tuple[Image.Image, ImageQualityScore]:
    """
    Complete processing pipeline for preview images.
    
    Args:
        image: Input PIL Image
        target_size: Target dimensions
        
    Returns:
        Tuple of (processed_image, quality_score)
    """
    return get_smart_image_processor().process_for_preview(image, target_size)

