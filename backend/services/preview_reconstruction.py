"""
Semantic Preview Reconstruction Service.

This module goes beyond screenshot cropping to perform semantic understanding
and reconstruction of webpage previews.

The system:
1. Identifies individual UI components (hero, headline, CTA, features, images, etc.)
2. Extracts actual content (text, image regions, colors) from those components
3. Generates a layout plan for optimal visual communication
4. Provides structured data for frontend reconstruction

CRITICAL CONSTRAINT: Only uses existing content from the page - no fabrication.
"""
import json
import base64
import logging
import time
from io import BytesIO
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from PIL import Image
from openai import OpenAI
from backend.core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMA DEFINITIONS
# =============================================================================

class ElementType(str, Enum):
    """Types of UI elements that can be extracted."""
    PROFILE_IMAGE = "profile_image"
    HERO_IMAGE = "hero_image"
    PRODUCT_IMAGE = "product_image"
    LOGO = "logo"
    HEADLINE = "headline"
    SUBHEADLINE = "subheadline"
    BODY_TEXT = "body_text"
    CTA_BUTTON = "cta_button"
    FEATURE_ITEM = "feature_item"
    TESTIMONIAL = "testimonial"
    PRICE = "price"
    RATING = "rating"
    LOCATION = "location"
    SKILL_TAG = "skill_tag"
    SOCIAL_PROOF = "social_proof"
    NAVIGATION = "navigation"
    METADATA = "metadata"


class PreviewTemplate(str, Enum):
    """Preview layout templates."""
    PROFILE_CARD = "profile_card"
    PRODUCT_CARD = "product_card"
    LANDING_HERO = "landing_hero"
    ARTICLE_CARD = "article_card"
    SERVICE_CARD = "service_card"
    MINIMAL = "minimal"


@dataclass
class BoundingBox:
    """Normalized bounding box (0-1 range)."""
    x: float
    y: float
    width: float
    height: float
    
    def to_dict(self) -> Dict[str, float]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}
    
    def to_pixels(self, img_width: int, img_height: int) -> Tuple[int, int, int, int]:
        """Convert to pixel coordinates (left, top, right, bottom)."""
        left = int(self.x * img_width)
        top = int(self.y * img_height)
        right = int((self.x + self.width) * img_width)
        bottom = int((self.y + self.height) * img_height)
        return (left, top, right, bottom)


@dataclass
class ExtractedElement:
    """A single extracted UI element from the page."""
    id: str
    type: ElementType
    content: str  # Text content or image description
    bounding_box: BoundingBox
    priority: int  # 1 = highest priority
    include_in_preview: bool
    
    # Visual properties extracted from the element
    text_content: Optional[str] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    font_weight: Optional[str] = None
    is_image: bool = False
    image_crop_data: Optional[str] = None  # Base64 of cropped image region
    
    # Additional metadata
    confidence: float = 0.8
    extraction_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, ElementType) else self.type,
            "content": self.content,
            "bounding_box": self.bounding_box.to_dict(),
            "priority": self.priority,
            "include_in_preview": self.include_in_preview,
            "text_content": self.text_content,
            "background_color": self.background_color,
            "text_color": self.text_color,
            "font_weight": self.font_weight,
            "is_image": self.is_image,
            "image_crop_data": self.image_crop_data,
            "confidence": self.confidence,
            "extraction_notes": self.extraction_notes
        }


@dataclass
class LayoutSection:
    """A section in the reconstructed layout."""
    name: str
    element_ids: List[str]  # References to ExtractedElement IDs
    layout_direction: str  # horizontal, vertical, grid
    alignment: str  # left, center, right
    spacing: str  # tight, normal, loose
    emphasis: str  # primary, secondary, tertiary
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "element_ids": self.element_ids,
            "layout_direction": self.layout_direction,
            "alignment": self.alignment,
            "spacing": self.spacing,
            "emphasis": self.emphasis
        }


@dataclass
class LayoutPlan:
    """Complete plan for reconstructing the preview."""
    template: PreviewTemplate
    page_type: str  # profile, product, landing, article
    
    # Style extracted from original
    primary_color: str
    secondary_color: str
    accent_color: str
    background_style: str  # solid, gradient, image
    font_style: str  # modern, classic, playful
    
    # Layout structure
    sections: List[LayoutSection]
    
    # Content for reconstruction
    title: str
    subtitle: Optional[str]
    description: Optional[str]
    cta_text: Optional[str]
    
    # Reasoning
    layout_rationale: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "template": self.template.value if isinstance(self.template, PreviewTemplate) else self.template,
            "page_type": self.page_type,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "accent_color": self.accent_color,
            "background_style": self.background_style,
            "font_style": self.font_style,
            "sections": [s.to_dict() for s in self.sections],
            "title": self.title,
            "subtitle": self.subtitle,
            "description": self.description,
            "cta_text": self.cta_text,
            "layout_rationale": self.layout_rationale
        }


