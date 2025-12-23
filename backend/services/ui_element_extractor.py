"""
UI Element Extractor - Extract and Classify Actual UI Components from Websites

This service extracts REAL visual components from screenshots, not just styling.
It detects buttons, CTAs, badges, testimonials, hero images, and other UI elements
that can be re-composed into compelling previews.

PHILOSOPHY:
- Websites are designed by professionals with intentional visual hierarchy
- The best preview honors the original design intent
- Extract what WORKS, then re-compose intelligently
"""

import logging
import base64
import json
from io import BytesIO
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from openai import OpenAI

from backend.core.config import settings

logger = logging.getLogger(__name__)


class ElementType(Enum):
    """Types of extractable UI elements."""
    CTA_BUTTON = "cta_button"
    HERO_TEXT = "hero_text"
    HERO_IMAGE = "hero_image"
    BADGE = "badge"
    TESTIMONIAL = "testimonial"
    LOGO = "logo"
    ICON = "icon"
    PRICE_TAG = "price_tag"
    RATING = "rating"
    FEATURE_CARD = "feature_card"
    SOCIAL_PROOF = "social_proof"
    HEADLINE = "headline"
    SUBHEADLINE = "subheadline"
    VALUE_PROP = "value_prop"
    TRUST_BADGE = "trust_badge"
    NAVIGATION = "navigation"
    PRODUCT_IMAGE = "product_image"
    AVATAR = "avatar"


class ElementImportance(Enum):
    """Importance level for composition priority."""
    CRITICAL = "critical"  # Must include in preview
    HIGH = "high"  # Should include if space allows
    MEDIUM = "medium"  # Nice to have
    LOW = "low"  # Optional/decorative


@dataclass
class BoundingBox:
    """Normalized bounding box (0-1 scale)."""
    x: float
    y: float
    width: float
    height: float
    
    def to_pixels(self, image_width: int, image_height: int) -> Tuple[int, int, int, int]:
        """Convert to pixel coordinates (x1, y1, x2, y2)."""
        x1 = int(self.x * image_width)
        y1 = int(self.y * image_height)
        x2 = int((self.x + self.width) * image_width)
        y2 = int((self.y + self.height) * image_height)
        return (x1, y1, x2, y2)


@dataclass
class ExtractedElement:
    """A single extracted UI element."""
    element_type: ElementType
    importance: ElementImportance
    bbox: BoundingBox
    content_text: str  # Actual text content
    visual_style: Dict[str, Any]  # Extracted styling
    semantic_role: str  # What role does this play
    cropped_image_base64: Optional[str] = None  # Actual cropped element
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "element_type": self.element_type.value,
            "importance": self.importance.value,
            "bbox": asdict(self.bbox),
            "content_text": self.content_text,
            "visual_style": self.visual_style,
            "semantic_role": self.semantic_role,
            "has_cropped_image": self.cropped_image_base64 is not None,
            "confidence": self.confidence
        }


@dataclass
class UIElementMap:
    """Complete map of extracted UI elements from a page."""
    elements: List[ExtractedElement] = field(default_factory=list)
    page_type: str = "unknown"
    visual_hierarchy: List[str] = field(default_factory=list)  # Order of importance
    composition_suggestion: str = ""  # AI suggestion for preview composition
    design_rules: Dict[str, Any] = field(default_factory=dict)  # Detected design rules
    
    def get_by_type(self, element_type: ElementType) -> List[ExtractedElement]:
        """Get all elements of a specific type."""
        return [e for e in self.elements if e.element_type == element_type]
    
    def get_critical_elements(self) -> List[ExtractedElement]:
        """Get elements that must be included."""
        return [e for e in self.elements if e.importance == ElementImportance.CRITICAL]
    
    def get_hero_content(self) -> Optional[ExtractedElement]:
        """Get the primary hero content element."""
        heroes = self.get_by_type(ElementType.HERO_TEXT) + self.get_by_type(ElementType.HEADLINE)
        return heroes[0] if heroes else None
    
    def get_primary_cta(self) -> Optional[ExtractedElement]:
        """Get the most important CTA button."""
        ctas = self.get_by_type(ElementType.CTA_BUTTON)
        return ctas[0] if ctas else None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "elements": [e.to_dict() for e in self.elements],
            "page_type": self.page_type,
            "visual_hierarchy": self.visual_hierarchy,
            "composition_suggestion": self.composition_suggestion,
            "design_rules": self.design_rules,
            "element_counts": {et.value: len(self.get_by_type(et)) for et in ElementType}
        }


