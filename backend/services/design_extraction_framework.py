"""
Design Extraction Framework for preserving visual design elements.

This framework extracts and preserves design elements (colors, typography, layout)
from multiple sources to ensure design fidelity in preview generation.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
import re
import logging
from bs4 import BeautifulSoup
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class DesignElements:
    """Extracted design elements."""
    color_palette: Dict[str, str]  # primary, secondary, accent
    typography: Dict[str, Any]  # font_family, font_sizes, weights
    layout_structure: Dict[str, Any]  # grid, spacing, alignment
    visual_hierarchy: Dict[str, Any]  # prominence, contrast
    design_style: str  # minimalist, corporate, playful, etc.


class DesignExtractor:
    """
    Framework for extracting and preserving design elements.
    
    Extracts design from multiple sources:
    1. HTML/CSS (styles, inline styles)
    2. Brand elements (logo colors, brand colors)
    3. Visual analysis (screenshot analysis)
    
    Priority: Brand > HTML > Visual
    """
    
    def extract_design(
        self,
        html_content: str,
        screenshot_bytes: bytes,
        url: str
    ) -> DesignElements:
        """
        Extract design elements from multiple sources with quality validation.
        
        Args:
            html_content: HTML content
            screenshot_bytes: Screenshot bytes
            url: URL for context
            
        Returns:
            DesignElements with extracted design information
        """
        logger.info("Extracting design elements from multiple sources")
        
        # Extract from HTML
        html_design = self._extract_from_html(html_content)
        logger.debug(f"HTML design: colors={bool(html_design.color_palette.get('primary'))}, typography={bool(html_design.typography)}")
        
        # Extract from screenshot (visual analysis)
        visual_design = self._extract_from_visual(screenshot_bytes, html_content)
        
        # Extract from brand (if available)
        brand_design = self._extract_from_brand(html_content, screenshot_bytes, url)
        logger.debug(f"Brand design: colors={bool(brand_design.color_palette.get('primary'))}")
        
        # Fuse design elements with priority
        fused_design = self._fuse_design_elements(
            html_design,
            visual_design,
            brand_design
        )
        
        logger.info(
            f"Design extraction complete: "
            f"primary_color={fused_design.color_palette.get('primary')}, "
            f"style={fused_design.design_style}"
        )
        
        return fused_design
    
    def _extract_from_html(self, html_content: str) -> DesignElements:
        """Extract design elements from HTML/CSS."""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Extract colors
            color_palette = self._extract_colors_from_html(soup)
            
            # Extract typography
            typography = self._extract_typography_from_html(soup)
            
            # Extract layout structure
            layout_structure = self._extract_layout_from_html(soup)
            
            return DesignElements(
                color_palette=color_palette,
                typography=typography,
                layout_structure=layout_structure,
                visual_hierarchy={},
                design_style="corporate"
            )
        except Exception as e:
            logger.warning(f"HTML design extraction failed: {e}")
            return DesignElements(
                color_palette={},
                typography={},
                layout_structure={},
                visual_hierarchy={},
                design_style="unknown"
            )
    
    def _extract_colors_from_html(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract color palette from HTML/CSS."""
        colors = {}
        
        # Look for colors in style tags and inline styles
        style_tags = soup.find_all('style')
        inline_styles = soup.find_all(attrs={'style': True})
        
        # Extract hex colors
        hex_pattern = r'#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b'
        
        all_colors = []
        
        # Extract from style tags
        for style in style_tags:
            if style.string:
                matches = re.findall(hex_pattern, style.string)
                for match in matches:
                    if len(match) == 6:
                        all_colors.append(f"#{match}")
                    else:
                        # Expand 3-digit hex to 6-digit
                        all_colors.append(f"#{match[0]}{match[0]}{match[1]}{match[1]}{match[2]}{match[2]}")
        
        # Extract from inline styles
        for elem in inline_styles:
            style_attr = elem.get('style', '')
            matches = re.findall(hex_pattern, style_attr)
            for match in matches:
                if len(match) == 6:
                    all_colors.append(f"#{match}")
                else:
                    all_colors.append(f"#{match[0]}{match[0]}{match[1]}{match[1]}{match[2]}{match[2]}")
        
        # Filter out common background colors (white, black, gray)
        common_colors = {'#ffffff', '#000000', '#fff', '#000', '#f0f0f0', '#e0e0e0', '#cccccc'}
        filtered_colors = [c for c in all_colors if c.lower() not in common_colors]
        
        # Find most common colors (likely brand colors)
        if filtered_colors:
            color_counts = Counter(filtered_colors)
            common_colors_list = [color for color, count in color_counts.most_common(3)]
            
            if len(common_colors_list) >= 1:
                colors["primary"] = common_colors_list[0]
            if len(common_colors_list) >= 2:
                colors["secondary"] = common_colors_list[1]
            if len(common_colors_list) >= 3:
                colors["accent"] = common_colors_list[2]
        
        # Fallback to defaults if no colors found
        colors.setdefault("primary", "#2563EB")
        colors.setdefault("secondary", "#1E40AF")
        colors.setdefault("accent", "#F59E0B")
        
        return colors
    
    def _extract_typography_from_html(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract typography information from HTML/CSS."""
        typography = {}
        
        # Look for font-family in styles
        style_tags = soup.find_all('style')
        font_pattern = r'font-family:\s*([^;]+)'
        
        fonts = []
        for style in style_tags:
            if style.string:
                matches = re.findall(font_pattern, style.string, re.IGNORECASE)
                fonts.extend(matches)
        
        if fonts:
            font_counts = Counter(fonts)
            most_common_font = font_counts.most_common(1)[0][0]
            # Clean up font name (remove quotes, extra spaces)
            font_name = most_common_font.strip().strip("'\"")
            # Take first font from font stack
            typography["font_family"] = font_name.split(',')[0].strip()
        
        # Extract font sizes
        size_pattern = r'font-size:\s*([^;]+)'
        sizes = []
        for style in style_tags:
            if style.string:
                matches = re.findall(size_pattern, style.string, re.IGNORECASE)
                sizes.extend(matches)
        
        if sizes:
            typography["font_sizes"] = sizes[:5]  # Top 5 sizes
        
        # Extract font weights
        weight_pattern = r'font-weight:\s*([^;]+)'
        weights = []
        for style in style_tags:
            if style.string:
                matches = re.findall(weight_pattern, style.string, re.IGNORECASE)
                weights.extend(matches)
        
        if weights:
            typography["font_weights"] = list(set(weights))[:3]  # Unique weights
        
        return typography
    
    def _extract_layout_from_html(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract layout structure from HTML."""
        layout = {}
        
        # Check for grid layouts
        grid_elements = soup.find_all(class_=re.compile(r'grid|flex|container', re.I))
        if grid_elements:
            layout["has_grid"] = True
            classes_str = ' '.join([str(elem.get('class', [])) for elem in grid_elements[:1]])
            if "grid" in classes_str.lower():
                layout["grid_type"] = "css-grid"
            else:
                layout["grid_type"] = "flexbox"
        
        # Check for spacing
        spacing_elements = soup.find_all(class_=re.compile(r'padding|margin|spacing', re.I))
        layout["has_spacing"] = len(spacing_elements) > 0
        
        # Check for container patterns
        container_elements = soup.find_all(class_=re.compile(r'container|wrapper|content', re.I))
        layout["has_container"] = len(container_elements) > 0
        
        return layout
    
    def _extract_from_visual(
        self,
        screenshot_bytes: bytes,
        html_content: str
    ) -> DesignElements:
        """Extract design elements from screenshot using AI vision."""
        # This would use an improved vision prompt focused on design
        # For now, return minimal design (can be enhanced later)
        return DesignElements(
            color_palette={},
            typography={},
            layout_structure={},
            visual_hierarchy={},
            design_style="unknown"
        )
    
    def _extract_from_brand(
        self,
        html_content: str,
        screenshot_bytes: bytes,
        url: str = ""
    ) -> DesignElements:
        """Extract design from brand elements."""
        try:
            from backend.services.brand_extractor import extract_all_brand_elements
            
            brand_elements = extract_all_brand_elements(html_content, url, screenshot_bytes)
            
            color_palette = {}
            if brand_elements.get("colors"):
                colors = brand_elements["colors"]
                color_palette = {
                    "primary": colors.get("primary_color", "#2563EB"),
                    "secondary": colors.get("secondary_color", "#1E40AF"),
                    "accent": colors.get("accent_color", "#F59E0B")
                }
            
            return DesignElements(
                color_palette=color_palette,
                typography={},
                layout_structure={},
                visual_hierarchy={},
                design_style="brand"
            )
        except Exception as e:
            logger.warning(f"Brand design extraction failed: {e}")
            return DesignElements(
                color_palette={},
                typography={},
                layout_structure={},
                visual_hierarchy={},
                design_style="unknown"
            )
    
    def _fuse_design_elements(
        self,
        html_design: DesignElements,
        visual_design: DesignElements,
        brand_design: DesignElements
    ) -> DesignElements:
        """Fuse design elements with priority: Brand > HTML > Visual."""
        
        # Color palette fusion
        color_palette = {}
        if brand_design.color_palette and brand_design.color_palette.get("primary"):
            color_palette = brand_design.color_palette
            logger.debug("Using brand colors")
        elif html_design.color_palette and html_design.color_palette.get("primary"):
            color_palette = html_design.color_palette
            logger.debug("Using HTML colors")
        elif visual_design.color_palette and visual_design.color_palette.get("primary"):
            color_palette = visual_design.color_palette
            logger.debug("Using visual colors")
        else:
            color_palette = {
                "primary": "#2563EB",
                "secondary": "#1E40AF",
                "accent": "#F59E0B"
            }
            logger.debug("Using default colors")
        
        # Typography fusion
        typography = {}
        if html_design.typography:
            typography = html_design.typography
        elif visual_design.typography:
            typography = visual_design.typography
        
        # Layout fusion
        layout_structure = {}
        if html_design.layout_structure:
            layout_structure = html_design.layout_structure
        elif visual_design.layout_structure:
            layout_structure = visual_design.layout_structure
        
        # Design style fusion
        design_style = (
            brand_design.design_style or
            html_design.design_style or
            visual_design.design_style or
            "corporate"
        )
        
        return DesignElements(
            color_palette=color_palette,
            typography=typography,
            layout_structure=layout_structure,
            visual_hierarchy=visual_design.visual_hierarchy or html_design.visual_hierarchy,
            design_style=design_style
        )
