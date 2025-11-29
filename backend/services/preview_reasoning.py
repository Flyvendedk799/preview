"""
Multi-Stage Preview Reasoning Framework.

This module implements a systematic, step-by-step reasoning process for
generating high-quality preview reconstructions. The framework is designed
to generalize across different websites, layouts, and industries.

DESIGN PRINCIPLES:
1. Explicit multi-stage reasoning (not heuristics)
2. Generalization over perfection for edge cases
3. Transparent decision framework
4. Premium SaaS quality bar
5. Modular and extensible

REASONING STAGES:
1. SEGMENTATION: Identify distinct UI/UX regions
2. PURPOSE ANALYSIS: Determine each region's communication role
3. PRIORITY ASSIGNMENT: Rank by visual importance
4. COMPOSITION DECISION: What to keep, reorder, or remove
5. LAYOUT SYNTHESIS: Generate optimized structure
6. COHERENCE CHECK: Validate balance and flow
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
# REASONING SCHEMA
# =============================================================================

class RegionPurpose(str, Enum):
    """The communication purpose of a UI region."""
    IDENTITY = "identity"       # Who/what this is (name, logo, profile)
    VALUE_PROP = "value_prop"   # Core message or offering
    CONTEXT = "context"         # Supporting information (location, date)
    CREDIBILITY = "credibility" # Trust signals (ratings, testimonials)
    ACTION = "action"           # CTAs and conversion elements
    NAVIGATION = "navigation"   # Wayfinding elements
    DECORATION = "decoration"   # Visual enhancement only


class VisualWeight(str, Enum):
    """The visual weight/importance of an element."""
    HERO = "hero"           # Dominant visual anchor (1 per preview)
    PRIMARY = "primary"     # Key supporting element (1-2 per preview)
    SECONDARY = "secondary" # Supporting detail (2-4 per preview)
    TERTIARY = "tertiary"   # Minor detail (use sparingly)
    OMIT = "omit"           # Should not appear in preview


@dataclass
class AnalyzedRegion:
    """A UI region with full reasoning attached."""
    id: str
    content_type: str  # image, text, badge, button, etc.
    raw_content: str   # Exact extracted content
    
    # Stage 2: Purpose
    purpose: RegionPurpose
    purpose_reasoning: str
    
    # Stage 3: Priority
    visual_weight: VisualWeight
    priority_score: float  # 0-1
    priority_reasoning: str
    
    # Stage 4: Decision
    include_in_preview: bool
    decision_reasoning: str
    
    # Extracted values
    display_text: Optional[str] = None  # Clean text for display
    image_data: Optional[str] = None    # Base64 if image
    
    # Bounding box for cropping
    bbox: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content_type": self.content_type,
            "raw_content": self.raw_content,
            "purpose": self.purpose.value,
            "purpose_reasoning": self.purpose_reasoning,
            "visual_weight": self.visual_weight.value,
            "priority_score": self.priority_score,
            "priority_reasoning": self.priority_reasoning,
            "include_in_preview": self.include_in_preview,
            "decision_reasoning": self.decision_reasoning,
            "display_text": self.display_text,
            "has_image": self.image_data is not None,
            "bbox": self.bbox
        }


@dataclass
class LayoutBlueprint:
    """The final layout structure with explicit reasoning."""
    template_type: str  # profile, product, landing, article, service
    
    # Color palette extracted
    primary_color: str
    secondary_color: str
    accent_color: str
    
    # Content slots with assigned regions
    identity_slot: Optional[str] = None      # Main identifier (name/title)
    identity_image_slot: Optional[str] = None  # Avatar/logo/hero
    tagline_slot: Optional[str] = None       # Brief descriptor
    value_slot: Optional[str] = None         # Core value proposition
    context_slots: List[str] = field(default_factory=list)  # Location, date, etc.
    credibility_slots: List[str] = field(default_factory=list)  # Ratings, social proof
    action_slot: Optional[str] = None        # Primary CTA
    tags_slots: List[str] = field(default_factory=list)  # Skills, categories
    
    # Layout decisions
    layout_reasoning: str = ""
    composition_notes: str = ""
    
    # Quality metrics
    coherence_score: float = 0.0
    balance_score: float = 0.0
    clarity_score: float = 0.0
    overall_quality: str = "good"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_type": self.template_type,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "accent_color": self.accent_color,
            "identity_slot": self.identity_slot,
            "identity_image_slot": self.identity_image_slot,
            "tagline_slot": self.tagline_slot,
            "value_slot": self.value_slot,
            "context_slots": self.context_slots,
            "credibility_slots": self.credibility_slots,
            "action_slot": self.action_slot,
            "tags_slots": self.tags_slots,
            "layout_reasoning": self.layout_reasoning,
            "composition_notes": self.composition_notes,
            "coherence_score": self.coherence_score,
            "balance_score": self.balance_score,
            "clarity_score": self.clarity_score,
            "overall_quality": self.overall_quality
        }


@dataclass
class ReasonedPreview:
    """Complete preview with full reasoning chain."""
    # Analyzed regions
    regions: List[AnalyzedRegion]
    
    # Layout blueprint
    blueprint: LayoutBlueprint
    
    # Final content for rendering
    title: str
    subtitle: Optional[str]
    description: Optional[str]
    tags: List[str]
    context_items: List[Dict[str, str]]  # {icon, text}
    credibility_items: List[Dict[str, str]]  # {type, value}
    cta_text: Optional[str]
    
    # Images
    primary_image_base64: Optional[str]
    
    # Processing metadata
    processing_time_ms: int
    reasoning_confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "regions": [r.to_dict() for r in self.regions],
            "blueprint": self.blueprint.to_dict(),
            "title": self.title,
            "subtitle": self.subtitle,
            "description": self.description,
            "tags": self.tags,
            "context_items": self.context_items,
            "credibility_items": self.credibility_items,
            "cta_text": self.cta_text,
            "has_primary_image": self.primary_image_base64 is not None,
            "processing_time_ms": self.processing_time_ms,
            "reasoning_confidence": self.reasoning_confidence
        }


# =============================================================================
# AI PROMPTS - Multi-Stage Reasoning
# =============================================================================

STAGE_1_2_3_PROMPT = """You are a senior UI/UX analyst performing systematic visual analysis.

