"""
Visual Hierarchy Engine - Layer 1 of Design Framework Enhancement.

This module implements professional multi-level hierarchy with optical sizing,
dominance scoring, and z-index management.

Key Features:
- Dominance scoring (0-1) for each element
- Optical size adjustments (tracking, line height)
- Z-index layer management
- Dynamic hierarchy based on content importance
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HierarchyLevel(str, Enum):
    """Visual hierarchy levels."""
    HERO = "hero"           # 1.0 - Dominant element
    PRIMARY = "primary"     # 0.7-0.8 - Key supporting
    SECONDARY = "secondary" # 0.4-0.6 - Context, proof
    TERTIARY = "tertiary"   # 0.1-0.3 - Subtle details
    OMIT = "omit"          # 0.0 - Not visible


class ZIndex(int, Enum):
    """Z-index layers for depth management."""
    BACKGROUND = -1    # Textures, patterns
    BASE = 0          # Main content
    ELEVATED = 1      # Cards, floating elements
    OVERLAY = 2       # Badges, accents
    MODAL = 3         # Overlays, tooltips


@dataclass
class HierarchyElement:
    """An element with calculated hierarchy properties."""
    id: str
    content_type: str
    content: str
    
    # Hierarchy
    level: HierarchyLevel
    dominance_score: float  # 0-1
    z_index: int
    
    # Typography (optical adjustments)
    base_font_size: int
    adjusted_font_size: int
    letter_spacing: float  # em units
    line_height: float
    
    # Visual weight
    weight: float  # Combined: size + color + position
    
    # Positioning hints
    suggested_position: Tuple[int, int]  # (x, y)
    suggested_size: Tuple[int, int]      # (width, height)


class VisualHierarchyEngine:
    """
    Calculates and applies professional visual hierarchy.
    
    Ensures one hero element, proper scaling, optical adjustments,
    and depth management.
    """
    
    def __init__(self, canvas_width: int = 1200, canvas_height: int = 630):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
    def calculate_hierarchy(
        self,
        elements: List[Dict[str, Any]],
        design_style: str = "balanced"
    ) -> List[HierarchyElement]:
        """
        Calculate visual hierarchy for all elements.
        
        Args:
            elements: List of content elements with type, content, importance
            design_style: Design style (minimal, bold, balanced, etc.)
            
        Returns:
            List of HierarchyElement objects with calculated properties
        """
        if not elements:
            return []
        
        # Step 1: Calculate raw dominance scores
        scored_elements = self._score_dominance(elements)
        
        # Step 2: Assign hierarchy levels (ensure ONE hero)
        leveled_elements = self._assign_hierarchy_levels(scored_elements, design_style)
        
        # Step 3: Calculate optical adjustments
        hierarchy_elements = []
        for elem in leveled_elements:
            hierarchy_elem = self._calculate_optical_properties(elem, design_style)
            hierarchy_elements.append(hierarchy_elem)
        
        # Step 4: Calculate z-index
        for elem in hierarchy_elements:
            elem.z_index = self._calculate_z_index(elem)
        
        # Step 5: Suggest positioning
        hierarchy_elements = self._suggest_positions(hierarchy_elements, design_style)
        
        logger.info(f"✅ Calculated hierarchy for {len(hierarchy_elements)} elements")
        return hierarchy_elements
    
    def _score_dominance(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score each element's dominance (0-1).
        
        Factors:
        - Content importance (from AI reasoning)
        - Content length (shorter = more impact)
        - Content type (headlines > descriptions)
        - Position priority
        """
        scored = []
        
        for elem in elements:
            content_type = elem.get("content_type", "text").lower()
            content = elem.get("content", "")
            priority = elem.get("priority_score", 0.5)
            purpose = elem.get("purpose", "").lower()
            
            # Base score from AI priority
            score = priority
            
            # Content type multipliers
            type_weights = {
                "headline": 1.0,
                "title": 1.0,
                "hero_image": 0.9,
                "logo": 0.8,
                "subheadline": 0.7,
                "rating": 0.7,
                "statistic": 0.7,
                "image": 0.6,
                "description": 0.5,
                "badge": 0.4,
                "tag": 0.3,
                "caption": 0.2
            }
            score *= type_weights.get(content_type, 0.5)
            
            # Purpose multipliers
            purpose_weights = {
                "hook": 1.0,
                "identity": 0.9,
                "proof": 0.8,
                "benefit": 0.7,
                "action": 0.6,
                "filler": 0.1
            }
            score *= purpose_weights.get(purpose, 0.5)
            
            # Length penalty (shorter = punchier = more dominant)
            if content:
                length = len(content)
                if length < 30:
                    score *= 1.1  # Boost short content
                elif length > 100:
                    score *= 0.9  # Reduce long content
            
            # Clamp to 0-1
            score = max(0.0, min(1.0, score))
            
            elem_copy = elem.copy()
            elem_copy["dominance_score"] = score
            scored.append(elem_copy)
        
        return scored
    
    def _assign_hierarchy_levels(
        self,
        elements: List[Dict[str, Any]],
        design_style: str
    ) -> List[Dict[str, Any]]:
        """
        Assign hierarchy levels ensuring proper distribution.
        
        Rules:
        - ONE hero element (highest score)
        - 1-2 primary elements
        - 2-4 secondary elements
        - Remaining tertiary or omit
        """
        # Sort by dominance score
        sorted_elements = sorted(
            elements,
            key=lambda x: x.get("dominance_score", 0),
            reverse=True
        )
        
        # Assign levels based on design style
        if design_style == "bold":
            # Fewer elements, stronger hierarchy
            thresholds = {"hero": 1, "primary": 2, "secondary": 3}
        elif design_style == "minimal":
            # Very few elements
            thresholds = {"hero": 1, "primary": 1, "secondary": 2}
        else:  # balanced
            # Standard distribution
            thresholds = {"hero": 1, "primary": 2, "secondary": 4}
        
        for i, elem in enumerate(sorted_elements):
            if i < thresholds["hero"]:
                elem["hierarchy_level"] = HierarchyLevel.HERO
            elif i < thresholds["hero"] + thresholds["primary"]:
                elem["hierarchy_level"] = HierarchyLevel.PRIMARY
            elif i < thresholds["hero"] + thresholds["primary"] + thresholds["secondary"]:
                elem["hierarchy_level"] = HierarchyLevel.SECONDARY
            elif elem["dominance_score"] > 0.2:
                elem["hierarchy_level"] = HierarchyLevel.TERTIARY
            else:
                elem["hierarchy_level"] = HierarchyLevel.OMIT
        
        return sorted_elements
    
    def _calculate_optical_properties(
        self,
        elem: Dict[str, Any],
        design_style: str
    ) -> HierarchyElement:
        """
        Calculate optical typography adjustments.
        
        Larger type = tighter tracking
        Smaller type = looser tracking
        Different line heights by level
        """
        level = elem.get("hierarchy_level", HierarchyLevel.SECONDARY)
        content_type = elem.get("content_type", "text")
        
        # Base font sizes by level
        size_map = {
            HierarchyLevel.HERO: 96,      # Huge, dominant
            HierarchyLevel.PRIMARY: 48,   # Large, important
            HierarchyLevel.SECONDARY: 32, # Medium
            HierarchyLevel.TERTIARY: 20,  # Small
            HierarchyLevel.OMIT: 0
        }
        
        # Design style modifiers
        style_multipliers = {
            "bold": 1.2,      # Even larger
            "minimal": 0.9,   # Slightly smaller
            "elegant": 1.0,   # Standard
            "technical": 0.95 # Slightly smaller, denser
        }
        
        base_size = size_map[level]
        multiplier = style_multipliers.get(design_style, 1.0)
        adjusted_size = int(base_size * multiplier)
        
        # Optical letter spacing (em units)
        # Large type: tighter (-0.02em)
        # Small type: looser (+0.02em)
        if adjusted_size > 72:
            letter_spacing = -0.02
        elif adjusted_size > 48:
            letter_spacing = -0.01
        elif adjusted_size < 18:
            letter_spacing = 0.02
        else:
            letter_spacing = 0.0
        
        # Line height by level
        line_height_map = {
            HierarchyLevel.HERO: 1.0,      # Tight, dramatic
            HierarchyLevel.PRIMARY: 1.2,   # Balanced
            HierarchyLevel.SECONDARY: 1.4, # Comfortable
            HierarchyLevel.TERTIARY: 1.5,  # Readable
            HierarchyLevel.OMIT: 1.5
        }
        line_height = line_height_map[level]
        
        # Calculate visual weight (size + importance)
        dominance = elem.get("dominance_score", 0.5)
        weight = (adjusted_size / 100.0) * dominance
        
        # Suggested size (bounding box)
        content_length = len(elem.get("content", ""))
        suggested_width = min(
            self.canvas_width - 160,  # Padding
            int(adjusted_size * content_length * 0.6)
        )
        suggested_height = int(adjusted_size * line_height * 1.2)
        
        return HierarchyElement(
            id=elem.get("id", ""),
            content_type=content_type,
            content=elem.get("content", ""),
            level=level,
            dominance_score=dominance,
            z_index=0,  # Calculated separately
            base_font_size=base_size,
            adjusted_font_size=adjusted_size,
            letter_spacing=letter_spacing,
            line_height=line_height,
            weight=weight,
            suggested_position=(0, 0),  # Calculated separately
            suggested_size=(suggested_width, suggested_height)
        )
    
    def _calculate_z_index(self, elem: HierarchyElement) -> int:
        """
        Calculate z-index for depth layering.
        """
        content_type = elem.content_type.lower()
        
        # Background elements
        if "background" in content_type or "pattern" in content_type:
            return ZIndex.BACKGROUND
        
        # Overlay elements (badges, accents)
        if content_type in ["badge", "accent", "label", "tag"]:
            return ZIndex.OVERLAY
        
        # Elevated elements (cards, images with shadow)
        if content_type in ["card", "image", "logo"] and elem.level in [HierarchyLevel.HERO, HierarchyLevel.PRIMARY]:
            return ZIndex.ELEVATED
        
        # Base content
        return ZIndex.BASE
    
    def _suggest_positions(
        self,
        elements: List[HierarchyElement],
        design_style: str
    ) -> List[HierarchyElement]:
        """
        Suggest positions based on hierarchy and style.
        
        Hero: Center-dominant
        Primary: Supporting positions
        Secondary: Context areas
        """
        # Find hero element
        hero = next((e for e in elements if e.level == HierarchyLevel.HERO), None)
        
        if hero:
            # Hero: Vertically centered, horizontally centered or left-aligned
            if design_style == "minimal":
                hero.suggested_position = (
                    (self.canvas_width - hero.suggested_size[0]) // 2,
                    (self.canvas_height - hero.suggested_size[1]) // 2
                )
            else:
                hero.suggested_position = (
                    80,  # Left-aligned with padding
                    (self.canvas_height - hero.suggested_size[1]) // 2
                )
        
        # Primary elements: Above or below hero
        primary_elements = [e for e in elements if e.level == HierarchyLevel.PRIMARY]
        for i, elem in enumerate(primary_elements):
            if hero:
                y_offset = hero.suggested_position[1] + hero.suggested_size[1] + 40
            else:
                y_offset = 80 + (i * 100)
            
            elem.suggested_position = (80, y_offset)
        
        # Secondary: Bottom or top corners
        secondary_elements = [e for e in elements if e.level == HierarchyLevel.SECONDARY]
        for i, elem in enumerate(secondary_elements):
            if i == 0:
                # Top right (e.g., logo)
                elem.suggested_position = (self.canvas_width - elem.suggested_size[0] - 80, 80)
            else:
                # Bottom
                elem.suggested_position = (80, self.canvas_height - 80 - elem.suggested_size[1])
        
        return elements