@dataclass
class ReconstructedPreview:
    """Final output containing all data needed for frontend reconstruction."""
    # Layout plan
    layout_plan: LayoutPlan
    
    # Extracted elements
    elements: List[ExtractedElement]
    
    # Image data
    profile_image_base64: Optional[str] = None
    hero_image_base64: Optional[str] = None
    logo_base64: Optional[str] = None
    
    # Quality metrics
    extraction_confidence: float = 0.0
    reconstruction_quality: str = "good"  # excellent, good, fair, fallback
    
    # Processing info
    processing_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "layout_plan": self.layout_plan.to_dict(),
            "elements": [e.to_dict() for e in self.elements],
            "profile_image_base64": self.profile_image_base64,
            "hero_image_base64": self.hero_image_base64,
            "logo_base64": self.logo_base64,
            "extraction_confidence": self.extraction_confidence,
            "reconstruction_quality": self.reconstruction_quality,
            "processing_time_ms": self.processing_time_ms
        }


# =============================================================================
# CONFIGURATION
# =============================================================================

class ReconstructionConfig:
    """Configuration for preview reconstruction."""
    AI_TIMEOUT: int = 60
    MAX_RETRIES: int = 2
    MAX_IMAGE_DIMENSION: int = 2048
    JPEG_QUALITY: int = 90
    CROP_QUALITY: int = 95
    MIN_ELEMENT_CONFIDENCE: float = 0.6


# =============================================================================
# IMAGE PROCESSING
# =============================================================================

def prepare_image(screenshot_bytes: bytes) -> Tuple[str, Image.Image, Dict[str, Any]]:
    """
    Prepare image for AI analysis.
    
    Returns:
        Tuple of (base64_string, PIL_image, info_dict)
    """
    image = Image.open(BytesIO(screenshot_bytes))
    original_size = image.size
    
    # Resize if needed
    max_dim = ReconstructionConfig.MAX_IMAGE_DIMENSION
    if image.width > max_dim or image.height > max_dim:
        ratio = min(max_dim / image.width, max_dim / image.height)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    # Convert to RGB
    if image.mode in ('RGBA', 'P', 'LA'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        if image.mode in ('RGBA', 'LA'):
            background.paste(image, mask=image.split()[-1])
        image = background
    
    # To base64
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=ReconstructionConfig.JPEG_QUALITY)
    base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    info = {
        "original_size": original_size,
        "processed_size": image.size
    }
    
    return base64_str, image, info


def crop_element(image: Image.Image, bbox: BoundingBox) -> str:
    """
    Crop an element from the image and return as base64.
    """
    coords = bbox.to_pixels(image.width, image.height)
    
    # Ensure valid coordinates
    left = max(0, coords[0])
    top = max(0, coords[1])
    right = min(image.width, coords[2])
    bottom = min(image.height, coords[3])
    
    if right <= left or bottom <= top:
        return ""
    
    cropped = image.crop((left, top, right, bottom))
    
    buffer = BytesIO()
    cropped.save(buffer, format='PNG', optimize=True)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


# =============================================================================
# AI PROMPTS
# =============================================================================