TASK: Analyze this webpage screenshot through a rigorous multi-stage process.

=== STAGE 1: SEGMENTATION ===
Identify ALL distinct UI regions visible. For each region, note:
- What type of content it contains (image, text, badge, button, etc.)
- Its approximate position
- Its exact content

IMPROVEMENT: Pay special attention to:
- LOGO detection: Look for brand logos in header, favicon area, or prominent positions
- TRUST SIGNALS: Ratings, reviews, certifications, security badges, statistics
- BENEFIT BULLETS: Feature lists, value propositions, key selling points
- SOCIAL PROOF: Testimonials, user counts, success metrics

=== STAGE 2: PURPOSE ANALYSIS ===
For each region, determine its COMMUNICATION PURPOSE:
- identity: Who/what this is (name, logo, profile image)
- value_prop: Core message or what they offer
- benefits: Supporting benefits, features, or selling points (NEW - extract 2-3 key benefits)
- context: Supporting info (location, date, company)
- credibility: Trust signals (ratings, reviews, certifications, statistics, security badges)
- action: CTAs and conversion elements
- navigation: Menu items, tabs (usually exclude from preview)
- decoration: Pure visual enhancement (usually exclude)

REASONING REQUIRED: Explain WHY each region has its assigned purpose.

=== STAGE 3: PRIORITY ASSIGNMENT ===
Assign visual weight based on what users should see FIRST in a preview:
- hero: ONE dominant element (usually the main image or headline)
- primary: 1-2 key supporting elements (main value prop, primary benefit)
- secondary: 2-4 supporting details (additional benefits, trust signals)
- tertiary: Minor details (use sparingly in previews)
- omit: Should not appear (navigation, redundant info, clutter)

