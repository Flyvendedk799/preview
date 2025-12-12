"""
Dynamic Composition Engine - Layer 5 of Design Framework Enhancement.

This module implements intelligent grid systems and content-aware layouts
that adapt to content and context.

Key Features:
- Multiple grid systems (Swiss, Modular, Golden Ratio, Fibonacci)
- Content-aware layout decisions
- Visual weight balancing
- Responsive composition rules
- Negative space distribution
"""

import logging
import math
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class GridType(str, Enum):
    """Available grid systems."""
    SWISS = "swiss"              # 12-column, precise, modernist
    MODULAR = "modular"          # Blocks, flexible, editorial
    ASYMMETRIC = "asymmetric"    # Dynamic, bold, expressive
    GOLDEN_RATIO = "golden"      # 1.618, harmonious
    RULE_OF_THIRDS = "thirds"    # Photography-inspired
    FIBONACCI = "fibonacci"      # Organic, natural


@dataclass
class GridConfig:
    """Configuration for grid system."""
    grid_type: GridType
    columns: int
    gutter: int  # Space between columns
    margin: int  # Outer margins
    baseline: int  # Vertical rhythm


@dataclass
class LayoutZone:
    """A zone in the layout."""
    id: str
    x: int
    y: int
    width: int
    height: int
    purpose: str  # headline, image, proof, body, etc.
    priority: float  # 0-1
    
    def center(self) -> Tuple[int, int]:
        """Get center point."""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def area(self) -> int:
        """Get area in pixels."""
        return self.width * self.height