ELEMENT_EXTRACTION_PROMPT = """You are an expert UI/UX analyst. Analyze this webpage screenshot to identify and extract individual UI components.

Your task is to:
1. Identify distinct UI elements (images, text blocks, buttons, etc.)
2. Determine their exact bounding boxes (normalized 0-1 coordinates)
3. Extract the actual text content where applicable
4. Assess which elements are most important for a preview

OUTPUT STRICT JSON:
{{
    "page_type": "<profile|product|landing|article|service|unknown>",
    "elements": [
        {{
            "id": "<unique_id>",
            "type": "<profile_image|hero_image|product_image|logo|headline|subheadline|body_text|cta_button|feature_item|testimonial|price|rating|location|skill_tag|social_proof|navigation|metadata>",
            "content": "<exact text content or image description>",
            "bounding_box": {{"x": <0-1>, "y": <0-1>, "width": <0-1>, "height": <0-1>}},
            "priority": <1-5, 1=highest>,
            "include_in_preview": <true|false>,
            "text_content": "<exact text if applicable>",
            "background_color": "<hex color if detectable>",
            "text_color": "<hex color if detectable>",
            "font_weight": "<normal|bold|light>",
            "is_image": <true|false>,
            "confidence": <0-1>,
            "extraction_notes": "<any notes about this element>"
        }}
    ],
    "detected_colors": {{
        "primary": "<hex>",
        "secondary": "<hex>",
        "accent": "<hex>",
        "background": "<hex>"
    }},
    "overall_style": "<modern|classic|playful|professional|minimal>",
    "confidence": <0-1>
}}

EXTRACTION GUIDELINES:
1. Be PRECISE with bounding boxes - they will be used to crop actual image regions
2. Extract EXACT text content - do not paraphrase or summarize
3. For images: describe what you see (e.g., "Professional headshot of man in blue shirt")
4. Priority 1 = most visually prominent and important for preview
5. Set include_in_preview=true for elements that should appear in the reconstructed preview
6. Identify at most 8-10 key elements - quality over quantity

For PROFILE pages, prioritize: profile_image, headline (name), subheadline (title/role), skill_tags, location, rating
For PRODUCT pages, prioritize: product_image, headline (name), price, cta_button, feature_items
For LANDING pages, prioritize: hero_image, headline, subheadline, cta_button
For ARTICLE pages, prioritize: headline, hero_image, body_text (first paragraph)"""


LAYOUT_PLANNING_PROMPT = """Based on the extracted elements, create an optimal layout plan for a preview card.

EXTRACTED ELEMENTS:
{elements_json}

PAGE TYPE: {page_type}
DETECTED STYLE: {style}
COLORS: Primary={primary}, Secondary={secondary}, Accent={accent}

Create a layout plan that:
1. Uses ONLY the extracted elements (no fabricated content)
2. Arranges them for maximum visual impact and clarity
3. Prioritizes the most important information
4. Creates a cohesive, professional preview

OUTPUT STRICT JSON:
{{
    "template": "<profile_card|product_card|landing_hero|article_card|service_card|minimal>",
    "sections": [
        {{
            "name": "<section_name>",
            "element_ids": ["<element_id>", ...],
            "layout_direction": "<horizontal|vertical|grid>",
            "alignment": "<left|center|right>",
            "spacing": "<tight|normal|loose>",
            "emphasis": "<primary|secondary|tertiary>"
        }}
    ],
    "title": "<extracted title to display>",
    "subtitle": "<extracted subtitle if any>",
    "description": "<extracted description, max 150 chars>",
    "cta_text": "<extracted CTA text if any>",
    "background_style": "<solid|gradient|image>",
    "font_style": "<modern|classic|playful|professional>",
    "layout_rationale": "<explain why this layout works>"
}}

LAYOUT PRINCIPLES:
1. Lead with the most visually striking element (usually image or bold headline)
2. Create clear visual hierarchy through section emphasis
3. Group related elements (e.g., name + title, price + CTA)
4. Ensure the preview tells a clear story in 2-3 seconds
5. Don't overcrowd - sometimes less is more"""


# =============================================================================
# CORE EXTRACTION FUNCTIONS
# =============================================================================

def extract_elements(
    screenshot_bytes: bytes,
    url: str = ""
) -> Tuple[List[ExtractedElement], Dict[str, Any], Image.Image]:
    """
    Extract UI elements from a screenshot using AI vision.
    
    Returns:
        Tuple of (elements_list, metadata_dict, PIL_image)
    """
    start_time = time.time()
    
    # Prepare image
    image_base64, pil_image, prep_info = prepare_image(screenshot_bytes)
    
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=ReconstructionConfig.AI_TIMEOUT)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a UI/UX expert that extracts structured data from webpage screenshots. Output valid JSON only."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": ELEMENT_EXTRACTION_PROMPT
                        },
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
            max_tokens=2500,
            temperature=0.2
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        data = json.loads(content)
        
        # Build element list
        elements = []
        for elem_data in data.get("elements", []):
            try:
                bbox = BoundingBox(
                    x=float(elem_data["bounding_box"]["x"]),
                    y=float(elem_data["bounding_box"]["y"]),
                    width=float(elem_data["bounding_box"]["width"]),
                    height=float(elem_data["bounding_box"]["height"])
                )
                
                elem_type = elem_data.get("type", "metadata")
                try:
                    elem_type = ElementType(elem_type)
                except ValueError:
                    elem_type = ElementType.METADATA
                
                element = ExtractedElement(
                    id=elem_data.get("id", f"elem_{len(elements)}"),
                    type=elem_type,
                    content=elem_data.get("content", ""),
                    bounding_box=bbox,
                    priority=int(elem_data.get("priority", 5)),
                    include_in_preview=elem_data.get("include_in_preview", False),
                    text_content=elem_data.get("text_content"),
                    background_color=elem_data.get("background_color"),
                    text_color=elem_data.get("text_color"),
                    font_weight=elem_data.get("font_weight"),
                    is_image=elem_data.get("is_image", False),
                    confidence=float(elem_data.get("confidence", 0.8)),
                    extraction_notes=elem_data.get("extraction_notes")
                )
                
                # Crop image regions for image elements
                if element.is_image and element.include_in_preview:
                    element.image_crop_data = crop_element(pil_image, bbox)
                
                elements.append(element)
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Failed to parse element: {e}")
                continue
        
        metadata = {
            "page_type": data.get("page_type", "unknown"),
            "detected_colors": data.get("detected_colors", {}),
            "overall_style": data.get("overall_style", "modern"),
            "confidence": data.get("confidence", 0.5),
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }
        
        logger.info(f"Extracted {len(elements)} elements from screenshot")
        return elements, metadata, pil_image
        
    except Exception as e:
        logger.error(f"Element extraction failed: {e}")
        return [], {"error": str(e)}, pil_image