REASONING REQUIRED: Explain the priority logic.

OUTPUT STRICT JSON:
{{
    "page_type": "<profile|product|landing|article|service|unknown>",
    "regions": [
        {{
            "id": "<unique_id>",
            "content_type": "<image|headline|subheadline|body_text|badge|button|rating|location|tag|logo|benefit|statistic|testimonial|other>",
            "raw_content": "<exact content>",
            "bbox": {{"x": <0-1>, "y": <0-1>, "width": <0-1>, "height": <0-1>}},
            "purpose": "<identity|value_prop|benefits|context|credibility|action|navigation|decoration>",
            "purpose_reasoning": "<why this purpose>",
            "visual_weight": "<hero|primary|secondary|tertiary|omit>",
            "priority_score": <0.0-1.0>,
            "priority_reasoning": "<why this priority>",
            "is_logo": <true|false>  // NEW: Explicitly identify if this is a logo/brand mark
        }}
    ],
    "detected_palette": {{
        "primary": "<hex>",  // Extract from hero section, main buttons, or brand colors
        "secondary": "<hex>",  // Extract from secondary elements
        "accent": "<hex>"  // Extract from CTAs, highlights, or brand accent
    }},
    "detected_logo": {{
        "region_id": "<region_id or null>",  // NEW: Reference to logo region if found
        "confidence": <0.0-1.0>  // NEW: Confidence that this is actually a logo
    }},
    "analysis_confidence": <0.0-1.0>
}}

CRITICAL RULES:
1. Extract EXACT text content - no paraphrasing
2. Be PRECISE with bounding boxes - use normalized coordinates (0-1)
3. Provide GENUINE reasoning, not templates
4. Identify ALL visible regions, then filter by weight
5. HERO weight should be assigned to only ONE element
6. Navigation elements should usually be weight=omit
7. Duplicate/redundant content should be weight=omit

BOUNDING BOX PRECISION (very important):
- For PROFILE IMAGES (circular avatars): 
  * The bbox should encompass the ENTIRE circular avatar area
  * Include slight padding around the circle to capture the full image
  * x,y should be the top-left corner of the bounding rectangle containing the circle
  * width,height should cover the full circular avatar
- For rectangular images: bbox should tightly fit the image bounds
- All coordinates are normalized (0-1 relative to image dimensions)

Example for a profile avatar at position (100,50) with size 80x80 on a 800x600 image:
bbox: {"x": 0.1, "y": 0.067, "width": 0.1, "height": 0.133}"""


STAGE_4_5_PROMPT = """You are a senior visual designer creating an optimal preview layout.

ANALYZED REGIONS:
{regions_json}

PAGE TYPE: {page_type}
COLORS: Primary={primary}, Secondary={secondary}, Accent={accent}

=== STAGE 4: COMPOSITION DECISION ===
For each region, decide:
- INCLUDE: Essential for communicating the page's core message
- EXCLUDE: Redundant, noisy, or low-value for a preview

Rules for high-quality previews:
1. ONE clear identity (name/title) - no duplicates
2. ONE primary image maximum
3. NO navigation elements
4. NO redundant "About [Name]" headers if name is already shown
5. MAX 4 tags/badges (select most relevant)
6. Prefer concise value propositions over long descriptions
7. Include location/context only if it adds value
8. Include credibility items if they are visually prominent, even if the value is zero (e.g., "0 reviews" can be important for transparency)

=== STAGE 5: LAYOUT SYNTHESIS ===
Assign included regions to layout slots:
- identity_slot: Main name/title (clean, no prefix like "Om" or "About")
- identity_image_slot: Profile image/avatar/logo (PRIORITIZE detected logo if available)
- tagline_slot: Brief professional descriptor (role, specialty)
- value_slot: Core value proposition or about text
- benefits_slots: Key benefits or features (max 2-3, NEW - extract supporting benefits)
- context_slots: Location, date, company (max 2)
- credibility_slots: Ratings, testimonials, statistics, security badges (max 2-3, include if visually prominent even if zero)
- action_slot: Primary CTA
- tags_slots: Skills, categories (max 4)