UI_EXTRACTION_PROMPT = """You are a UI/UX expert analyzing a webpage screenshot to extract ACTUAL UI components.

Your goal is to identify and locate SPECIFIC visual elements that can be cropped and reused in a preview.

CRITICAL: Provide EXACT bounding boxes for each element. All coordinates are normalized 0-1.

=== ELEMENTS TO DETECT ===

1. **HERO/HEADLINE** (Most prominent text)
   - The main headline/title (usually largest text)
   - The hook or value proposition
   - Usually above the fold, center or left aligned

2. **CTA BUTTONS** (Call-to-action buttons)
   - Primary action buttons ("Get Started", "Sign Up", "Buy Now")
   - Look for distinct button styling (color contrast, shadows, borders)
   - Note the exact button text and style

3. **BADGES/TAGS** (Trust signals and labels)
   - "New", "Featured", "Best Seller", "Free Trial"
   - Star ratings
   - Trust badges ("Secure", "Verified", "Award Winner")
   - Certification logos

4. **TESTIMONIALS/SOCIAL PROOF**
   - Customer quotes with avatars
   - Company logos ("Trusted by...")
   - User counts ("10,000+ users")
   - Rating aggregates

5. **PRODUCT/HERO IMAGES**
   - Main product photo
   - Hero illustration
   - Feature screenshots

6. **VALUE PROPOSITIONS**
   - Key benefits (often with icons)
   - Feature highlights
   - "Why choose us" sections

7. **PRICING**
   - Price tags
   - Discount badges
   - "Starting at $X"

=== OUTPUT JSON ===
{
    "page_type": "<landing|product|profile|article|company|saas|ecommerce>",
    
    "elements": [
        {
            "element_type": "<cta_button|hero_text|hero_image|badge|testimonial|logo|price_tag|rating|feature_card|social_proof|headline|subheadline|value_prop|trust_badge|product_image|avatar>",
            "importance": "<critical|high|medium|low>",
            "bbox": {"x": 0.0-1.0, "y": 0.0-1.0, "width": 0.0-1.0, "height": 0.0-1.0},
            "content_text": "<exact text content if text element>",
            "visual_style": {
                "background_color": "<hex or 'transparent'>",
                "text_color": "<hex>",
                "font_weight": "<normal|medium|bold|black>",
                "border_radius": "<none|small|medium|large|pill>",
                "shadow": "<none|subtle|medium|strong>",
                "has_icon": <true|false>
            },
            "semantic_role": "<what this element communicates>",
            "confidence": 0.0-1.0
        }
    ],
    
    "visual_hierarchy": ["<ordered list of element types by visual prominence>"],
    
    "design_rules": {
        "color_scheme": "<light|dark|vibrant|muted>",
        "button_style": "<solid|outlined|gradient|ghost>",
        "spacing_density": "<compact|balanced|spacious>",
        "typography_style": "<modern|classic|bold|elegant>",
        "overall_mood": "<professional|friendly|luxurious|playful|technical>"
    },
    
    "composition_suggestion": "<2-3 sentence description of how to compose these elements into an effective preview>"
}

=== IMPORTANT RULES ===
1. Be PRECISE with bounding boxes - they will be used to crop actual elements
2. Only include elements you're confident about (confidence > 0.6)
3. Prioritize elements that would make the preview compelling
4. Note the visual styling so elements can be recreated if needed
5. Ignore navigation, footers, cookie banners
6. Focus on content that sells/converts/engages"""