def calculate_visual_weight(
    element_size: Tuple[int, int],
    color_luminance: float,
    position_centrality: float
) -> float:
    """
    Calculate visual weight of an element.
    
    Args:
        element_size: (width, height) in pixels
        color_luminance: 0-1, where 0=dark (heavy), 1=light (light)
        position_centrality: 0-1, where 1=center, 0=edge
        
    Returns:
        Visual weight score (0-1)
    """
    # Size component (larger = heavier)
    size_weight = (element_size[0] * element_size[1]) / (1200 * 630)
    size_weight = min(1.0, size_weight)
    
    # Color component (darker = heavier)
    color_weight = 1.0 - color_luminance
    
    # Position component (center = heavier)
    position_weight = position_centrality
    
    # Combined weight
    total_weight = (size_weight * 0.5) + (color_weight * 0.3) + (position_weight * 0.2)
    
    return total_weight


def apply_optical_kerning(text: str, font_size: int) -> List[Tuple[str, float]]:
    """
    Apply optical kerning adjustments for specific letter pairs.
    
    Args:
        text: Text to kern
        font_size: Font size for scaling adjustments
        
    Returns:
        List of (char, x_offset) tuples
    """
    # Common kerning pairs and their adjustments (in em units)
    kerning_pairs = {
        "AV": -0.08, "AW": -0.07, "AT": -0.06, "AY": -0.08,
        "FA": -0.05, "LA": -0.08, "LT": -0.08, "LV": -0.08, "LW": -0.07, "LY": -0.08,
        "PA": -0.05, "TA": -0.06, "TO": -0.04, "VA": -0.08, "WA": -0.07, "YA": -0.08,
        "Yo": -0.04, "We": -0.04, "Wa": -0.05, "Ya": -0.06, "Ye": -0.04,
        "r.": -0.03, "f.": -0.03, "r,": -0.03, "f,": -0.03
    }
    
    result = []
    for i, char in enumerate(text):
        offset = 0.0
        
        # Check if previous char + current char form a kerning pair
        if i > 0:
            pair = text[i-1] + char
            if pair in kerning_pairs:
                # Scale adjustment by font size
                offset = kerning_pairs[pair] * font_size
        
        result.append((char, offset))
    
    return result