OUTPUT JSON:
{{
    "composition_decisions": [
        {{
            "region_id": "<id>",
            "include": <true|false>,
            "decision_reasoning": "<why include/exclude>"
        }}
    ],
    "layout": {{
        "template_type": "<profile|product|landing|article|service>",
        "identity_slot": "<region_id or null>",
        "identity_image_slot": "<region_id or null>",  // PRIORITIZE logo if detected
        "tagline_slot": "<region_id or null>",
        "value_slot": "<region_id or null>",
        "benefits_slots": ["<region_id>"],  // NEW: 2-3 key benefits
        "context_slots": ["<region_id>"],
        "credibility_slots": ["<region_id>"],  // Can include up to 3 for rich trust signals
        "action_slot": "<region_id or null>",
        "tags_slots": ["<region_id>"]
    }},
    "layout_reasoning": "<explain the overall layout strategy>",
    "composition_notes": "<any adjustments made to content>"
}}

QUALITY GUIDELINES:
1. A preview should tell a clear story in 2-3 seconds
2. Visual hierarchy: Identity → Value → Context → Credibility
3. Avoid redundancy: Same info shouldn't appear twice
4. Clean over complete: Better to omit than clutter
5. Professional feel: Every element should feel intentional"""


STAGE_6_PROMPT = """Perform final quality validation on this preview layout.

LAYOUT PLAN:
{layout_json}

INCLUDED REGIONS:
{included_regions}

=== STAGE 6: COHERENCE CHECK ===
Evaluate:

1. COHERENCE (0-1): Does the preview tell a unified story?
   - Is the identity clear?
   - Does the value proposition make sense?
   - Are context elements relevant?

2. BALANCE (0-1): Is the visual composition balanced?
   - Not too empty, not too crowded
   - Proper hierarchy from top to bottom
   - Appropriate number of elements

3. CLARITY (0-1): Will users understand this in 2 seconds?
   - Is the main message obvious?
   - Are there confusing elements?
   - Is the purpose of the page clear?

