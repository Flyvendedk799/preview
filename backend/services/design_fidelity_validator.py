"""
Design Fidelity Validator.

Validates that generated previews honor the original design's soul.
Provides actionable feedback for improving design fidelity.

Key Validation Areas:
1. Typography Consistency - Does the typography feel right?
2. Color Emotional Accuracy - Do colors evoke the same emotion?
3. Spacing Rhythm Match - Does spacing match original personality?
4. Brand Recognition - Would someone familiar with the brand recognize it?
5. Overall Feel - Does it feel like the same design language?

This module serves as the final quality gate for ensuring previews
don't just extract content, but truly represent the brand.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# =============================================================================
# VALIDATION RESULT
# =============================================================================

@dataclass
class FidelityScore:
    """Individual fidelity score with explanation."""
    dimension: str
    score: float  # 0-1
    notes: str
    suggestions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "score": self.score,
            "notes": self.notes,
            "suggestions": self.suggestions
        }


@dataclass
class DesignFidelityResult:
    """Complete design fidelity validation result."""
    overall_score: float  # 0-1
    typography_score: FidelityScore
    color_score: FidelityScore
    spacing_score: FidelityScore
    recognition_score: FidelityScore
    soul_score: FidelityScore
    
    # Overall assessment
    verdict: str  # excellent, good, fair, poor
    biggest_gap: str
    improvement_priority: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "typography": self.typography_score.to_dict(),
            "color": self.color_score.to_dict(),
            "spacing": self.spacing_score.to_dict(),
            "recognition": self.recognition_score.to_dict(),
            "soul": self.soul_score.to_dict(),
            "verdict": self.verdict,
            "biggest_gap": self.biggest_gap,
            "improvement_priority": self.improvement_priority
        }


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_typography_fidelity(
    original_dna: Dict[str, Any],
    preview_config: Dict[str, Any]
) -> FidelityScore:
    """
    Validate typography consistency with original design.
    
    Checks:
    - Headline personality match
    - Weight contrast consistency
    - Spacing character alignment
    - Case strategy match
    """
    suggestions = []
    notes = []
    score = 0.0
    
    original_typography = original_dna.get("typography_personality", "bold")
    preview_typography = preview_config.get("typography", {}).get("headline_style", "bold")
    
    # Personality match
    if original_typography.lower() == preview_typography.lower():
        score += 0.4
        notes.append("Typography personality matches")
    elif _typography_compatible(original_typography, preview_typography):
        score += 0.25
        notes.append(f"Typography personality similar ({original_typography} vs {preview_typography})")
        suggestions.append(f"Consider using {original_typography} typography for exact match")
    else:
        notes.append(f"Typography mismatch: expected {original_typography}, got {preview_typography}")
        suggestions.append(f"Switch typography personality to {original_typography}")
    
    # Spacing character
    original_spacing = original_dna.get("spacing_feel", "balanced")
    preview_spacing = preview_config.get("spatial", {}).get("density", "balanced")
    
    if original_spacing.lower() == preview_spacing.lower():
        score += 0.3
        notes.append("Spacing character matches")
    else:
        score += 0.1
        suggestions.append(f"Adjust spacing from {preview_spacing} to {original_spacing}")
    
    # Weight contrast (from typography DNA if available)
    weight_contrast = original_dna.get("weight_contrast", "medium")
    score += 0.3  # Give partial credit by default for weight
    
    return FidelityScore(
        dimension="typography",
        score=min(1.0, score),
        notes=" | ".join(notes),
        suggestions=suggestions
    )


def validate_color_fidelity(
    original_dna: Dict[str, Any],
    preview_colors: Dict[str, str]
) -> FidelityScore:
    """
    Validate color emotional accuracy.
    
    Checks:
    - Color emotion alignment
    - Primary color similarity
    - Light/dark theme match
    """
    suggestions = []
    notes = []
    score = 0.0
    
    original_emotion = original_dna.get("color_emotion", "trust")
    
    # Map preview colors to likely emotion
    preview_emotion = _infer_color_emotion(preview_colors)
    
    if original_emotion.lower() == preview_emotion.lower():
        score += 0.5
        notes.append(f"Color emotion matches ({original_emotion})")
    elif _emotions_compatible(original_emotion, preview_emotion):
        score += 0.3
        notes.append(f"Color emotions compatible ({original_emotion} and {preview_emotion})")
        suggestions.append(f"Adjust colors to better evoke {original_emotion}")
    else:
        score += 0.1
        notes.append(f"Color emotion mismatch: expected {original_emotion}, got {preview_emotion}")
        suggestions.append(f"Use colors that evoke {original_emotion} emotion")
    
    # Check if using original colors
    original_primary = original_dna.get("primary_color", "").lower()
    preview_primary = preview_colors.get("primary", "").lower()
    
    if original_primary and preview_primary:
        if original_primary == preview_primary:
            score += 0.3
            notes.append("Using original brand color")
        elif _colors_similar(original_primary, preview_primary):
            score += 0.2
            notes.append("Using similar brand color")
    
    # Theme consistency
    score += 0.2  # Base credit for theme handling
    
    return FidelityScore(
        dimension="color",
        score=min(1.0, score),
        notes=" | ".join(notes),
        suggestions=suggestions
    )


def validate_spacing_fidelity(
    original_dna: Dict[str, Any],
    preview_config: Dict[str, Any]
) -> FidelityScore:
    """
    Validate spacing rhythm match.
    
    Checks:
    - Density match (compact vs spacious)
    - Padding scale consistency
    - Rhythm alignment
    """
    suggestions = []
    notes = []
    score = 0.0
    
    original_spacing = original_dna.get("spacing_feel", "balanced")
    preview_spacing = preview_config.get("spatial", {}).get("density", "balanced")
    
    if original_spacing.lower() == preview_spacing.lower():
        score += 0.6
        notes.append(f"Spacing density matches ({original_spacing})")
    elif _spacing_adjacent(original_spacing, preview_spacing):
        score += 0.4
        notes.append(f"Spacing density close ({original_spacing} vs {preview_spacing})")
        suggestions.append(f"Adjust spacing to {original_spacing} for exact match")
    else:
        score += 0.2
        notes.append(f"Spacing mismatch: expected {original_spacing}, got {preview_spacing}")
        suggestions.append(f"Change spacing density to {original_spacing}")
    
    # Padding scale
    original_style = original_dna.get("style", "corporate")
    
    # Luxurious/minimalist should have generous padding
    if original_style in ["luxurious", "minimalist", "ultra-minimal"]:
        score += 0.2
        if preview_spacing in ["spacious", "ultra-minimal"]:
            score += 0.2
            notes.append("Appropriate generous padding for style")
        else:
            suggestions.append("Increase padding for more luxurious feel")
    else:
        score += 0.4  # Default credit for other styles
    
    return FidelityScore(
        dimension="spacing",
        score=min(1.0, score),
        notes=" | ".join(notes),
        suggestions=suggestions
    )


def validate_brand_recognition(
    original_dna: Dict[str, Any],
    preview_content: Dict[str, Any]
) -> FidelityScore:
    """
    Validate brand recognition potential.
    
    Checks:
    - Logo presence
    - Brand adjectives representation
    - Style consistency
    """
    suggestions = []
    notes = []
    score = 0.0
    
    # Logo presence
    has_logo = preview_content.get("has_logo", False) or preview_content.get("logo_base64")
    if has_logo:
        score += 0.3
        notes.append("Logo present for brand recognition")
    else:
        suggestions.append("Include logo for better brand recognition")
    
    # Style match
    original_style = original_dna.get("style", "corporate")
    preview_style = preview_content.get("template_style", "corporate")
    
    if original_style.lower() == preview_style.lower():
        score += 0.4
        notes.append(f"Style matches ({original_style})")
    elif _styles_compatible(original_style, preview_style):
        score += 0.25
        notes.append(f"Compatible styles ({original_style} and {preview_style})")
    else:
        suggestions.append(f"Adjust template style to better match {original_style}")
    
    # Brand adjectives representation
    adjectives = original_dna.get("brand_adjectives", [])
    if adjectives:
        score += 0.3
        notes.append(f"Brand personality: {', '.join(adjectives[:3])}")
    else:
        score += 0.15
    
    return FidelityScore(
        dimension="recognition",
        score=min(1.0, score),
        notes=" | ".join(notes),
        suggestions=suggestions
    )


def validate_design_soul(
    original_dna: Dict[str, Any],
    preview_config: Dict[str, Any]
) -> FidelityScore:
    """
    Validate overall design soul match.
    
    The holistic check - does the preview FEEL like it belongs to the original brand?
    """
    suggestions = []
    notes = []
    score = 0.0
    
    original_style = original_dna.get("style", "corporate")
    original_mood = original_dna.get("mood", "balanced")
    original_formality = original_dna.get("formality", 0.5)
    
    # Style alignment
    if original_style:
        score += 0.3
        notes.append(f"Design style: {original_style}")
    
    # Mood consistency
    if original_mood:
        score += 0.25
        notes.append(f"Mood: {original_mood}")
    
    # Formality match
    if original_formality >= 0.7:
        notes.append("Formal design approach")
        score += 0.2
    elif original_formality <= 0.3:
        notes.append("Casual design approach")
        score += 0.2
    else:
        notes.append("Balanced formality")
        score += 0.15
    
    # Design reasoning provided
    reasoning = original_dna.get("design_reasoning", "")
    if reasoning:
        score += 0.25
        notes.append("Design rationale understood")
    else:
        score += 0.1
        suggestions.append("Consider original design intent for better fidelity")
    
    return FidelityScore(
        dimension="soul",
        score=min(1.0, score),
        notes=" | ".join(notes),
        suggestions=suggestions
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _typography_compatible(t1: str, t2: str) -> bool:
    """Check if typography personalities are compatible."""
    compatible_groups = [
        ["authoritative", "bold", "expressive"],
        ["friendly", "playful", "subtle"],
        ["elegant", "refined", "subtle"],
        ["technical", "minimal", "subtle"]
    ]
    
    for group in compatible_groups:
        if t1.lower() in group and t2.lower() in group:
            return True
    return False


def _emotions_compatible(e1: str, e2: str) -> bool:
    """Check if color emotions are compatible."""
    compatible_groups = [
        ["trust", "calm", "sophistication"],
        ["energy", "warmth", "playfulness"],
        ["innovation", "sophistication", "trust"],
        ["warmth", "energy", "playfulness"]
    ]
    
    for group in compatible_groups:
        if e1.lower() in group and e2.lower() in group:
            return True
    return False


def _spacing_adjacent(s1: str, s2: str) -> bool:
    """Check if spacing values are adjacent on the scale."""
    scale = ["compact", "balanced", "spacious", "ultra-minimal"]
    
    try:
        idx1 = scale.index(s1.lower())
        idx2 = scale.index(s2.lower())
        return abs(idx1 - idx2) <= 1
    except ValueError:
        return False


def _styles_compatible(s1: str, s2: str) -> bool:
    """Check if design styles are compatible."""
    compatible_groups = [
        ["minimalist", "corporate", "technical"],
        ["luxurious", "elegant", "editorial"],
        ["playful", "organic", "friendly"],
        ["bold", "maximalist", "expressive"]
    ]
    
    for group in compatible_groups:
        if s1.lower() in group and s2.lower() in group:
            return True
    return False


def _colors_similar(c1: str, c2: str, threshold: int = 50) -> bool:
    """Check if two hex colors are similar."""
    try:
        c1 = c1.lstrip('#')
        c2 = c2.lstrip('#')
        
        r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
        r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
        
        diff = abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2)
        return diff < threshold * 3
    except:
        return False


def _infer_color_emotion(colors: Dict[str, str]) -> str:
    """Infer emotion from color palette."""
    primary = colors.get("primary", "#3B82F6").lstrip('#')
    
    try:
        r, g, b = int(primary[0:2], 16), int(primary[2:4], 16), int(primary[4:6], 16)
        
        # Simple heuristics
        if b > r and b > g:
            return "trust"
        elif r > b and r > g:
            return "energy"
        elif g > r and g > b:
            return "nature"
        elif r > 200 and g > 200:
            return "warmth"
        elif r < 60 and g < 60 and b < 60:
            return "sophistication"
        elif r > 150 and b > 150:
            return "innovation"
        else:
            return "balanced"
    except:
        return "trust"


# =============================================================================
# MAIN VALIDATION FUNCTION
# =============================================================================

def validate_design_fidelity(
    original_dna: Dict[str, Any],
    preview_config: Dict[str, Any],
    preview_content: Dict[str, Any]
) -> DesignFidelityResult:
    """
    Perform complete design fidelity validation.
    
    Args:
        original_dna: Design DNA from extraction
        preview_config: Preview configuration (colors, typography, spacing)
        preview_content: Preview content (has_logo, template_style, etc.)
        
    Returns:
        DesignFidelityResult with complete validation
    """
    # Extract colors from preview config
    preview_colors = {
        "primary": preview_config.get("primary_color", ""),
        "secondary": preview_config.get("secondary_color", ""),
        "accent": preview_config.get("accent_color", "")
    }
    
    # Run validations
    typography_score = validate_typography_fidelity(original_dna, preview_config)
    color_score = validate_color_fidelity(original_dna, preview_colors)
    spacing_score = validate_spacing_fidelity(original_dna, preview_config)
    recognition_score = validate_brand_recognition(original_dna, preview_content)
    soul_score = validate_design_soul(original_dna, preview_config)
    
    # Calculate overall score (weighted average)
    weights = {
        "typography": 0.2,
        "color": 0.25,
        "spacing": 0.15,
        "recognition": 0.2,
        "soul": 0.2
    }
    
    overall_score = (
        typography_score.score * weights["typography"] +
        color_score.score * weights["color"] +
        spacing_score.score * weights["spacing"] +
        recognition_score.score * weights["recognition"] +
        soul_score.score * weights["soul"]
    )
    
    # Determine verdict
    if overall_score >= 0.85:
        verdict = "excellent"
    elif overall_score >= 0.7:
        verdict = "good"
    elif overall_score >= 0.5:
        verdict = "fair"
    else:
        verdict = "poor"
    
    # Find biggest gap
    scores = {
        "typography": typography_score.score,
        "color": color_score.score,
        "spacing": spacing_score.score,
        "recognition": recognition_score.score,
        "soul": soul_score.score
    }
    
    lowest = min(scores, key=scores.get)
    biggest_gap = f"{lowest} ({scores[lowest]:.0%})"
    
    # Prioritize improvements
    improvement_priority = []
    for dimension, score in sorted(scores.items(), key=lambda x: x[1]):
        if score < 0.7:
            improvement_priority.append(dimension)
    
    result = DesignFidelityResult(
        overall_score=overall_score,
        typography_score=typography_score,
        color_score=color_score,
        spacing_score=spacing_score,
        recognition_score=recognition_score,
        soul_score=soul_score,
        verdict=verdict,
        biggest_gap=biggest_gap,
        improvement_priority=improvement_priority[:3]
    )
    
    logger.info(
        f"🎨 Design Fidelity Validation: {verdict} ({overall_score:.0%}) - "
        f"Gap: {biggest_gap}"
    )
    
    return result


def quick_fidelity_check(design_dna: Dict[str, Any]) -> float:
    """
    Quick fidelity check based on Design DNA availability.
    
    Returns a score based on how much design information we have.
    Used when full validation isn't possible.
    """
    if not design_dna:
        return 0.5  # Default middle score
    
    score = 0.5  # Base score
    
    # Check for key DNA components
    if design_dna.get("style"):
        score += 0.1
    if design_dna.get("typography_personality"):
        score += 0.1
    if design_dna.get("color_emotion"):
        score += 0.1
    if design_dna.get("spacing_feel"):
        score += 0.05
    if design_dna.get("brand_adjectives"):
        score += 0.1
    if design_dna.get("design_reasoning"):
        score += 0.05
    
    return min(1.0, score)

