"""
Platform Optimizer - Platform-Specific Preview Generation.

PHASE 4 IMPLEMENTATION:
Generates optimized preview variants for different social platforms.
Each platform has unique:
- Aspect ratios and dimensions
- Text sizing requirements
- Style preferences (professional vs punchy)
- Safe zones for cropping

Supports: LinkedIn, Twitter/X, Facebook, Slack, Discord, and more.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# PLATFORM CONFIGURATIONS
# =============================================================================

class Platform(Enum):
    """Supported social media platforms."""
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    SLACK = "slack"
    DISCORD = "discord"
    INSTAGRAM = "instagram"
    PINTEREST = "pinterest"
    WHATSAPP = "whatsapp"
    DEFAULT = "default"


@dataclass
class PlatformConfig:
    """Configuration for a specific platform."""
    name: str
    display_name: str
    
    # Dimensions
    width: int
    height: int
    aspect_ratio: float  # width / height
    
    # Text scaling
    headline_scale: float  # Multiplier for headline size
    body_scale: float  # Multiplier for body text
    
    # Style
    style: str  # professional, punchy, emotional, compact, visual
    prefer_dark: bool  # Whether to prefer dark mode
    
    # Safe zones (as percentages)
    safe_margin_top: float  # Content should avoid this %
    safe_margin_bottom: float
    safe_margin_left: float
    safe_margin_right: float
    
    # Content preferences
    max_headline_chars: int
    max_description_chars: int
    show_url: bool
    show_logo: bool
    
    # Platform-specific features
    supports_animation: bool
    typical_viewing_context: str  # feed, message, notification
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "width": self.width,
            "height": self.height,
            "aspect_ratio": self.aspect_ratio,
            "headline_scale": self.headline_scale,
            "body_scale": self.body_scale,
            "style": self.style,
            "max_headline_chars": self.max_headline_chars,
            "max_description_chars": self.max_description_chars
        }


# Platform configurations
PLATFORM_CONFIGS: Dict[Platform, PlatformConfig] = {
    Platform.LINKEDIN: PlatformConfig(
        name="linkedin",
        display_name="LinkedIn",
        width=1200,
        height=627,
        aspect_ratio=1.91,
        headline_scale=1.0,
        body_scale=1.0,
        style="professional",
        prefer_dark=False,
        safe_margin_top=0.05,
        safe_margin_bottom=0.10,  # LinkedIn shows overlay at bottom
        safe_margin_left=0.05,
        safe_margin_right=0.05,
        max_headline_chars=70,
        max_description_chars=150,
        show_url=True,
        show_logo=True,
        supports_animation=False,
        typical_viewing_context="feed"
    ),
    Platform.TWITTER: PlatformConfig(
        name="twitter",
        display_name="Twitter/X",
        width=1200,
        height=600,
        aspect_ratio=2.0,
        headline_scale=1.1,  # Larger for quick scanning
        body_scale=1.05,
        style="punchy",
        prefer_dark=True,  # X is often used in dark mode
        safe_margin_top=0.05,
        safe_margin_bottom=0.05,
        safe_margin_left=0.05,
        safe_margin_right=0.05,
        max_headline_chars=55,  # Shorter for impact
        max_description_chars=100,
        show_url=False,  # Twitter shows URL separately
        show_logo=True,
        supports_animation=True,
        typical_viewing_context="feed"
    ),
    Platform.FACEBOOK: PlatformConfig(
        name="facebook",
        display_name="Facebook",
        width=1200,
        height=630,
        aspect_ratio=1.91,
        headline_scale=1.0,
        body_scale=1.0,
        style="emotional",
        prefer_dark=False,
        safe_margin_top=0.05,
        safe_margin_bottom=0.12,  # FB shows title overlay
        safe_margin_left=0.05,
        safe_margin_right=0.05,
        max_headline_chars=80,
        max_description_chars=200,
        show_url=True,
        show_logo=True,
        supports_animation=False,
        typical_viewing_context="feed"
    ),
    Platform.SLACK: PlatformConfig(
        name="slack",
        display_name="Slack",
        width=800,
        height=418,
        aspect_ratio=1.91,
        headline_scale=1.2,  # Larger for smaller preview
        body_scale=1.1,
        style="compact",
        prefer_dark=False,
        safe_margin_top=0.05,
        safe_margin_bottom=0.05,
        safe_margin_left=0.05,
        safe_margin_right=0.05,
        max_headline_chars=50,
        max_description_chars=80,
        show_url=False,
        show_logo=True,
        supports_animation=False,
        typical_viewing_context="message"
    ),
    Platform.DISCORD: PlatformConfig(
        name="discord",
        display_name="Discord",
        width=1200,
        height=630,
        aspect_ratio=1.91,
        headline_scale=1.0,
        body_scale=1.0,
        style="punchy",
        prefer_dark=True,  # Discord is primarily dark theme
        safe_margin_top=0.05,
        safe_margin_bottom=0.05,
        safe_margin_left=0.05,
        safe_margin_right=0.05,
        max_headline_chars=60,
        max_description_chars=120,
        show_url=False,
        show_logo=True,
        supports_animation=True,
        typical_viewing_context="message"
    ),
    Platform.INSTAGRAM: PlatformConfig(
        name="instagram",
        display_name="Instagram",
        width=1080,
        height=1080,
        aspect_ratio=1.0,  # Square for feed
        headline_scale=1.2,
        body_scale=1.1,
        style="visual",
        prefer_dark=False,
        safe_margin_top=0.08,
        safe_margin_bottom=0.08,
        safe_margin_left=0.08,
        safe_margin_right=0.08,
        max_headline_chars=40,
        max_description_chars=60,
        show_url=False,
        show_logo=True,
        supports_animation=False,
        typical_viewing_context="feed"
    ),
    Platform.PINTEREST: PlatformConfig(
        name="pinterest",
        display_name="Pinterest",
        width=1000,
        height=1500,
        aspect_ratio=0.667,  # Tall portrait
        headline_scale=1.3,
        body_scale=1.2,
        style="visual",
        prefer_dark=False,
        safe_margin_top=0.05,
        safe_margin_bottom=0.10,
        safe_margin_left=0.05,
        safe_margin_right=0.05,
        max_headline_chars=50,
        max_description_chars=100,
        show_url=False,
        show_logo=True,
        supports_animation=False,
        typical_viewing_context="feed"
    ),
    Platform.WHATSAPP: PlatformConfig(
        name="whatsapp",
        display_name="WhatsApp",
        width=800,
        height=418,
        aspect_ratio=1.91,
        headline_scale=1.15,
        body_scale=1.1,
        style="compact",
        prefer_dark=False,
        safe_margin_top=0.05,
        safe_margin_bottom=0.05,
        safe_margin_left=0.05,
        safe_margin_right=0.05,
        max_headline_chars=50,
        max_description_chars=80,
        show_url=False,
        show_logo=True,
        supports_animation=False,
        typical_viewing_context="message"
    ),
    Platform.DEFAULT: PlatformConfig(
        name="default",
        display_name="Default (OG Image)",
        width=1200,
        height=630,
        aspect_ratio=1.91,
        headline_scale=1.0,
        body_scale=1.0,
        style="balanced",
        prefer_dark=False,
        safe_margin_top=0.05,
        safe_margin_bottom=0.08,
        safe_margin_left=0.05,
        safe_margin_right=0.05,
        max_headline_chars=70,
        max_description_chars=150,
        show_url=True,
        show_logo=True,
        supports_animation=False,
        typical_viewing_context="feed"
    )
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PlatformVariant:
    """A preview variant optimized for a specific platform."""
    platform: Platform
    config: PlatformConfig
    image: Image.Image
    
    # Adjustments made
    text_adjustments: Dict[str, Any] = field(default_factory=dict)
    style_adjustments: Dict[str, Any] = field(default_factory=dict)
    
    # Quality metrics
    readability_score: float = 1.0
    platform_fit_score: float = 1.0
    
    def to_bytes(self, format: str = "PNG") -> bytes:
        """Convert image to bytes."""
        buffer = BytesIO()
        self.image.save(buffer, format=format)
        return buffer.getvalue()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "config": self.config.to_dict(),
            "size": f"{self.image.width}x{self.image.height}",
            "text_adjustments": self.text_adjustments,
            "style_adjustments": self.style_adjustments,
            "readability_score": self.readability_score,
            "platform_fit_score": self.platform_fit_score
        }


@dataclass
class MultiPlatformResult:
    """Result containing variants for multiple platforms."""
    variants: Dict[Platform, PlatformVariant]
    primary_platform: Platform
    
    def get_variant(self, platform: Platform) -> Optional[PlatformVariant]:
        return self.variants.get(platform)
    
    def get_all_variants(self) -> List[PlatformVariant]:
        return list(self.variants.values())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_platform": self.primary_platform.value,
            "variants": {
                p.value: v.to_dict() for p, v in self.variants.items()
            }
        }


# =============================================================================
# PLATFORM OPTIMIZER
# =============================================================================

class PlatformOptimizer:
    """
    Optimizes preview images for different social media platforms.
    
    Takes a base preview and adapts it for specific platforms,
    adjusting dimensions, text sizing, and style.
    """
    
    def __init__(self):
        """Initialize optimizer."""
        self.configs = PLATFORM_CONFIGS
        logger.info(
            f"PlatformOptimizer initialized: "
            f"{len(self.configs)} platforms configured"
        )
    
    def get_platform_config(self, platform: Platform) -> PlatformConfig:
        """Get configuration for a platform."""
        return self.configs.get(platform, self.configs[Platform.DEFAULT])
    
    def get_platform_by_name(self, name: str) -> Platform:
        """Get Platform enum from string name."""
        name_lower = name.lower().strip()
        for platform in Platform:
            if platform.value == name_lower:
                return platform
        return Platform.DEFAULT
    
    def optimize_for_platform(
        self,
        base_image: Image.Image,
        platform: Platform,
        content: Optional[Dict[str, Any]] = None
    ) -> PlatformVariant:
        """
        Optimize an image for a specific platform.
        
        Args:
            base_image: Base preview image
            platform: Target platform
            content: Optional content dict with title, description, etc.
            
        Returns:
            PlatformVariant with optimized image
        """
        config = self.get_platform_config(platform)
        
        logger.info(
            f"🎯 Optimizing for {config.display_name}: "
            f"{config.width}x{config.height}"
        )
        
        # 1. Resize/crop to target dimensions
        optimized = self._resize_for_platform(base_image, config)
        
        # 2. Apply style adjustments
        style_adjustments = {}
        if config.prefer_dark:
            optimized, dark_adj = self._apply_dark_mode_adjustments(optimized)
            style_adjustments.update(dark_adj)
        
        # 3. Apply platform-specific text adjustments
        text_adjustments = {}
        if content:
            text_adjustments = self._calculate_text_adjustments(content, config)
        
        # 4. Apply safe zone adjustments
        optimized = self._apply_safe_zones(optimized, config)
        
        # 5. Calculate fit scores
        readability = self._calculate_readability_score(optimized)
        platform_fit = self._calculate_platform_fit(optimized, config)
        
        return PlatformVariant(
            platform=platform,
            config=config,
            image=optimized,
            text_adjustments=text_adjustments,
            style_adjustments=style_adjustments,
            readability_score=readability,
            platform_fit_score=platform_fit
        )
    
    def optimize_for_multiple_platforms(
        self,
        base_image: Image.Image,
        platforms: List[Platform],
        content: Optional[Dict[str, Any]] = None,
        primary_platform: Platform = Platform.DEFAULT
    ) -> MultiPlatformResult:
        """
        Optimize image for multiple platforms.
        
        Args:
            base_image: Base preview image
            platforms: List of target platforms
            content: Optional content dict
            primary_platform: The primary/main platform
            
        Returns:
            MultiPlatformResult with all variants
        """
        variants = {}
        
        for platform in platforms:
            variant = self.optimize_for_platform(base_image, platform, content)
            variants[platform] = variant
        
        return MultiPlatformResult(
            variants=variants,
            primary_platform=primary_platform
        )
    
    def optimize_for_all_platforms(
        self,
        base_image: Image.Image,
        content: Optional[Dict[str, Any]] = None
    ) -> MultiPlatformResult:
        """
        Optimize image for all supported platforms.
        
        Args:
            base_image: Base preview image
            content: Optional content dict
            
        Returns:
            MultiPlatformResult with all variants
        """
        all_platforms = list(Platform)
        return self.optimize_for_multiple_platforms(
            base_image, all_platforms, content
        )
    
    def get_recommended_platforms(
        self,
        page_type: str,
        target_audience: str = "general"
    ) -> List[Platform]:
        """
        Get recommended platforms based on content type.
        
        Args:
            page_type: Type of page (saas, product, article, etc.)
            target_audience: Target audience type
            
        Returns:
            List of recommended platforms
        """
        recommendations = {
            "saas": [Platform.LINKEDIN, Platform.TWITTER, Platform.SLACK],
            "product": [Platform.FACEBOOK, Platform.INSTAGRAM, Platform.PINTEREST],
            "article": [Platform.TWITTER, Platform.FACEBOOK, Platform.LINKEDIN],
            "profile": [Platform.LINKEDIN, Platform.TWITTER],
            "portfolio": [Platform.INSTAGRAM, Platform.PINTEREST, Platform.LINKEDIN],
            "blog": [Platform.TWITTER, Platform.FACEBOOK],
            "landing": [Platform.LINKEDIN, Platform.FACEBOOK, Platform.TWITTER],
        }
        
        return recommendations.get(
            page_type.lower(),
            [Platform.DEFAULT, Platform.LINKEDIN, Platform.TWITTER]
        )
    
    def _resize_for_platform(
        self,
        image: Image.Image,
        config: PlatformConfig
    ) -> Image.Image:
        """Resize image to platform dimensions."""
        target_width = config.width
        target_height = config.height
        target_ratio = target_width / target_height
        
        current_width, current_height = image.size
        current_ratio = current_width / current_height
        
        # Calculate crop/resize strategy
        if abs(current_ratio - target_ratio) < 0.01:
            # Aspect ratios match, just resize
            return image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Need to crop first
        if current_ratio > target_ratio:
            # Image is wider - crop width
            new_width = int(current_height * target_ratio)
            left = (current_width - new_width) // 2
            cropped = image.crop((left, 0, left + new_width, current_height))
        else:
            # Image is taller - crop height
            new_height = int(current_width / target_ratio)
            # Crop more from bottom (rule of thirds)
            top = int((current_height - new_height) * 0.3)
            cropped = image.crop((0, top, current_width, top + new_height))
        
        # Resize to target
        return cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    def _apply_dark_mode_adjustments(
        self,
        image: Image.Image
    ) -> Tuple[Image.Image, Dict[str, Any]]:
        """Apply adjustments for platforms that prefer dark mode."""
        from PIL import ImageEnhance
        
        adjustments = {"dark_mode": True}
        
        # Slightly reduce brightness
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(0.95)
        
        # Boost contrast slightly for dark mode readability
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.05)
        
        adjustments["brightness"] = 0.95
        adjustments["contrast"] = 1.05
        
        return image, adjustments
    
    def _calculate_text_adjustments(
        self,
        content: Dict[str, Any],
        config: PlatformConfig
    ) -> Dict[str, Any]:
        """Calculate text adjustments for platform."""
        adjustments = {}
        
        title = content.get("title", "")
        description = content.get("description", "")
        
        # Truncate title if needed
        if len(title) > config.max_headline_chars:
            adjustments["title_truncated"] = True
            adjustments["original_title_length"] = len(title)
            adjustments["max_title_length"] = config.max_headline_chars
        
        # Truncate description if needed
        if len(description) > config.max_description_chars:
            adjustments["description_truncated"] = True
            adjustments["original_description_length"] = len(description)
            adjustments["max_description_length"] = config.max_description_chars
        
        # Scale factors
        adjustments["headline_scale"] = config.headline_scale
        adjustments["body_scale"] = config.body_scale
        
        return adjustments
    
    def _apply_safe_zones(
        self,
        image: Image.Image,
        config: PlatformConfig
    ) -> Image.Image:
        """
        Apply safe zone awareness.
        
        This is informational - actual content placement should
        respect these zones during rendering.
        """
        # For now, just return the image as-is
        # Safe zones are used during the rendering phase, not post-processing
        return image
    
    def _calculate_readability_score(self, image: Image.Image) -> float:
        """Calculate readability score for the image."""
        from PIL import ImageStat
        
        # Convert to grayscale
        gray = image.convert('L')
        stat = ImageStat.Stat(gray)
        
        # Good readability = good contrast (high stddev)
        contrast = stat.stddev[0] / 128  # Normalize
        
        return min(1.0, contrast)
    
    def _calculate_platform_fit(
        self,
        image: Image.Image,
        config: PlatformConfig
    ) -> float:
        """Calculate how well the image fits the platform requirements."""
        score = 1.0
        
        width, height = image.size
        
        # Check dimensions match exactly
        if width != config.width or height != config.height:
            score -= 0.2
        
        # Check aspect ratio
        actual_ratio = width / height
        if abs(actual_ratio - config.aspect_ratio) > 0.05:
            score -= 0.2
        
        return max(0.0, score)


# =============================================================================
# CONTENT ADAPTER
# =============================================================================

class ContentAdapter:
    """
    Adapts content (title, description, etc.) for specific platforms.
    """
    
    @staticmethod
    def adapt_title(title: str, platform: Platform) -> str:
        """Adapt title for platform."""
        config = PLATFORM_CONFIGS.get(platform, PLATFORM_CONFIGS[Platform.DEFAULT])
        max_chars = config.max_headline_chars
        
        if len(title) <= max_chars:
            return title
        
        # Try to break at word boundary
        truncated = title[:max_chars]
        last_space = truncated.rfind(' ')
        
        if last_space > max_chars * 0.7:
            truncated = truncated[:last_space]
        
        return truncated.rstrip() + "…"
    
    @staticmethod
    def adapt_description(description: str, platform: Platform) -> str:
        """Adapt description for platform."""
        config = PLATFORM_CONFIGS.get(platform, PLATFORM_CONFIGS[Platform.DEFAULT])
        max_chars = config.max_description_chars
        
        if len(description) <= max_chars:
            return description
        
        # Try to break at sentence boundary
        truncated = description[:max_chars]
        
        # Look for sentence ending
        for ending in ['. ', '! ', '? ']:
            last_sentence = truncated.rfind(ending)
            if last_sentence > max_chars * 0.5:
                return truncated[:last_sentence + 1]
        
        # Fall back to word boundary
        last_space = truncated.rfind(' ')
        if last_space > max_chars * 0.7:
            truncated = truncated[:last_space]
        
        return truncated.rstrip() + "…"
    
    @staticmethod
    def get_style_hints(platform: Platform) -> Dict[str, Any]:
        """Get style hints for a platform."""
        config = PLATFORM_CONFIGS.get(platform, PLATFORM_CONFIGS[Platform.DEFAULT])
        
        hints = {
            "style": config.style,
            "prefer_dark": config.prefer_dark,
            "headline_scale": config.headline_scale,
            "body_scale": config.body_scale,
            "show_logo": config.show_logo,
            "show_url": config.show_url
        }
        
        # Add style-specific hints
        if config.style == "professional":
            hints.update({
                "color_saturation": 0.8,  # Slightly muted
                "font_weight": "medium",
                "border_radius": "small"
            })
        elif config.style == "punchy":
            hints.update({
                "color_saturation": 1.1,  # Slightly boosted
                "font_weight": "bold",
                "border_radius": "none"
            })
        elif config.style == "emotional":
            hints.update({
                "color_saturation": 1.0,
                "font_weight": "medium",
                "border_radius": "medium"
            })
        elif config.style == "compact":
            hints.update({
                "color_saturation": 0.9,
                "font_weight": "semibold",
                "padding_scale": 0.8
            })
        elif config.style == "visual":
            hints.update({
                "color_saturation": 1.1,
                "text_overlay": True,
                "image_focus": True
            })
        
        return hints


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_optimizer_instance: Optional[PlatformOptimizer] = None


def get_platform_optimizer() -> PlatformOptimizer:
    """Get singleton PlatformOptimizer instance."""
    global _optimizer_instance
    
    if _optimizer_instance is None:
        _optimizer_instance = PlatformOptimizer()
    
    return _optimizer_instance


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def optimize_for_platform(
    image: Image.Image,
    platform: str,
    content: Optional[Dict[str, Any]] = None
) -> PlatformVariant:
    """
    Optimize image for a specific platform.
    
    Args:
        image: Base preview image
        platform: Platform name (linkedin, twitter, etc.)
        content: Optional content dict
        
    Returns:
        PlatformVariant
    """
    optimizer = get_platform_optimizer()
    platform_enum = optimizer.get_platform_by_name(platform)
    return optimizer.optimize_for_platform(image, platform_enum, content)


def optimize_for_platforms(
    image: Image.Image,
    platforms: List[str],
    content: Optional[Dict[str, Any]] = None
) -> MultiPlatformResult:
    """
    Optimize image for multiple platforms.
    
    Args:
        image: Base preview image
        platforms: List of platform names
        content: Optional content dict
        
    Returns:
        MultiPlatformResult
    """
    optimizer = get_platform_optimizer()
    platform_enums = [optimizer.get_platform_by_name(p) for p in platforms]
    return optimizer.optimize_for_multiple_platforms(image, platform_enums, content)


def get_platform_config(platform: str) -> PlatformConfig:
    """
    Get configuration for a platform.
    
    Args:
        platform: Platform name
        
    Returns:
        PlatformConfig
    """
    optimizer = get_platform_optimizer()
    platform_enum = optimizer.get_platform_by_name(platform)
    return optimizer.get_platform_config(platform_enum)


def adapt_content_for_platform(
    title: str,
    description: str,
    platform: str
) -> Dict[str, str]:
    """
    Adapt content for a specific platform.
    
    Args:
        title: Original title
        description: Original description
        platform: Platform name
        
    Returns:
        Dict with adapted title and description
    """
    optimizer = get_platform_optimizer()
    platform_enum = optimizer.get_platform_by_name(platform)
    
    return {
        "title": ContentAdapter.adapt_title(title, platform_enum),
        "description": ContentAdapter.adapt_description(description, platform_enum)
    }