OUTPUT JSON:
{{
    "coherence_score": <0.0-1.0>,
    "coherence_notes": "<specific observations>",
    "balance_score": <0.0-1.0>,
    "balance_notes": "<specific observations>",
    "clarity_score": <0.0-1.0>,
    "clarity_notes": "<specific observations>",
    "overall_quality": "<excellent|good|fair|poor>",
    "improvement_suggestions": ["<suggestion>"]
}}"""


# =============================================================================
# IMAGE PREPARATION
# =============================================================================

def prepare_image(screenshot_bytes: bytes) -> Tuple[str, Image.Image]:
    """Prepare image for AI analysis."""
    image = Image.open(BytesIO(screenshot_bytes))
    
    # Resize if needed
    max_dim = 2048
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
    image.save(buffer, format='JPEG', quality=90)
    base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return base64_str, image


def crop_region(image: Image.Image, bbox: Dict[str, float], is_profile_image: bool = False) -> str:
    """
    Crop a region from the image.
    
    For profile images, ensures a square, centered crop with padding
    to handle imprecise bounding boxes from AI detection.
    """
    # Calculate raw coordinates
    left = int(bbox['x'] * image.width)
    top = int(bbox['y'] * image.height)
    right = int((bbox['x'] + bbox['width']) * image.width)
    bottom = int((bbox['y'] + bbox['height']) * image.height)
    
    # Add padding to make cropping more forgiving (15% of each dimension for better coverage)
    padding_x = int((right - left) * 0.15)
    padding_y = int((bottom - top) * 0.15)
    
    left = max(0, left - padding_x)
    top = max(0, top - padding_y)
    right = min(image.width, right + padding_x)
    bottom = min(image.height, bottom + padding_y)
    
    if right <= left or bottom <= top:
        return ""
    
    # For profile images, ensure square crop centered on the detected region
    if is_profile_image:
        width = right - left
        height = bottom - top
        
        # Make it square by taking the larger dimension, with extra padding for circular avatars
        size = max(width, height)
        # Add 20% more to ensure we capture the full circular avatar
        size = int(size * 1.2)
        
        # Center the square on the original detection
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        
        # Calculate new bounds
        half_size = size // 2
        left = max(0, center_x - half_size)
        top = max(0, center_y - half_size)
        right = min(image.width, center_x + half_size)
        bottom = min(image.height, center_y + half_size)
        
        # Re-adjust if we hit image bounds (try to maintain square)
        actual_width = right - left
        actual_height = bottom - top
        
        # If we lost size due to bounds, try to expand the other dimension
        if actual_width < size and actual_height < size:
            # Try to expand horizontally if possible
            if right < image.width:
                right = min(image.width, left + size)
            elif left > 0:
                left = max(0, right - size)
            # Try to expand vertically if possible
            if bottom < image.height:
                bottom = min(image.height, top + size)
            elif top > 0:
                top = max(0, bottom - size)
    
    if right <= left or bottom <= top:
        return ""
    
    cropped = image.crop((left, top, right, bottom))
    
    # For profile images, resize to a consistent size for quality
    if is_profile_image and cropped.width > 0:
        target_size = 256
        cropped = cropped.resize((target_size, target_size), Image.Resampling.LANCZOS)
    
    buffer = BytesIO()
    cropped.save(buffer, format='PNG', optimize=True)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


# =============================================================================
# CORE REASONING ENGINE
# =============================================================================

def run_stages_1_2_3(screenshot_bytes: bytes) -> Tuple[List[Dict], Dict[str, str], str, float]:
    """
    Run Stages 1-3: Segmentation, Purpose Analysis, Priority Assignment.
    
    Returns:
        Tuple of (regions_list, color_palette, page_type, confidence)
    """
    image_base64, pil_image = prepare_image(screenshot_bytes)
    
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=60)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a UI/UX expert performing systematic visual analysis. Output valid JSON only."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": STAGE_1_2_3_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}", "detail": "high"}
                    }
                ]
            }
        ],
        max_tokens=3000,
        temperature=0.2
    )
    
    content = response.choices[0].message.content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    data = json.loads(content)
    
    # IMPROVEMENT: Extract logo information if detected
    detected_logo = data.get("detected_logo", {})
    logo_region_id = detected_logo.get("region_id") if detected_logo else None
    
    # Crop images for included regions
    for region in data.get("regions", []):
        if region.get("content_type") == "image" and region.get("bbox"):
            # Check if this is a profile/identity image or logo for special handling
            is_profile = region.get("purpose") == "identity"
            is_logo = region.get("is_logo", False) or region.get("id") == logo_region_id
            
            # Crop the region (use profile handling for logos too)
            try:
                image_data = crop_region(pil_image, region["bbox"], is_profile_image=(is_profile or is_logo))
                if image_data:
                    region["image_data"] = image_data
                    # Mark as logo if detected
                    if is_logo:
                        region["is_logo"] = True
            except Exception as e:
                logger.warning(f"Failed to crop region {region.get('id')}: {e}")
    
    return (
        data.get("regions", []),
        data.get("detected_palette", {"primary": "#3B82F6", "secondary": "#1E293B", "accent": "#F59E0B"}),
        data.get("page_type", "unknown"),
        data.get("analysis_confidence", 0.7)
    )


def run_stages_4_5(regions: List[Dict], page_type: str, palette: Dict[str, str]) -> Dict[str, Any]:
    """
    Run Stages 4-5: Composition Decision, Layout Synthesis.
    
    Returns:
        Layout plan dictionary
    """
    # Filter to non-omit regions for composition decisions
    relevant_regions = [r for r in regions if r.get("visual_weight") != "omit"]
    
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=45)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a visual designer creating optimal preview layouts. Output valid JSON only."
            },
            {
                "role": "user",
                "content": STAGE_4_5_PROMPT.format(
                    regions_json=json.dumps(relevant_regions, indent=2),
                    page_type=page_type,
                    primary=palette.get("primary", "#3B82F6"),
                    secondary=palette.get("secondary", "#1E293B"),
                    accent=palette.get("accent", "#F59E0B")
                )
            }
        ],
        max_tokens=1500,
        temperature=0.3
    )
    
    content = response.choices[0].message.content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    return json.loads(content)


def run_stage_6(layout: Dict[str, Any], included_regions: List[Dict]) -> Dict[str, Any]:
    """
    Run Stage 6: Coherence Check.
    
    Returns:
        Quality scores dictionary
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a quality reviewer for visual designs. Output valid JSON only."
            },
            {
                "role": "user",
                "content": STAGE_6_PROMPT.format(
                    layout_json=json.dumps(layout, indent=2),
                    included_regions=json.dumps(included_regions, indent=2)
                )
            }
        ],
        max_tokens=500,
        temperature=0.2
    )
    
    content = response.choices[0].message.content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    return json.loads(content)


