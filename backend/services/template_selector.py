"""
Dynamic Template Selector - Intelligent template selection based on Design DNA.

This module selects the optimal template layout for preview generation based on:
1. Page type (product, profile, article, landing)
2. Design style (minimal, bold, corporate, playful, etc.)
3. Content density (text-heavy, image-focused, balanced)
4. Available content (what elements do we have?)

Each template has multiple layout variants optimized for different scenarios.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

from backend.services.visual_style_classifier import DesignStyle, LayoutDensity
from backend.services.design_dna_applicator import RenderingParams

logger = logging.getLogger(__name__)


class TemplateType(str, Enum):
    """Available template types."""
    LANDING_HERO = "landing_hero"  # Hero image with text overlay
    LANDING_SPLIT = "landing_split"  # 50/50 image and text split
    LANDING_CENTERED = "landing_centered"  # Centered text with subtle bg
    PRODUCT_CARD = "product_card"  # Product image with details
    PRODUCT_FULL = "product_full"  # Full-width product showcase
    PROFILE_AVATAR = "profile_avatar"  # Avatar with bio
    PROFILE_FEATURED = "profile_featured"  # Large profile photo
    ARTICLE_HEADLINE = "article_headline"  # Large headline focused
    ARTICLE_IMAGE = "article_image"  # Image with headline overlay
    MINIMAL_TEXT = "minimal_text"  # Text-only minimal design
    BOLD_STATEMENT = "bold_statement"  # Big bold headline
    SOCIAL_PROOF = "social_proof"  # Ratings and trust-focused


class LayoutVariant(str, Enum):
    """Layout variants within templates."""
    LEFT_ALIGNED = "left_aligned"
    RIGHT_ALIGNED = "right_aligned"
    CENTERED = "centered"
    SPLIT_LEFT = "split_left"  # Image left, text right
    SPLIT_RIGHT = "split_right"  # Text left, image right
    STACKED = "stacked"  # Content stacked vertically
    OVERLAY = "overlay"  # Text overlaid on image


@dataclass
class TemplateConfig:
    """Configuration for a template."""
    template_type: TemplateType
    layout_variant: LayoutVariant
    
    # Layout dimensions (as percentages of 1200x630 canvas)
    image_area: Dict[str, float]  # x, y, width, height (0-1)
    text_area: Dict[str, float]
    
    # Content slots
    has_logo_slot: bool = True
    has_title_slot: bool = True
    has_subtitle_slot: bool = True
    has_description_slot: bool = True
    has_cta_slot: bool = True
    has_social_proof_slot: bool = True
    has_tags_slot: bool = True
    
    # Style preferences
    min_image_prominence: float = 0.0  # 0-1, how important is the image
    text_alignment: str = "left"
    overlay_opacity: float = 0.0  # For overlay layouts
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_type": self.template_type.value,
            "layout_variant": self.layout_variant.value,
            "image_area": self.image_area,
            "text_area": self.text_area,
            "has_logo_slot": self.has_logo_slot,
            "has_title_slot": self.has_title_slot,
            "has_subtitle_slot": self.has_subtitle_slot,
            "has_description_slot": self.has_description_slot,
            "has_cta_slot": self.has_cta_slot,
            "has_social_proof_slot": self.has_social_proof_slot,
            "has_tags_slot": self.has_tags_slot,
            "min_image_prominence": self.min_image_prominence,
            "text_alignment": self.text_alignment,
            "overlay_opacity": self.overlay_opacity
        }


# Template library
TEMPLATE_LIBRARY: Dict[TemplateType, TemplateConfig] = {
    TemplateType.LANDING_HERO: TemplateConfig(
        template_type=TemplateType.LANDING_HERO,
        layout_variant=LayoutVariant.OVERLAY,
        image_area={"x": 0, "y": 0, "width": 1.0, "height": 1.0},
        text_area={"x": 0.05, "y": 0.2, "width": 0.5, "height": 0.6},
        min_image_prominence=0.7,
        text_alignment="left",
        overlay_opacity=0.6
    ),
    TemplateType.LANDING_SPLIT: TemplateConfig(
        template_type=TemplateType.LANDING_SPLIT,
        layout_variant=LayoutVariant.SPLIT_RIGHT,
        image_area={"x": 0.5, "y": 0, "width": 0.5, "height": 1.0},
        text_area={"x": 0.05, "y": 0.1, "width": 0.4, "height": 0.8},
        min_image_prominence=0.5,
        text_alignment="left"
    ),
    TemplateType.LANDING_CENTERED: TemplateConfig(
        template_type=TemplateType.LANDING_CENTERED,
        layout_variant=LayoutVariant.CENTERED,
        image_area={"x": 0.4, "y": 0.65, "width": 0.2, "height": 0.25},
        text_area={"x": 0.1, "y": 0.15, "width": 0.8, "height": 0.45},
        min_image_prominence=0.2,
        text_alignment="center"
    ),
    TemplateType.PRODUCT_CARD: TemplateConfig(
        template_type=TemplateType.PRODUCT_CARD,
        layout_variant=LayoutVariant.SPLIT_LEFT,
        image_area={"x": 0.02, "y": 0.1, "width": 0.4, "height": 0.8},
        text_area={"x": 0.45, "y": 0.1, "width": 0.5, "height": 0.8},
        min_image_prominence=0.6,
        text_alignment="left",
        has_social_proof_slot=True
    ),
    TemplateType.PRODUCT_FULL: TemplateConfig(
        template_type=TemplateType.PRODUCT_FULL,
        layout_variant=LayoutVariant.OVERLAY,
        image_area={"x": 0.5, "y": 0, "width": 0.5, "height": 1.0},
        text_area={"x": 0.05, "y": 0.1, "width": 0.42, "height": 0.8},
        min_image_prominence=0.7,
        text_alignment="left"
    ),
    TemplateType.PROFILE_AVATAR: TemplateConfig(
        template_type=TemplateType.PROFILE_AVATAR,
        layout_variant=LayoutVariant.LEFT_ALIGNED,
        image_area={"x": 0.05, "y": 0.15, "width": 0.25, "height": 0.7},
        text_area={"x": 0.35, "y": 0.15, "width": 0.55, "height": 0.7},
        min_image_prominence=0.5,
        text_alignment="left"
    ),
    TemplateType.PROFILE_FEATURED: TemplateConfig(
        template_type=TemplateType.PROFILE_FEATURED,
        layout_variant=LayoutVariant.OVERLAY,
        image_area={"x": 0.6, "y": 0, "width": 0.4, "height": 1.0},
        text_area={"x": 0.05, "y": 0.15, "width": 0.5, "height": 0.7},
        min_image_prominence=0.6,
        text_alignment="left"
    ),
    TemplateType.ARTICLE_HEADLINE: TemplateConfig(
        template_type=TemplateType.ARTICLE_HEADLINE,
        layout_variant=LayoutVariant.CENTERED,
        image_area={"x": 0, "y": 0, "width": 0, "height": 0},  # No image
        text_area={"x": 0.08, "y": 0.2, "width": 0.84, "height": 0.6},
        min_image_prominence=0.0,
        text_alignment="center"
    ),
    TemplateType.ARTICLE_IMAGE: TemplateConfig(
        template_type=TemplateType.ARTICLE_IMAGE,
        layout_variant=LayoutVariant.OVERLAY,
        image_area={"x": 0, "y": 0, "width": 1.0, "height": 1.0},
        text_area={"x": 0.05, "y": 0.5, "width": 0.9, "height": 0.4},
        min_image_prominence=0.8,
        text_alignment="left",
        overlay_opacity=0.7
    ),
    TemplateType.MINIMAL_TEXT: TemplateConfig(
        template_type=TemplateType.MINIMAL_TEXT,
        layout_variant=LayoutVariant.CENTERED,
        image_area={"x": 0.05, "y": 0.7, "width": 0.15, "height": 0.2},
        text_area={"x": 0.1, "y": 0.15, "width": 0.8, "height": 0.5},
        min_image_prominence=0.1,
        text_alignment="center"
    ),
    TemplateType.BOLD_STATEMENT: TemplateConfig(
        template_type=TemplateType.BOLD_STATEMENT,
        layout_variant=LayoutVariant.CENTERED,
        image_area={"x": 0, "y": 0, "width": 0, "height": 0},  # No image
        text_area={"x": 0.05, "y": 0.25, "width": 0.9, "height": 0.5},
        min_image_prominence=0.0,
        text_alignment="center",
        has_description_slot=False,
        has_cta_slot=False
    ),
    TemplateType.SOCIAL_PROOF: TemplateConfig(
        template_type=TemplateType.SOCIAL_PROOF,
        layout_variant=LayoutVariant.LEFT_ALIGNED,
        image_area={"x": 0.6, "y": 0.15, "width": 0.35, "height": 0.7},
        text_area={"x": 0.05, "y": 0.15, "width": 0.5, "height": 0.7},
        min_image_prominence=0.3,
        text_alignment="left",
        has_social_proof_slot=True
    ),
}


@dataclass
class TemplateSelection:
    """Result of template selection."""
    template: TemplateConfig
    score: float
    reasoning: str
    alternatives: List[TemplateType] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "template": self.template.to_dict(),
            "score": self.score,
            "reasoning": self.reasoning,
            "alternatives": [t.value for t in self.alternatives]
        }


class TemplateSelector:
    """
    Intelligently selects templates based on content and design.
    
    Uses a scoring system that considers:
    1. Page type match
    2. Design style compatibility
    3. Content availability
    4. Image prominence requirements
    """
    
    def __init__(self):
        """Initialize the selector."""
        logger.info("📐 TemplateSelector initialized")
    
    def select(
        self,
        page_type: str,
        rendering_params: RenderingParams,
        has_image: bool = True,
        has_logo: bool = False,
        has_social_proof: bool = False,
        title_length: int = 50,
        description_length: int = 150
    ) -> TemplateSelection:
        """
        Select the optimal template for the content.
        
        Args:
            page_type: Type of page (product, profile, article, landing)
            rendering_params: Rendering parameters from DNA applicator
            has_image: Whether we have a primary image
            has_logo: Whether we have a logo
            has_social_proof: Whether we have social proof
            title_length: Length of title in characters
            description_length: Length of description in characters
            
        Returns:
            TemplateSelection with best template and alternatives
        """
        style = rendering_params.style_classification.primary_style
        density = rendering_params.style_classification.layout_density
        
        logger.info(
            f"📐 Selecting template for: type={page_type}, "
            f"style={style.value}, has_image={has_image}"
        )
        
        # Score all templates
        scores: Dict[TemplateType, Tuple[float, str]] = {}
        
        for template_type, config in TEMPLATE_LIBRARY.items():
            score, reason = self._score_template(
                config,
                page_type,
                style,
                density,
                has_image,
                has_logo,
                has_social_proof,
                title_length,
                description_length
            )
            scores[template_type] = (score, reason)
        
        # Sort by score
        sorted_templates = sorted(
            scores.items(),
            key=lambda x: x[1][0],
            reverse=True
        )
        
        # Get best template
        best_type = sorted_templates[0][0]
        best_score = sorted_templates[0][1][0]
        best_reason = sorted_templates[0][1][1]
        
        # Get alternatives
        alternatives = [t[0] for t in sorted_templates[1:4] if t[1][0] > 0.5]
        
        selection = TemplateSelection(
            template=TEMPLATE_LIBRARY[best_type],
            score=best_score,
            reasoning=best_reason,
            alternatives=alternatives
        )
        
        logger.info(
            f"✅ Selected template: {best_type.value} "
            f"(score={best_score:.2f})"
        )
        
        return selection
    
    def _score_template(
        self,
        config: TemplateConfig,
        page_type: str,
        style: DesignStyle,
        density: LayoutDensity,
        has_image: bool,
        has_logo: bool,
        has_social_proof: bool,
        title_length: int,
        description_length: int
    ) -> Tuple[float, str]:
        """Score a template for the given content."""
        score = 0.0
        reasons = []
        
        # Page type matching (highest weight)
        type_match = self._check_type_match(config.template_type, page_type)
        if type_match > 0:
            score += type_match * 0.35
            reasons.append(f"type_match={type_match:.1f}")
        
        # Image availability
        if has_image and config.min_image_prominence > 0:
            score += 0.2
            reasons.append("has_image")
        elif not has_image and config.min_image_prominence == 0:
            score += 0.2
            reasons.append("no_image_needed")
        elif not has_image and config.min_image_prominence > 0.5:
            score -= 0.3  # Penalty for image-heavy template without image
            reasons.append("missing_required_image")
        
        # Style compatibility
        style_match = self._check_style_match(config, style)
        score += style_match * 0.2
        if style_match > 0:
            reasons.append(f"style={style_match:.1f}")
        
        # Content density
        if density == LayoutDensity.SPARSE and config.min_image_prominence < 0.5:
            score += 0.1
            reasons.append("sparse_friendly")
        elif density == LayoutDensity.DENSE and config.has_description_slot:
            score += 0.1
            reasons.append("content_rich")
        
        # Social proof
        if has_social_proof and config.has_social_proof_slot:
            score += 0.1
            reasons.append("has_social_proof")
        
        # Text length considerations
        if title_length > 60 and config.text_area["width"] > 0.6:
            score += 0.05
            reasons.append("long_title_fits")
        
        # Normalize score
        score = max(0.0, min(1.0, score))
        
        return score, " + ".join(reasons)
    
    def _check_type_match(
        self,
        template_type: TemplateType,
        page_type: str
    ) -> float:
        """Check how well template matches page type."""
        page_type = page_type.lower()
        
        # Perfect matches
        if page_type == "product":
            if template_type in [TemplateType.PRODUCT_CARD, TemplateType.PRODUCT_FULL]:
                return 1.0
            if template_type == TemplateType.SOCIAL_PROOF:
                return 0.8
        
        elif page_type == "profile":
            if template_type in [TemplateType.PROFILE_AVATAR, TemplateType.PROFILE_FEATURED]:
                return 1.0
        
        elif page_type == "article":
            if template_type in [TemplateType.ARTICLE_HEADLINE, TemplateType.ARTICLE_IMAGE]:
                return 1.0
        
        elif page_type == "landing":
            if template_type in [TemplateType.LANDING_HERO, TemplateType.LANDING_SPLIT, TemplateType.LANDING_CENTERED]:
                return 1.0
            if template_type == TemplateType.BOLD_STATEMENT:
                return 0.8
        
        # Generic matches
        if template_type in [TemplateType.LANDING_SPLIT, TemplateType.MINIMAL_TEXT]:
            return 0.5  # Works for many page types
        
        return 0.2  # Base score for any template
    
    def _check_style_match(
        self,
        config: TemplateConfig,
        style: DesignStyle
    ) -> float:
        """Check how well template matches design style."""
        # Minimal style
        if style == DesignStyle.MINIMAL:
            if config.template_type in [TemplateType.MINIMAL_TEXT, TemplateType.LANDING_CENTERED]:
                return 1.0
            if config.overlay_opacity > 0:
                return 0.3  # Overlays can be busy
            return 0.6
        
        # Bold style
        if style == DesignStyle.BOLD:
            if config.template_type in [TemplateType.BOLD_STATEMENT, TemplateType.LANDING_HERO]:
                return 1.0
            if config.min_image_prominence > 0.5:
                return 0.8
            return 0.5
        
        # Editorial style
        if style == DesignStyle.EDITORIAL:
            if config.template_type in [TemplateType.ARTICLE_IMAGE, TemplateType.ARTICLE_HEADLINE]:
                return 1.0
            return 0.5
        
        # Playful style
        if style == DesignStyle.PLAYFUL:
            if config.template_type in [TemplateType.LANDING_SPLIT, TemplateType.PRODUCT_CARD]:
                return 0.9
            return 0.6
        
        # Corporate style
        if style == DesignStyle.CORPORATE:
            if config.template_type in [TemplateType.LANDING_SPLIT, TemplateType.SOCIAL_PROOF]:
                return 0.9
            return 0.6
        
        # Default
        return 0.5


# Singleton instance
_selector_instance: Optional[TemplateSelector] = None


def get_template_selector() -> TemplateSelector:
    """Get or create the template selector singleton."""
    global _selector_instance
    if _selector_instance is None:
        _selector_instance = TemplateSelector()
    return _selector_instance


def select_template(
    page_type: str,
    rendering_params: RenderingParams,
    has_image: bool = True,
    has_logo: bool = False,
    has_social_proof: bool = False,
    title_length: int = 50,
    description_length: int = 150
) -> TemplateSelection:
    """Convenience function to select a template."""
    selector = get_template_selector()
    return selector.select(
        page_type, rendering_params, has_image, has_logo,
        has_social_proof, title_length, description_length
    )

