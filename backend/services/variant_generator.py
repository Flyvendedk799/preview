"""
Variant Generator - Multi-Variant Preview Generation.

PHASE 5 IMPLEMENTATION:
Generates multiple preview variants for user selection.
Each variant uses different:
- Layout compositions (hero-focused, text-focused, minimal, gradient)
- Color treatments (dark mode, light mode, gradient, flat)
- Text emphasis (headline vs description focus)

This enables A/B testing and lets users pick their preferred design.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from io import BytesIO
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from enum import Enum
import random

logger = logging.getLogger(__name__)


# =============================================================================
# VARIANT TYPES
# =============================================================================

class VariantStyle(Enum):
    """Visual style variants."""
    HERO_FOCUSED = "hero_focused"      # Large hero image, minimal text
    TEXT_FOCUSED = "text_focused"      # Large headline, smaller image
    BALANCED = "balanced"              # Equal emphasis on image and text
    MINIMAL = "minimal"                # Clean, lots of whitespace
    GRADIENT = "gradient"              # Bold gradient background
    DARK_MODE = "dark_mode"            # Dark theme
    LIGHT_MODE = "light_mode"          # Light theme
    BOLD = "bold"                      # High contrast, strong colors
    SUBTLE = "subtle"                  # Muted colors, soft appearance


class LayoutType(Enum):
    """Layout arrangement types."""
    CENTERED = "centered"              # Content centered
    LEFT_ALIGNED = "left_aligned"      # Content left-aligned
    SPLIT = "split"                    # Image on one side, text on other
    OVERLAY = "overlay"                # Text overlaid on image
    STACKED = "stacked"                # Image on top, text below


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class VariantConfig:
    """Configuration for a single variant."""
    style: VariantStyle
    layout: LayoutType
    
    # Color adjustments
    brightness: float = 1.0           # 0.5-1.5
    contrast: float = 1.0             # 0.5-1.5
    saturation: float = 1.0           # 0.5-1.5
    
    # Gradient settings
    use_gradient: bool = False
    gradient_opacity: float = 0.5
    
    # Text adjustments
    headline_size_multiplier: float = 1.0
    description_size_multiplier: float = 1.0
    text_shadow: bool = False
    
    # Layout adjustments
    padding_multiplier: float = 1.0
    image_size_ratio: float = 0.4     # Image takes this % of space
    
    # Effects
    blur_background: bool = False
    vignette: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "style": self.style.value,
            "layout": self.layout.value,
            "brightness": self.brightness,
            "contrast": self.contrast,
            "saturation": self.saturation,
            "use_gradient": self.use_gradient,
            "headline_size_multiplier": self.headline_size_multiplier,
            "text_shadow": self.text_shadow
        }


@dataclass
class PreviewVariant:
    """A single preview variant."""
    id: str
    name: str
    description: str
    config: VariantConfig
    image: Image.Image
    
    # Quality metrics
    readability_score: float = 1.0
    visual_appeal_score: float = 1.0
    uniqueness_score: float = 1.0
    
    # Metadata
    is_default: bool = False
    tags: List[str] = field(default_factory=list)
    
    def to_bytes(self, format: str = "PNG") -> bytes:
        """Convert image to bytes."""
        buffer = BytesIO()
        self.image.save(buffer, format=format)
        return buffer.getvalue()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "config": self.config.to_dict(),
            "size": f"{self.image.width}x{self.image.height}",
            "readability_score": self.readability_score,
            "visual_appeal_score": self.visual_appeal_score,
            "uniqueness_score": self.uniqueness_score,
            "is_default": self.is_default,
            "tags": self.tags
        }


@dataclass
class VariantGenerationResult:
    """Result of variant generation."""
    variants: List[PreviewVariant]
    default_variant: PreviewVariant
    generation_time_ms: int = 0
    
    def get_variant_by_id(self, variant_id: str) -> Optional[PreviewVariant]:
        for variant in self.variants:
            if variant.id == variant_id:
                return variant
        return None
    
    def get_best_variant(self, metric: str = "visual_appeal_score") -> PreviewVariant:
        return max(self.variants, key=lambda v: getattr(v, metric, 0))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "variants": [v.to_dict() for v in self.variants],
            "default_variant_id": self.default_variant.id,
            "generation_time_ms": self.generation_time_ms
        }


# =============================================================================
# PRESET VARIANT CONFIGURATIONS
# =============================================================================

VARIANT_PRESETS: Dict[str, VariantConfig] = {
    "hero": VariantConfig(
        style=VariantStyle.HERO_FOCUSED,
        layout=LayoutType.OVERLAY,
        brightness=0.9,
        contrast=1.1,
        use_gradient=True,
        gradient_opacity=0.7,
        headline_size_multiplier=1.3,
        text_shadow=True,
        image_size_ratio=0.6
    ),
    "text": VariantConfig(
        style=VariantStyle.TEXT_FOCUSED,
        layout=LayoutType.LEFT_ALIGNED,
        brightness=1.0,
        contrast=1.05,
        headline_size_multiplier=1.4,
        description_size_multiplier=1.1,
        image_size_ratio=0.25
    ),
    "minimal": VariantConfig(
        style=VariantStyle.MINIMAL,
        layout=LayoutType.CENTERED,
        brightness=1.05,
        saturation=0.85,
        padding_multiplier=1.3,
        headline_size_multiplier=1.1,
        image_size_ratio=0.2
    ),
    "gradient": VariantConfig(
        style=VariantStyle.GRADIENT,
        layout=LayoutType.CENTERED,
        brightness=0.85,
        contrast=1.15,
        saturation=1.1,
        use_gradient=True,
        gradient_opacity=0.8,
        text_shadow=True,
        headline_size_multiplier=1.2
    ),
    "dark": VariantConfig(
        style=VariantStyle.DARK_MODE,
        layout=LayoutType.CENTERED,
        brightness=0.7,
        contrast=1.2,
        use_gradient=True,
        gradient_opacity=0.5,
        text_shadow=True
    ),
    "light": VariantConfig(
        style=VariantStyle.LIGHT_MODE,
        layout=LayoutType.CENTERED,
        brightness=1.1,
        contrast=1.0,
        saturation=0.9,
        padding_multiplier=1.1
    ),
    "bold": VariantConfig(
        style=VariantStyle.BOLD,
        layout=LayoutType.LEFT_ALIGNED,
        brightness=0.95,
        contrast=1.3,
        saturation=1.2,
        headline_size_multiplier=1.5,
        text_shadow=True
    ),
    "subtle": VariantConfig(
        style=VariantStyle.SUBTLE,
        layout=LayoutType.CENTERED,
        brightness=1.05,
        contrast=0.9,
        saturation=0.75,
        padding_multiplier=1.2,
        vignette=True
    )
}


# =============================================================================
# VARIANT GENERATOR
# =============================================================================

class VariantGenerator:
    """
    Generates multiple preview variants for user selection.
    
    Creates diverse variants with different visual treatments
    to give users options for their preview image.
    """
    
    def __init__(
        self,
        default_variant_count: int = 4,
        include_default: bool = True
    ):
        """
        Initialize generator.
        
        Args:
            default_variant_count: Default number of variants to generate
            include_default: Whether to always include the original as a variant
        """
        self.default_variant_count = default_variant_count
        self.include_default = include_default
        
        logger.info(
            f"VariantGenerator initialized: "
            f"default_count={default_variant_count}"
        )
    
    def generate_variants(
        self,
        base_image: Image.Image,
        content: Optional[Dict[str, Any]] = None,
        design_dna: Optional[Dict[str, Any]] = None,
        variant_count: Optional[int] = None,
        styles: Optional[List[str]] = None
    ) -> VariantGenerationResult:
        """
        Generate multiple preview variants.
        
        Args:
            base_image: Base preview image
            content: Optional content dict with title, description, etc.
            design_dna: Optional Design DNA for style consistency
            variant_count: Number of variants to generate
            styles: Specific styles to generate (from VARIANT_PRESETS)
            
        Returns:
            VariantGenerationResult with all variants
        """
        import time
        start_time = time.time()
        
        count = variant_count or self.default_variant_count
        
        logger.info(f"🎨 Generating {count} preview variants...")
        
        variants = []
        
        # Determine which styles to use
        if styles:
            selected_styles = [s for s in styles if s in VARIANT_PRESETS]
        else:
            # Select diverse styles automatically
            selected_styles = self._select_diverse_styles(count, design_dna)
        
        # 1. Include original as "balanced" if requested
        if self.include_default:
            default_variant = PreviewVariant(
                id="original",
                name="Original",
                description="The original preview design",
                config=VariantConfig(
                    style=VariantStyle.BALANCED,
                    layout=LayoutType.CENTERED
                ),
                image=base_image.copy(),
                is_default=True,
                tags=["original", "balanced"]
            )
            variants.append(default_variant)
        
        # 2. Generate style variants
        for i, style_name in enumerate(selected_styles):
            if style_name not in VARIANT_PRESETS:
                continue
            
            config = VARIANT_PRESETS[style_name]
            
            # Apply variant transformations
            variant_image = self._apply_variant_config(base_image, config)
            
            # Calculate quality metrics
            readability = self._calculate_readability(variant_image)
            visual_appeal = self._calculate_visual_appeal(variant_image, config)
            uniqueness = self._calculate_uniqueness(variant_image, variants)
            
            variant = PreviewVariant(
                id=f"variant_{style_name}_{i}",
                name=self._get_variant_name(style_name),
                description=self._get_variant_description(style_name),
                config=config,
                image=variant_image,
                readability_score=readability,
                visual_appeal_score=visual_appeal,
                uniqueness_score=uniqueness,
                is_default=False,
                tags=self._get_variant_tags(style_name)
            )
            
            variants.append(variant)
        
        # 3. Determine default variant
        default = variants[0] if variants else None
        if len(variants) > 1:
            # Pick the one with best combined score
            for v in variants:
                if v.is_default:
                    default = v
                    break
            else:
                default = max(
                    variants,
                    key=lambda v: (v.readability_score + v.visual_appeal_score) / 2
                )
        
        generation_time = int((time.time() - start_time) * 1000)
        
        result = VariantGenerationResult(
            variants=variants,
            default_variant=default,
            generation_time_ms=generation_time
        )
        
        logger.info(
            f"✅ Generated {len(variants)} variants in {generation_time}ms, "
            f"default='{default.name}'"
        )
        
        return result
    
    def generate_quick_variants(
        self,
        base_image: Image.Image
    ) -> VariantGenerationResult:
        """
        Generate a quick set of 4 diverse variants.
        
        Args:
            base_image: Base preview image
            
        Returns:
            VariantGenerationResult
        """
        return self.generate_variants(
            base_image,
            variant_count=4,
            styles=["hero", "minimal", "gradient", "bold"]
        )
    
    def generate_ab_test_variants(
        self,
        base_image: Image.Image,
        test_type: str = "style"
    ) -> VariantGenerationResult:
        """
        Generate variants optimized for A/B testing.
        
        Args:
            base_image: Base preview image
            test_type: Type of test (style, layout, color)
            
        Returns:
            VariantGenerationResult with 2 contrasting variants
        """
        if test_type == "style":
            styles = ["minimal", "bold"]
        elif test_type == "layout":
            styles = ["hero", "text"]
        elif test_type == "color":
            styles = ["dark", "light"]
        else:
            styles = ["hero", "minimal"]
        
        return self.generate_variants(
            base_image,
            variant_count=2,
            styles=styles
        )
    
    def _select_diverse_styles(
        self,
        count: int,
        design_dna: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Select diverse styles for variant generation."""
        all_styles = list(VARIANT_PRESETS.keys())
        
        # If we have design DNA, prioritize matching styles
        if design_dna:
            philosophy = design_dna.get("design_philosophy", {})
            primary_style = philosophy.get("primary_style", "").lower()
            
            if "minimalist" in primary_style:
                preferred = ["minimal", "light", "subtle"]
            elif "bold" in primary_style or "maximalist" in primary_style:
                preferred = ["bold", "gradient", "hero"]
            elif "dark" in primary_style:
                preferred = ["dark", "gradient", "bold"]
            else:
                preferred = ["hero", "minimal", "gradient", "bold"]
            
            # Combine preferred with others
            remaining = [s for s in all_styles if s not in preferred]
            styles = preferred + remaining
        else:
            # Default diverse selection
            styles = ["hero", "minimal", "gradient", "text", "bold", "dark", "light", "subtle"]
        
        return styles[:count]
    
    def _apply_variant_config(
        self,
        image: Image.Image,
        config: VariantConfig
    ) -> Image.Image:
        """Apply variant configuration to image."""
        result = image.copy()
        
        # 1. Apply brightness
        if config.brightness != 1.0:
            enhancer = ImageEnhance.Brightness(result)
            result = enhancer.enhance(config.brightness)
        
        # 2. Apply contrast
        if config.contrast != 1.0:
            enhancer = ImageEnhance.Contrast(result)
            result = enhancer.enhance(config.contrast)
        
        # 3. Apply saturation
        if config.saturation != 1.0:
            enhancer = ImageEnhance.Color(result)
            result = enhancer.enhance(config.saturation)
        
        # 4. Apply gradient overlay
        if config.use_gradient:
            result = self._apply_gradient_overlay(result, config.gradient_opacity)
        
        # 5. Apply blur background
        if config.blur_background:
            result = self._apply_blur_effect(result)
        
        # 6. Apply vignette
        if config.vignette:
            result = self._apply_vignette(result)
        
        return result
    
    def _apply_gradient_overlay(
        self,
        image: Image.Image,
        opacity: float
    ) -> Image.Image:
        """Apply gradient overlay to image."""
        width, height = image.size
        
        # Create gradient overlay
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Diagonal gradient from top-left to bottom-right
        for y in range(height):
            # Calculate opacity based on position
            t = y / height
            alpha = int(opacity * 255 * t * 0.7)  # Fade in from top
            draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
        
        # Composite
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        result = Image.alpha_composite(image, overlay)
        return result.convert('RGB')
    
    def _apply_blur_effect(self, image: Image.Image) -> Image.Image:
        """Apply blur effect to background areas."""
        # Simple overall subtle blur
        return image.filter(ImageFilter.GaussianBlur(radius=1))
    
    def _apply_vignette(
        self,
        image: Image.Image,
        intensity: float = 0.3
    ) -> Image.Image:
        """Apply vignette effect."""
        width, height = image.size
        
        # Create vignette mask
        mask = Image.new('L', (width, height), 255)
        draw = ImageDraw.Draw(mask)
        
        # Draw radial gradient
        center_x, center_y = width // 2, height // 2
        max_dist = (center_x ** 2 + center_y ** 2) ** 0.5
        
        for y in range(height):
            for x in range(0, width, 5):  # Step for performance
                dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                factor = dist / max_dist
                value = int(255 * (1 - factor * intensity))
                draw.point((x, y), fill=value)
        
        # Apply mask
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Darken edges
        darkened = ImageEnhance.Brightness(image).enhance(0.7)
        
        result = Image.composite(image, darkened, mask)
        return result.convert('RGB')
    
    def _calculate_readability(self, image: Image.Image) -> float:
        """Calculate readability score for variant."""
        from PIL import ImageStat
        
        gray = image.convert('L')
        stat = ImageStat.Stat(gray)
        
        # Good readability = good contrast
        contrast = stat.stddev[0] / 128
        
        return min(1.0, contrast)
    
    def _calculate_visual_appeal(
        self,
        image: Image.Image,
        config: VariantConfig
    ) -> float:
        """Calculate visual appeal score."""
        from PIL import ImageStat
        
        stat = ImageStat.Stat(image)
        
        # Factors for visual appeal
        score = 0.5  # Base score
        
        # Good contrast adds appeal
        contrast = sum(stat.stddev) / (3 * 128)
        score += min(0.2, contrast * 0.3)
        
        # Balanced brightness
        brightness = sum(stat.mean) / (3 * 255)
        if 0.3 < brightness < 0.7:
            score += 0.2
        elif 0.2 < brightness < 0.8:
            score += 0.1
        
        # Gradient variants often look more polished
        if config.use_gradient:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_uniqueness(
        self,
        image: Image.Image,
        existing_variants: List[PreviewVariant]
    ) -> float:
        """Calculate how unique this variant is compared to others."""
        if not existing_variants:
            return 1.0
        
        from PIL import ImageStat
        
        stat = ImageStat.Stat(image)
        new_signature = (stat.mean[0], stat.mean[1], stat.mean[2], stat.stddev[0])
        
        min_diff = float('inf')
        
        for variant in existing_variants:
            v_stat = ImageStat.Stat(variant.image)
            v_sig = (v_stat.mean[0], v_stat.mean[1], v_stat.mean[2], v_stat.stddev[0])
            
            # Calculate Euclidean distance
            diff = sum((a - b) ** 2 for a, b in zip(new_signature, v_sig)) ** 0.5
            min_diff = min(min_diff, diff)
        
        # Normalize difference to score
        uniqueness = min(1.0, min_diff / 100)
        
        return uniqueness
    
    def _get_variant_name(self, style_name: str) -> str:
        """Get display name for a variant style."""
        names = {
            "hero": "Hero Image",
            "text": "Text Focus",
            "minimal": "Minimal",
            "gradient": "Gradient",
            "dark": "Dark Mode",
            "light": "Light Mode",
            "bold": "Bold",
            "subtle": "Subtle"
        }
        return names.get(style_name, style_name.replace("_", " ").title())
    
    def _get_variant_description(self, style_name: str) -> str:
        """Get description for a variant style."""
        descriptions = {
            "hero": "Large hero image with text overlay",
            "text": "Emphasis on headline and description",
            "minimal": "Clean design with lots of whitespace",
            "gradient": "Bold gradient background",
            "dark": "Dark theme for better contrast",
            "light": "Light, airy design",
            "bold": "High contrast, strong visual impact",
            "subtle": "Muted colors, soft appearance"
        }
        return descriptions.get(style_name, f"Preview in {style_name} style")
    
    def _get_variant_tags(self, style_name: str) -> List[str]:
        """Get tags for a variant style."""
        tags = {
            "hero": ["visual", "image-focused", "overlay"],
            "text": ["text-focused", "headline", "content"],
            "minimal": ["clean", "whitespace", "simple"],
            "gradient": ["gradient", "colorful", "modern"],
            "dark": ["dark-mode", "high-contrast", "modern"],
            "light": ["light-mode", "clean", "bright"],
            "bold": ["bold", "high-contrast", "impactful"],
            "subtle": ["muted", "soft", "elegant"]
        }
        return tags.get(style_name, [style_name])


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_generator_instance: Optional[VariantGenerator] = None