def generate_layout_plan(
    elements: List[ExtractedElement],
    metadata: Dict[str, Any]
) -> LayoutPlan:
    """
    Generate an optimal layout plan based on extracted elements.
    """
    # Prepare elements for the prompt
    elements_for_prompt = [
        {
            "id": e.id,
            "type": e.type.value if isinstance(e.type, ElementType) else e.type,
            "content": e.content[:200] if e.content else "",
            "text_content": e.text_content[:200] if e.text_content else None,
            "priority": e.priority,
            "include_in_preview": e.include_in_preview,
            "is_image": e.is_image
        }
        for e in elements if e.include_in_preview or e.priority <= 2
    ]
    
    colors = metadata.get("detected_colors", {})
    
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=ReconstructionConfig.AI_TIMEOUT)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a UI/UX designer creating optimal preview layouts. Output valid JSON only."
                },
                {
                    "role": "user",
                    "content": LAYOUT_PLANNING_PROMPT.format(
                        elements_json=json.dumps(elements_for_prompt, indent=2),
                        page_type=metadata.get("page_type", "unknown"),
                        style=metadata.get("overall_style", "modern"),
                        primary=colors.get("primary", "#2563eb"),
                        secondary=colors.get("secondary", "#1e293b"),
                        accent=colors.get("accent", "#f59e0b")
                    )
                }
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        data = json.loads(content)
        
        # Build sections
        sections = []
        for sec_data in data.get("sections", []):
            sections.append(LayoutSection(
                name=sec_data.get("name", "content"),
                element_ids=sec_data.get("element_ids", []),
                layout_direction=sec_data.get("layout_direction", "vertical"),
                alignment=sec_data.get("alignment", "left"),
                spacing=sec_data.get("spacing", "normal"),
                emphasis=sec_data.get("emphasis", "secondary")
            ))
        
        # Determine template
        template_str = data.get("template", "minimal")
        try:
            template = PreviewTemplate(template_str)
        except ValueError:
            template = PreviewTemplate.MINIMAL
        
        plan = LayoutPlan(
            template=template,
            page_type=metadata.get("page_type", "unknown"),
            primary_color=colors.get("primary", "#2563eb"),
            secondary_color=colors.get("secondary", "#1e293b"),
            accent_color=colors.get("accent", "#f59e0b"),
            background_style=data.get("background_style", "solid"),
            font_style=data.get("font_style", "modern"),
            sections=sections,
            title=data.get("title", ""),
            subtitle=data.get("subtitle"),
            description=data.get("description"),
            cta_text=data.get("cta_text"),
            layout_rationale=data.get("layout_rationale", "")
        )
        
        logger.info(f"Generated layout plan: template={plan.template.value}")
        return plan
        
    except Exception as e:
        logger.error(f"Layout planning failed: {e}")
        # Return fallback plan
        return _get_fallback_layout_plan(elements, metadata)