def get_responsive_type_scale(base_size: int = 16, ratio: float = 1.25) -> Dict[str, int]:
    """
    Generate a responsive type scale.
    
    Args:
        base_size: Base font size in pixels
        ratio: Scale ratio (1.25=Major Third, 1.618=Golden Ratio, 1.333=Perfect Fourth)
        
    Returns:
        Dictionary of type scale sizes
    """
    scale = {
        "xs": int(base_size / (ratio ** 2)),
        "sm": int(base_size / ratio),
        "base": base_size,
        "md": int(base_size * ratio),
        "lg": int(base_size * (ratio ** 2)),
        "xl": int(base_size * (ratio ** 3)),
        "2xl": int(base_size * (ratio ** 4)),
        "3xl": int(base_size * (ratio ** 5)),
        "4xl": int(base_size * (ratio ** 6))
    }
    
    return scale


# Example usage
if __name__ == "__main__":
    # Test the hierarchy engine
    test_elements = [
        {
            "id": "hero_title",
            "content_type": "headline",
            "content": "Ship 10x Faster",
            "priority_score": 0.95,
            "purpose": "hook"
        },
        {
            "id": "subtitle",
            "content_type": "subheadline",
            "content": "The modern development platform",
            "priority_score": 0.7,
            "purpose": "identity"
        },
        {
            "id": "proof",
            "content_type": "rating",
            "content": "4.9★ from 2,847 reviews",
            "priority_score": 0.8,
            "purpose": "proof"
        },
        {
            "id": "description",
            "content_type": "description",
            "content": "Build, deploy, and scale applications instantly",
            "priority_score": 0.6,
            "purpose": "benefit"
        }
    ]
    
    engine = VisualHierarchyEngine()
    hierarchy = engine.calculate_hierarchy(test_elements, "bold")
    
    for elem in hierarchy:
        print(f"{elem.content[:30]:<30} | Level: {elem.level.value:<10} | Size: {elem.adjusted_font_size}px | Weight: {elem.weight:.2f}")
