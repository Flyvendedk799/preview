"""
Composition Intelligence - Content-Aware Layout Selection.

PHASE 6 IMPLEMENTATION:
Intelligently selects and adapts preview compositions based on:
- Content characteristics (title length, description, images)
- Design DNA (philosophy, typography, spatial intelligence)
- Page type (product, profile, landing, article)
- Visual balance scoring

Instead of fixed template selection, this system dynamically
adapts composition to maximize visual impact and brand fidelity.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# COMPOSITION TYPES
# =============================================================================

class CompositionType(str, Enum):
    """Available composition styles."""
    MINIMAL_LUXURY = "minimal-luxury"
    BOLD_EXPRESSIVE = "bold-expressive"
    PROFESSIONAL_CLEAN = "professional-clean"
    EDITORIAL_CREATIVE = "editorial-creative"
    BRUTALIST_STARK = "brutalist-stark"
    ORGANIC_NATURAL = "organic-natural"
    PRODUCT_FOCUSED = "product-focused"
    PROFILE_CENTERED = "profile-centered"


class ContentDensity(str, Enum):
    """Content density classification."""
    MINIMAL = "minimal"      # Just title
    LIGHT = "light"          # Title + short subtitle
    MEDIUM = "medium"        # Title + subtitle + short description
    DENSE = "dense"          # Title + subtitle + description + proof


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ContentAnalysis:
    """Analysis of content characteristics."""
    title_length: int = 0
    title_word_count: int = 0
    has_subtitle: bool = False
    subtitle_length: int = 0
    has_description: bool = False
    description_length: int = 0
    has_logo: bool = False
    has_hero_image: bool = False
    has_proof: bool = False
    proof_length: int = 0
    
    # Derived
    content_density: ContentDensity = ContentDensity.MEDIUM
    title_is_short: bool = True  # < 30 chars
    title_is_long: bool = False  # > 60 chars
    has_numbers: bool = False    # Social proof with numbers
    
    def __post_init__(self):
        # Calculate content density
        score = 0
        if self.title_length > 0:
            score += 1
        if self.has_subtitle:
            score += 1
        if self.has_description:
            score += 1
        if self.has_proof:
            score += 1
        
        if score <= 1:
            self.content_density = ContentDensity.MINIMAL
        elif score == 2:
            self.content_density = ContentDensity.LIGHT
        elif score == 3:
            self.content_density = ContentDensity.MEDIUM
        else:
            self.content_density = ContentDensity.DENSE


@dataclass
class CompositionScore:
    """Score for a composition type."""
    composition_type: CompositionType
    score: float  # 0.0 - 1.0
    reasons: List[str] = field(default_factory=list)
    adjustments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompositionDecision:
    """Final composition decision with adjustments."""
    selected_composition: CompositionType
    confidence: float
    reasons: List[str]
    
    # Zone adjustments
    zone_adjustments: Dict[str, Any] = field(default_factory=dict)
    
    # Style adjustments
    font_size_multiplier: float = 1.0
    padding_multiplier: float = 1.0
    spacing_multiplier: float = 1.0
    
    # Feature flags
    show_logo: bool = True
    show_accent_bar: bool = True
    show_proof: bool = True
    use_gradient_background: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_composition": self.selected_composition.value,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "zone_adjustments": self.zone_adjustments,
            "font_size_multiplier": self.font_size_multiplier,
            "padding_multiplier": self.padding_multiplier,
            "spacing_multiplier": self.spacing_multiplier,
            "show_logo": self.show_logo,
            "show_accent_bar": self.show_accent_bar,
            "show_proof": self.show_proof,
            "use_gradient_background": self.use_gradient_background
        }


# =============================================================================
# COMPOSITION INTELLIGENCE ENGINE
# =============================================================================

class CompositionIntelligence:
    """
    Intelligently selects and adapts preview compositions.
    
    This engine analyzes content and design DNA to select the optimal
    composition and make fine-grained adjustments for visual balance.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_content(
        self,
        title: str,
        subtitle: Optional[str] = None,
        description: Optional[str] = None,
        proof_text: Optional[str] = None,
        logo_base64: Optional[str] = None,
        hero_image_base64: Optional[str] = None
    ) -> ContentAnalysis:
        """
        Analyze content characteristics for composition selection.
        
        Args:
            title: Main headline
            subtitle: Optional subtitle
            description: Optional description
            proof_text: Optional social proof
            logo_base64: Optional logo
            hero_image_base64: Optional hero image
            
        Returns:
            ContentAnalysis with all metrics
        """
        import re
        
        title_clean = title.strip() if title else ""
        
        analysis = ContentAnalysis(
            title_length=len(title_clean),
            title_word_count=len(title_clean.split()) if title_clean else 0,
            has_subtitle=bool(subtitle and subtitle.strip()),
            subtitle_length=len(subtitle.strip()) if subtitle else 0,
            has_description=bool(description and description.strip()),
            description_length=len(description.strip()) if description else 0,
            has_logo=bool(logo_base64),
            has_hero_image=bool(hero_image_base64),
            has_proof=bool(proof_text and proof_text.strip()),
            proof_length=len(proof_text.strip()) if proof_text else 0
        )
        
        # Derived analysis
        analysis.title_is_short = analysis.title_length < 30
        analysis.title_is_long = analysis.title_length > 60
        
        # Check for numbers (social proof indicator)
        if proof_text:
            analysis.has_numbers = bool(re.search(r'\d+', proof_text))
        if title:
            analysis.has_numbers = analysis.has_numbers or bool(re.search(r'\d+[kK+%]|\d{3,}', title))
        
        # Recalculate content density
        analysis.__post_init__()
        
        self.logger.debug(
            f"Content analysis: "
            f"title_len={analysis.title_length}, "
            f"density={analysis.content_density.value}, "
            f"has_logo={analysis.has_logo}"
        )
        
        return analysis
    
    def select_composition(
        self,
        content: ContentAnalysis,
        design_dna: Optional[Dict[str, Any]] = None,
        page_type: Optional[str] = None
    ) -> CompositionDecision:
        """
        Select optimal composition based on content and design DNA.
        
        This is the core intelligence method that scores each composition
        and selects the best match.
        
        Args:
            content: Content analysis
            design_dna: Design DNA dict (optional)
            page_type: Page type classification (optional)
            
        Returns:
            CompositionDecision with selected composition and adjustments
        """
        scores: List[CompositionScore] = []
        
        # Get design philosophy style if available
        design_style = "professional"
        if design_dna:
            philosophy = design_dna.get("philosophy", {})
            design_style = philosophy.get("primary_style", "professional").lower()
        
        # Score each composition type
        for comp_type in CompositionType:
            score = self._score_composition(content, comp_type, design_style, page_type)
            scores.append(score)
        
        # Sort by score descending
        scores.sort(key=lambda x: x.score, reverse=True)
        
        # Select best composition
        best = scores[0]
        
        # Calculate confidence based on score gap
        confidence = best.score
        if len(scores) > 1:
            gap = best.score - scores[1].score
            confidence = min(1.0, best.score + gap * 0.5)
        
        # Build decision with adjustments
        decision = CompositionDecision(
            selected_composition=best.composition_type,
            confidence=confidence,
            reasons=best.reasons,
            zone_adjustments=best.adjustments
        )
        
        # Apply content-based adjustments
        decision = self._apply_content_adjustments(decision, content)
        
        # Apply design DNA adjustments
        if design_dna:
            decision = self._apply_dna_adjustments(decision, design_dna)
        
        self.logger.info(
            f"🎯 Composition selected: {decision.selected_composition.value} "
            f"(confidence={decision.confidence:.2f})"
        )
        
        return decision
    
    def _score_composition(
        self,
        content: ContentAnalysis,
        comp_type: CompositionType,
        design_style: str,
        page_type: Optional[str]
    ) -> CompositionScore:
        """Score a single composition type for the given content."""
        score = 0.5  # Base score
        reasons = []
        adjustments = {}
        
        # =================================================================
        # PAGE TYPE MATCHING
        # =================================================================
        if page_type:
            page_lower = page_type.lower()
            
            if "product" in page_lower:
                if comp_type == CompositionType.PRODUCT_FOCUSED:
                    score += 0.3
                    reasons.append("Product page matches product-focused composition")
                elif comp_type == CompositionType.PROFESSIONAL_CLEAN:
                    score += 0.15
                    reasons.append("Product page works with professional composition")
            
            elif "profile" in page_lower or "person" in page_lower:
                if comp_type == CompositionType.PROFILE_CENTERED:
                    score += 0.35
                    reasons.append("Profile page matches profile-centered composition")
                elif comp_type == CompositionType.MINIMAL_LUXURY:
                    score += 0.15
                    reasons.append("Profile page works with minimal luxury")
            
            elif "article" in page_lower or "blog" in page_lower:
                if comp_type == CompositionType.EDITORIAL_CREATIVE:
                    score += 0.3
                    reasons.append("Article page matches editorial composition")
            
            elif "landing" in page_lower or "home" in page_lower:
                if comp_type == CompositionType.BOLD_EXPRESSIVE:
                    score += 0.2
                    reasons.append("Landing page benefits from bold composition")
                elif comp_type == CompositionType.PROFESSIONAL_CLEAN:
                    score += 0.15
        
        # =================================================================
        # DESIGN STYLE MATCHING
        # =================================================================
        style_composition_map = {
            "minimalist": [CompositionType.MINIMAL_LUXURY, CompositionType.BRUTALIST_STARK],
            "luxurious": [CompositionType.MINIMAL_LUXURY],
            "bold": [CompositionType.BOLD_EXPRESSIVE],
            "playful": [CompositionType.BOLD_EXPRESSIVE, CompositionType.ORGANIC_NATURAL],
            "corporate": [CompositionType.PROFESSIONAL_CLEAN],
            "professional": [CompositionType.PROFESSIONAL_CLEAN],
            "editorial": [CompositionType.EDITORIAL_CREATIVE],
            "artistic": [CompositionType.EDITORIAL_CREATIVE, CompositionType.ORGANIC_NATURAL],
            "technical": [CompositionType.PROFESSIONAL_CLEAN, CompositionType.BRUTALIST_STARK],
            "organic": [CompositionType.ORGANIC_NATURAL]
        }
        
        matching_styles = style_composition_map.get(design_style, [])
        if comp_type in matching_styles:
            score += 0.2
            reasons.append(f"Design style '{design_style}' matches composition")
        
        # =================================================================
        # CONTENT MATCHING
        # =================================================================
        
        # Title length matching
        if content.title_is_long:
            if comp_type == CompositionType.BOLD_EXPRESSIVE:
                score += 0.15
                reasons.append("Long title benefits from bold layout")
                adjustments["headline_zone_height_mult"] = 1.2
            elif comp_type == CompositionType.BRUTALIST_STARK:
                score += 0.1
                reasons.append("Long title works with stark layout")
        elif content.title_is_short:
            if comp_type == CompositionType.MINIMAL_LUXURY:
                score += 0.15
                reasons.append("Short title works with minimal luxury")
            elif comp_type == CompositionType.PROFESSIONAL_CLEAN:
                score += 0.1
        
        # Content density matching
        if content.content_density == ContentDensity.MINIMAL:
            if comp_type in [CompositionType.MINIMAL_LUXURY, CompositionType.BRUTALIST_STARK]:
                score += 0.2
                reasons.append("Minimal content matches minimal composition")
        elif content.content_density == ContentDensity.DENSE:
            if comp_type in [CompositionType.PROFESSIONAL_CLEAN, CompositionType.EDITORIAL_CREATIVE]:
                score += 0.15
                reasons.append("Dense content works with structured layout")
        
        # Logo presence
        if content.has_logo:
            if comp_type in [CompositionType.MINIMAL_LUXURY, CompositionType.PROFESSIONAL_CLEAN]:
                score += 0.1
                reasons.append("Logo presence suits composition with logo zone")
        
        # Social proof with numbers
        if content.has_numbers and content.has_proof:
            if comp_type in [CompositionType.BOLD_EXPRESSIVE, CompositionType.PRODUCT_FOCUSED]:
                score += 0.1
                reasons.append("Numeric proof benefits from prominent display")
        
        # Hero image presence
        if content.has_hero_image:
            if comp_type == CompositionType.EDITORIAL_CREATIVE:
                score += 0.15
                reasons.append("Hero image suits editorial layout")
                adjustments["has_image_zone"] = True
        
        return CompositionScore(
            composition_type=comp_type,
            score=min(1.0, score),
            reasons=reasons,
            adjustments=adjustments
        )
    
    def _apply_content_adjustments(
        self,
        decision: CompositionDecision,
        content: ContentAnalysis
    ) -> CompositionDecision:
        """Apply content-based adjustments to composition decision."""
        
        # Adjust font size based on title length
        if content.title_is_long:
            decision.font_size_multiplier = 0.85
        elif content.title_is_short:
            decision.font_size_multiplier = 1.1
        
        # Adjust spacing based on content density
        if content.content_density == ContentDensity.MINIMAL:
            decision.spacing_multiplier = 1.3
            decision.padding_multiplier = 1.2
        elif content.content_density == ContentDensity.DENSE:
            decision.spacing_multiplier = 0.9
            decision.padding_multiplier = 0.95
        
        # Feature flags based on content
        decision.show_logo = content.has_logo
        decision.show_proof = content.has_proof and content.proof_length > 5
        decision.show_accent_bar = content.content_density != ContentDensity.MINIMAL
        
        return decision
    
    def _apply_dna_adjustments(
        self,
        decision: CompositionDecision,
        design_dna: Dict[str, Any]
    ) -> CompositionDecision:
        """Apply design DNA adjustments to composition decision."""
        
        # Get visual effects
        visual_effects = design_dna.get("visual_effects", {})
        gradients = visual_effects.get("gradients", "none")
        
        # Enable gradient background if DNA specifies gradients
        if gradients != "none":
            decision.use_gradient_background = True
        
        # Get spatial intelligence
        spatial = design_dna.get("spatial", {})
        density = spatial.get("density", "balanced")
        padding_scale = spatial.get("padding_scale", "medium")
        
        # Apply spatial adjustments
        density_mult = {
            "compact": 0.85,
            "balanced": 1.0,
            "spacious": 1.15,
            "ultra-minimal": 1.3
        }
        decision.spacing_multiplier *= density_mult.get(density, 1.0)
        
        padding_mult = {
            "compact": 0.8,
            "medium": 1.0,
            "generous": 1.2,
            "luxurious": 1.4
        }
        decision.padding_multiplier *= padding_mult.get(padding_scale, 1.0)
        
        # Get typography settings
        typography = design_dna.get("typography", {})
        weight_contrast = typography.get("weight_contrast", "medium")
        
        # Adjust font size based on weight contrast
        if weight_contrast == "high":
            decision.font_size_multiplier *= 1.1
        elif weight_contrast == "subtle":
            decision.font_size_multiplier *= 0.95
        
        return decision
    
    def score_visual_balance(
        self,
        composition: CompositionDecision,
        content: ContentAnalysis
    ) -> float:
        """
        Score the visual balance of a composition with content.
        
        Returns a score from 0.0 to 1.0 indicating how well-balanced
        the composition will look.
        
        Args:
            composition: Selected composition
            content: Content analysis
            
        Returns:
            Visual balance score (0.0 - 1.0)
        """
        score = 0.7  # Base score
        
        # Check logo/content balance
        if content.has_logo and composition.show_logo:
            score += 0.05
        
        # Check proof text balance
        if content.has_proof and composition.show_proof:
            if content.proof_length < 50:
                score += 0.05
            elif content.proof_length > 100:
                score -= 0.05  # Too long proof can unbalance
        
        # Check content density vs composition match
        if content.content_density == ContentDensity.MINIMAL:
            if composition.selected_composition in [
                CompositionType.MINIMAL_LUXURY, 
                CompositionType.BRUTALIST_STARK
            ]:
                score += 0.1
        elif content.content_density == ContentDensity.DENSE:
            if composition.selected_composition in [
                CompositionType.PROFESSIONAL_CLEAN,
                CompositionType.EDITORIAL_CREATIVE
            ]:
                score += 0.1
        
        # Penalize mismatches
        if content.content_density == ContentDensity.DENSE:
            if composition.selected_composition == CompositionType.MINIMAL_LUXURY:
                score -= 0.1  # Dense content in minimal layout
        
        return max(0.0, min(1.0, score))


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def select_optimal_composition(
    title: str,
    subtitle: Optional[str] = None,
    description: Optional[str] = None,
    proof_text: Optional[str] = None,
    logo_base64: Optional[str] = None,
    design_dna: Optional[Dict[str, Any]] = None,
    page_type: Optional[str] = None
) -> CompositionDecision:
    """
    Convenience function to select optimal composition.
    
    Args:
        title: Main headline
        subtitle: Optional subtitle
        description: Optional description
        proof_text: Optional social proof
        logo_base64: Optional logo
        design_dna: Design DNA dict
        page_type: Page type classification
        
    Returns:
        CompositionDecision
    """
    engine = CompositionIntelligence()
    
    content = engine.analyze_content(
        title=title,
        subtitle=subtitle,
        description=description,
        proof_text=proof_text,
        logo_base64=logo_base64
    )
    
    return engine.select_composition(content, design_dna, page_type)


def get_composition_for_page_type(page_type: str) -> CompositionType:
    """
    Quick lookup of default composition for a page type.
    
    Args:
        page_type: Page type string
        
    Returns:
        Default CompositionType
    """
    page_lower = page_type.lower()
    
    if "product" in page_lower:
        return CompositionType.PRODUCT_FOCUSED
    elif "profile" in page_lower or "person" in page_lower:
        return CompositionType.PROFILE_CENTERED
    elif "article" in page_lower or "blog" in page_lower:
        return CompositionType.EDITORIAL_CREATIVE
    elif "landing" in page_lower or "home" in page_lower:
        return CompositionType.BOLD_EXPRESSIVE
    else:
        return CompositionType.PROFESSIONAL_CLEAN