class CompositionEngine:
    """
    Creates intelligent, content-aware layouts using professional grid systems.
    
    Adapts composition based on:
    - Content amount and type
    - Visual weight distribution
    - Design style preferences
    - Canvas dimensions
    """
    
    def __init__(self, canvas_width: int = 1200, canvas_height: int = 630):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
    
    def calculate_layout(
        self,
        elements: List[Dict[str, Any]],
        grid_type: GridType = GridType.SWISS,
        design_style: str = "balanced"
    ) -> List[LayoutZone]:
        """
        Calculate optimal layout for elements.
        
        Args:
            elements: List of content elements with metadata
            grid_type: Grid system to use
            design_style: Design style (minimal, bold, balanced)
            
        Returns:
            List of LayoutZone objects with positioning
        """
        # Create grid configuration
        grid_config = self._create_grid_config(grid_type, design_style)
        
        # Analyze content
        content_analysis = self._analyze_content(elements)
        
        # Select layout strategy
        if content_analysis["has_hero_image"] and content_analysis["has_headline"]:
            zones = self._create_split_layout(elements, grid_config, content_analysis)
        elif content_analysis["headline_dominant"]:
            zones = self._create_headline_focused_layout(elements, grid_config, content_analysis)
        elif content_analysis["image_focused"]:
            zones = self._create_image_focused_layout(elements, grid_config, content_analysis)
        else:
            zones = self._create_balanced_layout(elements, grid_config, content_analysis)
        
        # Balance visual weight
        zones = self._balance_visual_weight(zones)
        
        # Apply grid alignment
        zones = self._snap_to_grid(zones, grid_config)
        
        logger.info(f"✅ Created {len(zones)} layout zones using {grid_type.value} grid")
        return zones
    
    def _create_grid_config(
        self,
        grid_type: GridType,
        design_style: str
    ) -> GridConfig:
        """Create grid configuration."""
        if grid_type == GridType.SWISS:
            # Classic 12-column grid
            return GridConfig(
                grid_type=grid_type,
                columns=12,
                gutter=20,
                margin=80 if design_style == "minimal" else 60,
                baseline=8
            )
        
        elif grid_type == GridType.GOLDEN_RATIO:
            # Golden ratio divisions
            return GridConfig(
                grid_type=grid_type,
                columns=8,  # Fibonacci-like
                gutter=int(self.canvas_width * 0.0163),  # ~1.63% (related to φ)
                margin=int(self.canvas_width * 0.0618),  # ~6.18% (1/φ)
                baseline=8
            )
        
        elif grid_type == GridType.MODULAR:
            # Block-based grid
            return GridConfig(
                grid_type=grid_type,
                columns=6,
                gutter=30,
                margin=60,
                baseline=16
            )
        
        elif grid_type == GridType.RULE_OF_THIRDS:
            # 3x3 grid (photography)
            return GridConfig(
                grid_type=grid_type,
                columns=3,
                gutter=0,
                margin=0,
                baseline=8
            )
        
        elif grid_type == GridType.ASYMMETRIC:
            # Dynamic, no fixed columns
            return GridConfig(
                grid_type=grid_type,
                columns=0,
                gutter=20,
                margin=40,
                baseline=8
            )
        
        else:  # FIBONACCI
            # Fibonacci spiral-based
            return GridConfig(
                grid_type=grid_type,
                columns=13,  # Fibonacci number
                gutter=8,   # Fibonacci number
                margin=34,  # Fibonacci number
                baseline=8
            )
    
    def _analyze_content(self, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content characteristics."""
        analysis = {
            "element_count": len(elements),
            "has_headline": False,
            "has_hero_image": False,
            "has_logo": False,
            "has_proof": False,
            "headline_dominant": False,
            "image_focused": False,
            "text_heavy": False,
        }
        
        text_count = 0
        image_count = 0
        headline_size = 0
        
        for elem in elements:
            content_type = elem.get("content_type", "").lower()
            
            if "headline" in content_type or "title" in content_type:
                analysis["has_headline"] = True
                headline_size = len(elem.get("content", ""))
            
            if "image" in content_type or "photo" in content_type:
                image_count += 1
                if "hero" in content_type:
                    analysis["has_hero_image"] = True
            
            if "logo" in content_type:
                analysis["has_logo"] = True
            
            if "rating" in content_type or "proof" in content_type:
                analysis["has_proof"] = True
            
            if content_type in ["text", "description", "body"]:
                text_count += 1
        
        # Determine focus
        if headline_size > 50 and text_count < 2:
            analysis["headline_dominant"] = True
        elif image_count > 1:
            analysis["image_focused"] = True
        elif text_count > 3:
            analysis["text_heavy"] = True
        
        return analysis
    
    def _create_headline_focused_layout(
        self,
        elements: List[Dict[str, Any]],
        grid: GridConfig,
        analysis: Dict[str, Any]
    ) -> List[LayoutZone]:
        """Create layout with headline dominating."""
        zones = []
        
        content_width = self.canvas_width - (grid.margin * 2)
        content_height = self.canvas_height - (grid.margin * 2)
        
        # Headline: Large, centered vertically
        headline = next((e for e in elements if "headline" in e.get("content_type", "").lower()), None)
        if headline:
            zones.append(LayoutZone(
                id=headline.get("id", "headline"),
                x=grid.margin,
                y=grid.margin + content_height // 3,
                width=content_width,
                height=content_height // 3,
                purpose="headline",
                priority=1.0
            ))
        
        # Logo: Top left
        logo = next((e for e in elements if "logo" in e.get("content_type", "").lower()), None)
        if logo:
            zones.append(LayoutZone(
                id=logo.get("id", "logo"),
                x=grid.margin,
                y=grid.margin,
                width=100,
                height=100,
                purpose="logo",
                priority=0.7
            ))
        
        # Proof badge: Top right
        proof = next((e for e in elements if "proof" in e.get("content_type", "").lower() or "rating" in e.get("content_type", "").lower()), None)
        if proof:
            zones.append(LayoutZone(
                id=proof.get("id", "proof"),
                x=self.canvas_width - grid.margin - 250,
                y=grid.margin,
                width=250,
                height=50,
                purpose="proof",
                priority=0.8
            ))
        
        # Description: Below headline
        description = next((e for e in elements if "description" in e.get("content_type", "").lower()), None)
        if description:
            zones.append(LayoutZone(
                id=description.get("id", "description"),
                x=grid.margin,
                y=grid.margin + content_height * 2 // 3,
                width=content_width,
                height=content_height // 6,
                purpose="description",
                priority=0.5
            ))
        
        return zones
    
    def _create_split_layout(
        self,
        elements: List[Dict[str, Any]],
        grid: GridConfig,
        analysis: Dict[str, Any]
    ) -> List[LayoutZone]:
        """Create split layout (content left, image right)."""
        zones = []
        
        split_point = int(self.canvas_width * 0.55)  # 55/45 split
        
        # Left side: Content
        content_width = split_point - grid.margin * 2
        
        headline = next((e for e in elements if "headline" in e.get("content_type", "").lower()), None)
        if headline:
            zones.append(LayoutZone(
                id=headline.get("id", "headline"),
                x=grid.margin,
                y=grid.margin + 80,
                width=content_width,
                height=200,
                purpose="headline",
                priority=1.0
            ))
        
        description = next((e for e in elements if "description" in e.get("content_type", "").lower()), None)
        if description:
            zones.append(LayoutZone(
                id=description.get("id", "description"),
                x=grid.margin,
                y=grid.margin + 300,
                width=content_width,
                height=120,
                purpose="description",
                priority=0.6
            ))
        
        # Right side: Image
        image = next((e for e in elements if "image" in e.get("content_type", "").lower()), None)
        if image:
            zones.append(LayoutZone(
                id=image.get("id", "image"),
                x=split_point + grid.margin,
                y=grid.margin + 40,
                width=self.canvas_width - split_point - grid.margin * 2,
                height=self.canvas_height - grid.margin * 2 - 80,
                purpose="image",
                priority=0.9
            ))
        
        return zones
    
    def _create_image_focused_layout(
        self,
        elements: List[Dict[str, Any]],
        grid: GridConfig,
        analysis: Dict[str, Any]
    ) -> List[LayoutZone]:
        """Create layout with image as hero."""
        zones = []
        
        # Hero image: Large, background or prominent
        image = next((e for e in elements if "hero" in e.get("content_type", "").lower() or "image" in e.get("content_type", "").lower()), None)
        if image:
            zones.append(LayoutZone(
                id=image.get("id", "image"),
                x=0,
                y=0,
                width=self.canvas_width,
                height=self.canvas_height,
                purpose="background_image",
                priority=0.5  # Background priority
            ))
        
        # Overlay text card
        card_width = int(self.canvas_width * 0.6)
        card_height = int(self.canvas_height * 0.4)
        
        headline = next((e for e in elements if "headline" in e.get("content_type", "").lower()), None)
        if headline:
            zones.append(LayoutZone(
                id=headline.get("id", "headline"),
                x=(self.canvas_width - card_width) // 2,
                y=(self.canvas_height - card_height) // 2,
                width=card_width,
                height=100,
                purpose="headline_overlay",
                priority=1.0
            ))
        
        return zones
    
    def _create_balanced_layout(
        self,
        elements: List[Dict[str, Any]],
        grid: GridConfig,
        analysis: Dict[str, Any]
    ) -> List[LayoutZone]:
        """Create balanced layout with even distribution."""
        zones = []
        
        # Use Swiss grid for balance
        column_width = (self.canvas_width - grid.margin * 2 - grid.gutter * (grid.columns - 1)) // grid.columns
        
        current_y = grid.margin
        
        # Distribute elements vertically
        for elem in sorted(elements, key=lambda e: e.get("priority_score", 0.5), reverse=True):
            content_type = elem.get("content_type", "").lower()
            
            if "headline" in content_type:
                height = 120
                width = column_width * 10 + grid.gutter * 9
            elif "image" in content_type:
                height = 200
                width = column_width * 6 + grid.gutter * 5
            elif "description" in content_type:
                height = 80
                width = column_width * 8 + grid.gutter * 7
            else:
                height = 60
                width = column_width * 6 + grid.gutter * 5
            
            if current_y + height < self.canvas_height - grid.margin:
                zones.append(LayoutZone(
                    id=elem.get("id", "elem"),
                    x=grid.margin,
                    y=current_y,
                    width=width,
                    height=height,
                    purpose=content_type,
                    priority=elem.get("priority_score", 0.5)
                ))
                current_y += height + grid.gutter * 2
        
        return zones
    
    def _balance_visual_weight(self, zones: List[LayoutZone]) -> List[LayoutZone]:
        """Balance visual weight across layout."""
        if not zones:
            return zones
        
        # Calculate center of mass
        total_weight = 0
        weighted_x = 0
        weighted_y = 0
        
        for zone in zones:
            weight = zone.area() * zone.priority
            center = zone.center()
            weighted_x += center[0] * weight
            weighted_y += center[1] * weight
            total_weight += weight
        
        if total_weight > 0:
            center_of_mass_x = weighted_x / total_weight
            center_of_mass_y = weighted_y / total_weight
            
            # Ideal center
            ideal_x = self.canvas_width // 2
            ideal_y = self.canvas_height // 2
            
            # If significantly off-center, log warning
            if abs(center_of_mass_x - ideal_x) > 200:
                logger.warning(f"Layout is off-center horizontally: {center_of_mass_x} vs {ideal_x}")
            if abs(center_of_mass_y - ideal_y) > 100:
                logger.warning(f"Layout is off-center vertically: {center_of_mass_y} vs {ideal_y}")
        
        return zones
    
    def _snap_to_grid(
        self,
        zones: List[LayoutZone],
        grid: GridConfig
    ) -> List[LayoutZone]:
        """Snap zones to grid for alignment."""
        if grid.grid_type == GridType.ASYMMETRIC:
            return zones  # No snapping for asymmetric
        
        baseline = grid.baseline
        
        for zone in zones:
            # Snap to baseline grid
            zone.y = round(zone.y / baseline) * baseline
            zone.height = round(zone.height / baseline) * baseline
        
        return zones


def calculate_golden_ratio_divisions(
    dimension: int,
    level: int = 1
) -> List[int]:
    """
    Calculate golden ratio divisions of a dimension.
    
    Args:
        dimension: Total dimension (width or height)
        level: Recursion level
        
    Returns:
        List of division points
    """
    phi = 1.618
    divisions = []
    
    # First division at golden ratio
    major = int(dimension / phi)
    minor = dimension - major
    
    divisions.append(major)
    
    if level > 1 and major > 100:
        # Recursively divide major section
        sub_divisions = calculate_golden_ratio_divisions(major, level - 1)
        divisions.extend(sub_divisions)
    
    return sorted(set(divisions))


def calculate_fibonacci_spiral_points(
    width: int,
    height: int,
    iterations: int = 7
) -> List[Tuple[int, int, int]]:
    """
    Calculate points for Fibonacci spiral layout.
    
    Args:
        width: Canvas width
        height: Canvas height
        iterations: Number of spiral iterations
        
    Returns:
        List of (x, y, size) rectangles
    """
    # Fibonacci sequence
    fib = [1, 1]
    for i in range(iterations - 2):
        fib.append(fib[-1] + fib[-2])
    
    # Scale to canvas
    total = sum(fib)
    unit = min(width, height) / total
    
    rectangles = []
    x, y = 0, 0
    direction = 0  # 0: right, 1: down, 2: left, 3: up
    
    for i, f in enumerate(fib):
        size = int(f * unit)
        rectangles.append((x, y, size))
        
        # Move to next position
        if direction == 0:  # Right
            x += size
            direction = 1
        elif direction == 1:  # Down
            y += size
            direction = 2
        elif direction == 2:  # Left
            x -= size
            direction = 3
        elif direction == 3:  # Up
            y -= size
            direction = 0
    
    return rectangles


# Example usage
if __name__ == "__main__":
    engine = CompositionEngine()
    
    test_elements = [
        {"id": "headline", "content_type": "headline", "content": "Big Headline", "priority_score": 1.0},
        {"id": "description", "content_type": "description", "content": "Supporting text", "priority_score": 0.6},
        {"id": "image", "content_type": "hero_image", "content": "", "priority_score": 0.8},
        {"id": "proof", "content_type": "rating", "content": "4.9★", "priority_score": 0.7},
    ]
    
    zones = engine.calculate_layout(test_elements, GridType.SWISS, "balanced")
    
    print(f"Generated {len(zones)} layout zones:")
    for zone in zones:
        print(f"  {zone.purpose}: ({zone.x}, {zone.y}) {zone.width}x{zone.height}")