def get_variant_generator() -> VariantGenerator:
    """Get singleton VariantGenerator instance."""
    global _generator_instance
    
    if _generator_instance is None:
        _generator_instance = VariantGenerator()
    
    return _generator_instance


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_variants(
    image: Image.Image,
    count: int = 4,
    styles: Optional[List[str]] = None
) -> VariantGenerationResult:
    """
    Generate preview variants.
    
    Args:
        image: Base preview image
        count: Number of variants
        styles: Specific styles to use
        
    Returns:
        VariantGenerationResult
    """
    return get_variant_generator().generate_variants(
        image, variant_count=count, styles=styles
    )


def generate_quick_variants(image: Image.Image) -> VariantGenerationResult:
    """
    Generate 4 diverse variants quickly.
    
    Args:
        image: Base preview image
        
    Returns:
        VariantGenerationResult
    """
    return get_variant_generator().generate_quick_variants(image)


def generate_ab_variants(
    image: Image.Image,
    test_type: str = "style"
) -> VariantGenerationResult:
    """
    Generate 2 variants for A/B testing.
    
    Args:
        image: Base preview image
        test_type: Type of test (style, layout, color)
        
    Returns:
        VariantGenerationResult
    """
    return get_variant_generator().generate_ab_test_variants(image, test_type)


def get_available_styles() -> List[str]:
    """Get list of available variant styles."""
    return list(VARIANT_PRESETS.keys())