def _get_fallback_layout_plan(
    elements: List[ExtractedElement],
    metadata: Dict[str, Any]
) -> LayoutPlan:
    """Generate a fallback layout plan when AI fails."""
    colors = metadata.get("detected_colors", {})
    
    # Find key elements
    headline_elem = next((e for e in elements if e.type == ElementType.HEADLINE), None)
    image_elem = next((e for e in elements if e.is_image and e.priority <= 2), None)
    
    return LayoutPlan(
        template=PreviewTemplate.MINIMAL,
        page_type=metadata.get("page_type", "unknown"),
        primary_color=colors.get("primary", "#2563eb"),
        secondary_color=colors.get("secondary", "#1e293b"),
        accent_color=colors.get("accent", "#f59e0b"),
        background_style="solid",
        font_style="modern",
        sections=[
            LayoutSection(
                name="main",
                element_ids=[e.id for e in elements if e.include_in_preview][:5],
                layout_direction="vertical",
                alignment="center",
                spacing="normal",
                emphasis="primary"
            )
        ],
        title=headline_elem.text_content if headline_elem else "",
        subtitle=None,
        description=None,
        cta_text=None,
        layout_rationale="Fallback layout due to AI error"
    )


# =============================================================================
# MAIN RECONSTRUCTION FUNCTION
# =============================================================================

def reconstruct_preview(
    screenshot_bytes: bytes,
    url: str = ""
) -> ReconstructedPreview:
    """
    Main entry point for semantic preview reconstruction.
    
    This function:
    1. Extracts individual UI elements from the screenshot
    2. Generates an optimal layout plan
    3. Crops key image regions
    4. Returns structured data for frontend reconstruction
    
    Args:
        screenshot_bytes: Raw PNG screenshot bytes
        url: URL for context
        
    Returns:
        ReconstructedPreview with all data needed for frontend rendering
    """
    start_time = time.time()
    
    # Step 1: Extract elements
    elements, metadata, pil_image = extract_elements(screenshot_bytes, url)
    
    if not elements:
        logger.warning("No elements extracted, using fallback")
        return _get_fallback_preview(screenshot_bytes)
    
    # Step 2: Generate layout plan
    layout_plan = generate_layout_plan(elements, metadata)
    
    # Step 3: Extract key images
    profile_image = None
    hero_image = None
    logo_image = None
    
    for elem in elements:
        if elem.is_image and elem.image_crop_data:
            if elem.type == ElementType.PROFILE_IMAGE:
                profile_image = elem.image_crop_data
            elif elem.type in (ElementType.HERO_IMAGE, ElementType.PRODUCT_IMAGE):
                hero_image = elem.image_crop_data
            elif elem.type == ElementType.LOGO:
                logo_image = elem.image_crop_data
    
    # If no specific images found, use the first high-priority image
    if not profile_image and not hero_image:
        image_elem = next((e for e in elements if e.is_image and e.image_crop_data and e.priority <= 2), None)
        if image_elem:
            if layout_plan.page_type == "profile":
                profile_image = image_elem.image_crop_data
            else:
                hero_image = image_elem.image_crop_data
    
    # Calculate quality
    avg_confidence = sum(e.confidence for e in elements) / len(elements) if elements else 0
    quality = "excellent" if avg_confidence > 0.85 else "good" if avg_confidence > 0.7 else "fair"
    
    processing_time = int((time.time() - start_time) * 1000)
    
    result = ReconstructedPreview(
        layout_plan=layout_plan,
        elements=elements,
        profile_image_base64=profile_image,
        hero_image_base64=hero_image,
        logo_base64=logo_image,
        extraction_confidence=avg_confidence,
        reconstruction_quality=quality,
        processing_time_ms=processing_time
    )
    
    logger.info(f"Preview reconstruction complete: quality={quality}, elements={len(elements)}, time={processing_time}ms")
    
    return result


def _get_fallback_preview(screenshot_bytes: bytes) -> ReconstructedPreview:
    """Generate a fallback preview when extraction fails."""
    # Use full screenshot as hero image
    image = Image.open(BytesIO(screenshot_bytes))
    
    # Crop top portion as fallback
    crop_height = int(image.height * 0.6)
    cropped = image.crop((0, 0, image.width, crop_height))
    
    buffer = BytesIO()
    cropped.save(buffer, format='PNG', optimize=True)
    hero_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return ReconstructedPreview(
        layout_plan=LayoutPlan(
            template=PreviewTemplate.MINIMAL,
            page_type="unknown",
            primary_color="#2563eb",
            secondary_color="#1e293b",
            accent_color="#f59e0b",
            background_style="solid",
            font_style="modern",
            sections=[],
            title="Page Preview",
            subtitle=None,
            description=None,
            cta_text=None,
            layout_rationale="Fallback: Could not extract elements"
        ),
        elements=[],
        profile_image_base64=None,
        hero_image_base64=hero_base64,
        logo_base64=None,
        extraction_confidence=0.2,
        reconstruction_quality="fallback",
        processing_time_ms=0
    )