# =============================================================================
# CONTENT REFINEMENT
# =============================================================================

def clean_display_text(raw_text: str, purpose: str) -> str:
    """
    Clean and refine text for display.
    
    Removes prefixes like "Om", "About" when not appropriate.
    """
    if not raw_text:
        return ""
    
    text = raw_text.strip()
    
    # For identity slots, remove "Om" or "About" prefixes
    if purpose == "identity":
        prefixes_to_remove = ["om ", "about ", "meet "]
        text_lower = text.lower()
        for prefix in prefixes_to_remove:
            if text_lower.startswith(prefix):
                text = text[len(prefix):].strip()
                break
    
    return text


def extract_final_content(
    regions: List[Dict],
    layout: Dict[str, Any],
    composition_decisions: List[Dict]
) -> Dict[str, Any]:
    """
    Extract final content for rendering based on layout slots.
    """
    # Build region lookup
    region_map = {r["id"]: r for r in regions}
    
    # Build inclusion map
    included = {d["region_id"]: d["include"] for d in composition_decisions}
    
    layout_slots = layout.get("layout", {})
    
    # Extract content for each slot
    def get_region_content(region_id: str, purpose: str = "") -> Optional[str]:
        if not region_id or region_id not in region_map:
            return None
        region = region_map[region_id]
        raw = region.get("raw_content", "")
        return clean_display_text(raw, purpose)
    
    def get_region_image(region_id: str) -> Optional[str]:
        if not region_id or region_id not in region_map:
            return None
        region = region_map[region_id]
        return region.get("image_data")
    
    # Extract primary identity with comprehensive fallbacks
    title = get_region_content(layout_slots.get("identity_slot"), "identity")
    
    # Fallback: Search all included regions for identity content
    if not title or title == "Untitled":
        # Try tagline slot as fallback
        title = get_region_content(layout_slots.get("tagline_slot"), "tagline")
        
        # If still no title, search included regions for identity purpose
        if not title or title == "Untitled":
            for region_id, include_flag in included.items():
                if include_flag and region_id in region_map:
                    region = region_map[region_id]
                    if region.get("purpose") == "identity":
                        title = get_region_content(region_id, "identity")
                        if title and title != "Untitled":
                            break
            
            # Last resort: find any high-priority text region
            if not title or title == "Untitled":
                for region in regions:
                    if included.get(region["id"], False):
                        raw = region.get("raw_content", "")
                        if raw and len(raw.strip()) > 3 and len(raw.strip()) < 100:
                            # Check if it looks like a title (not too long, has some structure)
                            cleaned = clean_display_text(raw, "identity")
                            if cleaned and cleaned != "Untitled":
                                title = cleaned
                                break
    
    # Final fallback
    if not title or title == "Untitled":
        title = "Untitled"
    
    # Extract subtitle/tagline
    subtitle = get_region_content(layout_slots.get("tagline_slot"), "tagline")
    
    # Extract value/description with fallback
    description = get_region_content(layout_slots.get("value_slot"), "value_prop")
    
    # Fallback: If no description, try to find value_prop purpose in included regions
    if not description:
        for region_id, include_flag in included.items():
            if include_flag and region_id in region_map:
                region = region_map[region_id]
                if region.get("purpose") == "value_prop":
                    description = get_region_content(region_id, "value_prop")
                    if description:
                        break
    
    # Extract tags
    tags = []
    for tag_id in layout_slots.get("tags_slots", [])[:4]:
        tag_text = get_region_content(tag_id)
        if tag_text:
            tags.append(tag_text)
    
    # Extract context items
    context_items = []
    for ctx_id in layout_slots.get("context_slots", [])[:2]:
        if ctx_id in region_map:
            region = region_map[ctx_id]
            ctx_type = region.get("content_type", "other")
            ctx_text = get_region_content(ctx_id)
            if ctx_text:
                icon = "location" if "location" in ctx_type.lower() else "info"
                context_items.append({"icon": icon, "text": ctx_text})
    
    # IMPROVEMENT: Extract benefits (2-3 key benefits/features)
    benefits = []
    for benefit_id in layout_slots.get("benefits_slots", [])[:3]:
        benefit_text = get_region_content(benefit_id, "benefits")
        if benefit_text:
            benefits.append(benefit_text)
    
    # If no explicit benefits slots, try to extract from value_prop or secondary regions
    if not benefits:
        # Look for regions with purpose="benefits" or secondary value_prop regions
        for region_id, include_flag in included.items():
            if include_flag and region_id in region_map:
                region = region_map[region_id]
                if region.get("purpose") == "benefits" and len(benefits) < 3:
                    benefit_text = get_region_content(region_id, "benefits")
                    if benefit_text and benefit_text not in benefits:
                        benefits.append(benefit_text)
    
    # IMPROVEMENT: Extract more credibility items (up to 3 for rich trust signals)
    credibility_items = []
    for cred_id in layout_slots.get("credibility_slots", [])[:3]:
        if cred_id in region_map:
            region = region_map[cred_id]
            cred_type = region.get("content_type", "other")
            cred_text = get_region_content(cred_id)
            # Include all credibility items if they were selected by AI (even zero ratings)
            if cred_text:
                credibility_items.append({"type": cred_type, "value": cred_text})
    
    # IMPROVEMENT: If description is thin, try to enrich it with first benefit
    if description and len(description) < 50 and benefits:
        # Append first benefit to description for richer content
        description = f"{description} {benefits[0]}"
    
    # Extract CTA
    cta_text = get_region_content(layout_slots.get("action_slot"))
    
    # IMPROVEMENT: Extract primary image, prioritizing logo if detected
    primary_image = get_region_image(layout_slots.get("identity_image_slot"))
    
    # If no primary image but we have logo detection, try to find it
    if not primary_image:
        # Look for regions marked as logo
        for region in regions:
            if region.get("is_logo") and region.get("image_data"):
                primary_image = region.get("image_data")
                logger.info("Using detected logo as primary image")
                break
    
    return {
        "title": title,
        "subtitle": subtitle,
        "description": description,
        "tags": tags,
        "benefits": benefits,  # NEW: Extracted benefits
        "context_items": context_items,
        "credibility_items": credibility_items,
        "cta_text": cta_text,
        "primary_image_base64": primary_image
    }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def generate_reasoned_preview(screenshot_bytes: bytes, url: str = "") -> ReasonedPreview:
    """
    Main entry point for multi-stage reasoned preview generation.
    
    This function orchestrates all 6 stages of the reasoning framework:
    1. Segmentation
    2. Purpose Analysis
    3. Priority Assignment
    4. Composition Decision
    5. Layout Synthesis
    6. Coherence Check
    
    Args:
        screenshot_bytes: Raw PNG screenshot
        url: URL for context
        
    Returns:
        ReasonedPreview with full reasoning chain
    """
    start_time = time.time()
    
    logger.info("Starting multi-stage preview reasoning")
    
    # Stages 1-3: Analysis
    logger.info("Running Stages 1-3: Segmentation, Purpose, Priority")
    regions, palette, page_type, confidence = run_stages_1_2_3(screenshot_bytes)
    logger.info(f"Identified {len(regions)} regions, page_type={page_type}")
    
    # Stages 4-5: Layout
    logger.info("Running Stages 4-5: Composition, Layout")
    layout_result = run_stages_4_5(regions, page_type, palette)
    
    # Get included regions for Stage 6
    composition_decisions = layout_result.get("composition_decisions", [])
    included_ids = {d["region_id"] for d in composition_decisions if d.get("include")}
    included_regions = [r for r in regions if r["id"] in included_ids]
    
    # Stage 6: Quality Check
    logger.info("Running Stage 6: Coherence Check")
    quality = run_stage_6(layout_result, included_regions)
    
    # Extract final content
    final_content = extract_final_content(regions, layout_result, composition_decisions)
    
    # Build analyzed regions
    analyzed_regions = []
    for r in regions:
        try:
            decision = next((d for d in composition_decisions if d["region_id"] == r["id"]), None)
            
            analyzed_regions.append(AnalyzedRegion(
                id=r["id"],
                content_type=r.get("content_type", "other"),
                raw_content=r.get("raw_content", ""),
                purpose=RegionPurpose(r.get("purpose", "decoration")),
                purpose_reasoning=r.get("purpose_reasoning", ""),
                visual_weight=VisualWeight(r.get("visual_weight", "omit")),
                priority_score=r.get("priority_score", 0.0),
                priority_reasoning=r.get("priority_reasoning", ""),
                include_in_preview=decision.get("include", False) if decision else False,
                decision_reasoning=decision.get("decision_reasoning", "") if decision else "",
                display_text=clean_display_text(r.get("raw_content", ""), r.get("purpose", "")),
                image_data=r.get("image_data"),
                bbox=r.get("bbox")
            ))
        except (ValueError, KeyError) as e:
            logger.warning(f"Error building analyzed region: {e}")
    
    # Build layout blueprint
    layout_data = layout_result.get("layout", {})
    blueprint = LayoutBlueprint(
        template_type=layout_data.get("template_type", page_type),
        primary_color=palette.get("primary", "#3B82F6"),
        secondary_color=palette.get("secondary", "#1E293B"),
        accent_color=palette.get("accent", "#F59E0B"),
        identity_slot=layout_data.get("identity_slot"),
        identity_image_slot=layout_data.get("identity_image_slot"),
        tagline_slot=layout_data.get("tagline_slot"),
        value_slot=layout_data.get("value_slot"),
        context_slots=layout_data.get("context_slots", []),
        credibility_slots=layout_data.get("credibility_slots", []),
        action_slot=layout_data.get("action_slot"),
        tags_slots=layout_data.get("tags_slots", []),
        layout_reasoning=layout_result.get("layout_reasoning", ""),
        composition_notes=layout_result.get("composition_notes", ""),
        coherence_score=quality.get("coherence_score", 0.7),
        balance_score=quality.get("balance_score", 0.7),
        clarity_score=quality.get("clarity_score", 0.7),
        overall_quality=quality.get("overall_quality", "good")
    )
    
    processing_time = int((time.time() - start_time) * 1000)
    
    # IMPROVEMENT: Enrich description with benefits if available
    description = final_content.get("description", "")
    benefits = final_content.get("benefits", [])
    if benefits and description:
        # If description is short, append first benefit
        if len(description) < 100 and len(benefits) > 0:
            description = f"{description} {benefits[0]}"
    
    result = ReasonedPreview(
        regions=analyzed_regions,
        blueprint=blueprint,
        title=final_content["title"],
        subtitle=final_content["subtitle"],
        description=description,  # Use enriched description
        tags=final_content["tags"],
        context_items=final_content["context_items"],
        credibility_items=final_content["credibility_items"],
        cta_text=final_content["cta_text"],
        primary_image_base64=final_content["primary_image_base64"],
        processing_time_ms=processing_time,
        reasoning_confidence=confidence
    )
    
    logger.info(f"Preview reasoning complete: quality={blueprint.overall_quality}, time={processing_time}ms")
    
    return result