class UIElementExtractor:
    """
    Extract actual UI components from webpage screenshots.
    
    This goes beyond color/style extraction to identify and crop
    actual visual elements that can be recomposed into previews.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.logger = logging.getLogger(__name__)
    
    def extract_ui_elements(
        self,
        screenshot_bytes: bytes,
        url: str,
        html_content: Optional[str] = None
    ) -> UIElementMap:
        """
        Extract UI elements from a screenshot.
        
        Args:
            screenshot_bytes: PNG/JPEG screenshot
            url: URL for context
            html_content: Optional HTML for additional context
            
        Returns:
            UIElementMap with all detected elements
        """
        self.logger.info(f"🎯 Extracting UI elements from: {url}")
        
        try:
            # Prepare image for AI analysis
            img = Image.open(BytesIO(screenshot_bytes))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large (keep aspect ratio)
            max_dimension = 2048
            if max(img.size) > max_dimension:
                ratio = max_dimension / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Call AI for element detection
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": UI_EXTRACTION_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            # Parse response
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text)
            
            # Convert to UIElementMap
            element_map = self._parse_extraction_result(result, img, screenshot_bytes)
            
            self.logger.info(
                f"✅ Extracted {len(element_map.elements)} UI elements: "
                f"{[e.element_type.value for e in element_map.elements[:5]]}"
            )
            
            return element_map
            
        except Exception as e:
            self.logger.error(f"UI element extraction failed: {e}")
            return UIElementMap()
    
    def _parse_extraction_result(
        self,
        result: Dict[str, Any],
        image: Image.Image,
        original_bytes: bytes
    ) -> UIElementMap:
        """Parse AI extraction result into UIElementMap."""
        elements = []
        
        for elem_data in result.get("elements", []):
            try:
                # Parse element type
                elem_type_str = elem_data.get("element_type", "headline")
                try:
                    elem_type = ElementType(elem_type_str)
                except ValueError:
                    elem_type = ElementType.HEADLINE
                
                # Parse importance
                importance_str = elem_data.get("importance", "medium")
                try:
                    importance = ElementImportance(importance_str)
                except ValueError:
                    importance = ElementImportance.MEDIUM
                
                # Parse bounding box
                bbox_data = elem_data.get("bbox", {})
                bbox = BoundingBox(
                    x=float(bbox_data.get("x", 0)),
                    y=float(bbox_data.get("y", 0)),
                    width=float(bbox_data.get("width", 0.1)),
                    height=float(bbox_data.get("height", 0.1))
                )
                
                # Crop the element from screenshot
                cropped_base64 = self._crop_element(image, bbox)
                
                element = ExtractedElement(
                    element_type=elem_type,
                    importance=importance,
                    bbox=bbox,
                    content_text=elem_data.get("content_text", ""),
                    visual_style=elem_data.get("visual_style", {}),
                    semantic_role=elem_data.get("semantic_role", ""),
                    cropped_image_base64=cropped_base64,
                    confidence=float(elem_data.get("confidence", 0.5))
                )
                
                elements.append(element)
                
            except Exception as e:
                self.logger.warning(f"Failed to parse element: {e}")
                continue
        
        return UIElementMap(
            elements=elements,
            page_type=result.get("page_type", "unknown"),
            visual_hierarchy=result.get("visual_hierarchy", []),
            composition_suggestion=result.get("composition_suggestion", ""),
            design_rules=result.get("design_rules", {})
        )
    
    def _crop_element(
        self,
        image: Image.Image,
        bbox: BoundingBox,
        padding: int = 5
    ) -> Optional[str]:
        """Crop an element from the image and return as base64."""
        try:
            width, height = image.size
            x1, y1, x2, y2 = bbox.to_pixels(width, height)
            
            # Add padding
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(width, x2 + padding)
            y2 = min(height, y2 + padding)
            
            # Validate crop area
            if x2 <= x1 or y2 <= y1:
                return None
            if (x2 - x1) < 10 or (y2 - y1) < 10:
                return None
            
            # Crop
            cropped = image.crop((x1, y1, x2, y2))
            
            # Convert to base64
            buffer = BytesIO()
            cropped.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        except Exception as e:
            self.logger.warning(f"Failed to crop element: {e}")
            return None
    
    def compose_preview_from_elements(
        self,
        element_map: UIElementMap,
        width: int = 1200,
        height: int = 630,
        background_color: Tuple[int, int, int] = (15, 23, 42)
    ) -> bytes:
        """
        Compose a preview image using extracted UI elements.
        
        This intelligently arranges the extracted elements into
        a visually appealing preview.
        
        Args:
            element_map: Extracted UI elements
            width: Output width
            height: Output height
            background_color: Background color
            
        Returns:
            PNG image bytes
        """
        self.logger.info("🎨 Composing preview from extracted elements")
        
        # Create base image
        img = Image.new('RGB', (width, height), background_color)
        
        # Apply gradient background
        img = self._apply_gradient_background(img, background_color)
        
        # Get critical elements
        hero = element_map.get_hero_content()
        cta = element_map.get_primary_cta()
        badges = element_map.get_by_type(ElementType.BADGE)[:2]
        testimonials = element_map.get_by_type(ElementType.TESTIMONIAL)[:1]
        logos = element_map.get_by_type(ElementType.LOGO)[:1]
        
        # Layout zones (based on visual hierarchy)
        zones = {
            "logo": (40, 40, 200, 80),  # Top left
            "hero": (60, 150, width - 120, 250),  # Center main
            "cta": (60, 420, 300, 80),  # Bottom left
            "badges": (width - 300, 40, 260, 60),  # Top right
            "testimonial": (60, 520, width - 120, 70)  # Bottom
        }
        
        # Place elements
        if logos:
            self._place_element(img, logos[0], zones["logo"])
        
        if hero:
            self._render_hero_text(img, hero, zones["hero"])
        
        if cta:
            self._place_element(img, cta, zones["cta"])
        
        if badges:
            self._place_badges(img, badges, zones["badges"])
        
        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG', quality=95)
        return buffer.getvalue()
    
    def _apply_gradient_background(
        self,
        img: Image.Image,
        base_color: Tuple[int, int, int]
    ) -> Image.Image:
        """Apply a professional gradient background with dithering to prevent banding."""
        import numpy as np
        width, height = img.size
        
        # Create darker shade for gradient
        darker = tuple(max(0, c - 20) for c in base_color)
        
        # Create smooth gradient using numpy with dithering
        y_coords = np.linspace(0, 1, height)[:, np.newaxis]
        progress = np.broadcast_to(y_coords, (height, width))
        
        # Interpolate colors
        r = (base_color[0] * (1 - progress * 0.3) + darker[0] * (progress * 0.3))
        g = (base_color[1] * (1 - progress * 0.3) + darker[1] * (progress * 0.3))
        b = (base_color[2] * (1 - progress * 0.3) + darker[2] * (progress * 0.3))
        
        # Use ordered dithering (Bayer matrix) for better banding elimination
        # Create 8x8 Bayer matrix for ordered dithering
        bayer_matrix = np.array([
            [0, 32, 8, 40, 2, 34, 10, 42],
            [48, 16, 56, 24, 50, 18, 58, 26],
            [12, 44, 4, 36, 14, 46, 6, 38],
            [60, 28, 52, 20, 62, 30, 54, 22],
            [3, 35, 11, 43, 1, 33, 9, 41],
            [51, 19, 59, 27, 49, 17, 57, 25],
            [15, 47, 7, 39, 13, 45, 5, 37],
            [63, 31, 55, 23, 61, 29, 53, 21]
        ], dtype=np.float32) / 64.0 - 0.5  # Normalize to -0.5 to 0.5
        
        # Tile Bayer matrix across image
        bayer_tiled = np.tile(bayer_matrix, (height // 8 + 1, width // 8 + 1))[:height, :width]
        
        # Apply ordered dithering with stronger intensity for dark gradients
        dither_strength = 6.0  # Stronger dithering for dark gradients
        r = np.clip(r + bayer_tiled * dither_strength, 0, 255).astype(np.uint8)
        g = np.clip(g + bayer_tiled * dither_strength, 0, 255).astype(np.uint8)
        b = np.clip(b + bayer_tiled * dither_strength, 0, 255).astype(np.uint8)
        
        # Create image from array
        gradient_array = np.stack([r, g, b], axis=2)
        gradient_img = Image.fromarray(gradient_array, mode='RGB')
        img.paste(gradient_img)
        
        return img
    
    def _place_element(
        self,
        canvas: Image.Image,
        element: ExtractedElement,
        zone: Tuple[int, int, int, int]
    ) -> None:
        """Place an extracted element into a zone."""
        if not element.cropped_image_base64:
            return
        
        try:
            # Decode element image
            elem_bytes = base64.b64decode(element.cropped_image_base64)
            elem_img = Image.open(BytesIO(elem_bytes))
            
            # Resize to fit zone while maintaining aspect ratio
            x, y, max_w, max_h = zone
            elem_ratio = elem_img.width / elem_img.height
            zone_ratio = max_w / max_h
            
            if elem_ratio > zone_ratio:
                # Width constrained
                new_w = min(max_w, elem_img.width)
                new_h = int(new_w / elem_ratio)
            else:
                # Height constrained
                new_h = min(max_h, elem_img.height)
                new_w = int(new_h * elem_ratio)
            
            if new_w > 0 and new_h > 0:
                elem_img = elem_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Convert to RGBA for proper pasting
                if elem_img.mode != 'RGBA':
                    elem_img = elem_img.convert('RGBA')
                
                canvas.paste(elem_img, (x, y), elem_img)
                
        except Exception as e:
            self.logger.warning(f"Failed to place element: {e}")
    
    def _render_hero_text(
        self,
        canvas: Image.Image,
        element: ExtractedElement,
        zone: Tuple[int, int, int, int]
    ) -> None:
        """Render hero text in the specified zone."""
        from PIL import ImageFont
        
        draw = ImageDraw.Draw(canvas)
        x, y, max_w, max_h = zone
        
        text = element.content_text
        if not text:
            return
        
        # Try to load a bold font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        except:
            try:
                font = ImageFont.load_default()
            except:
                return
        
        # Get text color from visual style
        text_color = (255, 255, 255)  # Default white
        if element.visual_style.get("text_color"):
            try:
                hex_color = element.visual_style["text_color"].lstrip('#')
                text_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            except:
                pass
        
        # Draw text with shadow
        shadow_offset = 2
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 128))
        draw.text((x, y), text, font=font, fill=text_color)
    
    def _place_badges(
        self,
        canvas: Image.Image,
        badges: List[ExtractedElement],
        zone: Tuple[int, int, int, int]
    ) -> None:
        """Place multiple badges in a zone."""
        x, y, max_w, max_h = zone
        current_x = x
        
        for badge in badges:
            if badge.cropped_image_base64:
                try:
                    badge_bytes = base64.b64decode(badge.cropped_image_base64)
                    badge_img = Image.open(BytesIO(badge_bytes))
                    
                    # Scale badge
                    scale = min(max_h / badge_img.height, 1.0)
                    new_w = int(badge_img.width * scale)
                    new_h = int(badge_img.height * scale)
                    
                    if new_w > 0 and new_h > 0:
                        badge_img = badge_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        
                        if badge_img.mode != 'RGBA':
                            badge_img = badge_img.convert('RGBA')
                        
                        canvas.paste(badge_img, (current_x, y), badge_img)
                        current_x += new_w + 10  # Spacing
                        
                except Exception as e:
                    self.logger.warning(f"Failed to place badge: {e}")


def extract_ui_elements(
    screenshot_bytes: bytes,
    url: str,
    html_content: Optional[str] = None
) -> UIElementMap:
    """Convenience function to extract UI elements."""
    extractor = UIElementExtractor()
    return extractor.extract_ui_elements(screenshot_bytes, url, html_content)

