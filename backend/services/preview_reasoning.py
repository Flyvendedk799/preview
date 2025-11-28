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

=== STAGE 2: PURPOSE ANALYSIS ===
For each region, determine its COMMUNICATION PURPOSE:
- identity: Who/what this is (name, logo, profile image)
- value_prop: Core message or what they offer
- context: Supporting info (location, date, company)
- credibility: Trust signals (ratings, reviews, certifications)
- action: CTAs and conversion elements
- navigation: Menu items, tabs (usually exclude from preview)
- decoration: Pure visual enhancement (usually exclude)

REASONING REQUIRED: Explain WHY each region has its assigned purpose.

=== STAGE 3: PRIORITY ASSIGNMENT ===
Assign visual weight based on what users should see FIRST in a preview:
- hero: ONE dominant element (usually the main image or headline)
- primary: 1-2 key supporting elements
- secondary: 2-4 supporting details
- tertiary: Minor details (use sparingly in previews)
- omit: Should not appear (navigation, redundant info, clutter)

REASONING REQUIRED: Explain the priority logic.

OUTPUT STRICT JSON:
{{
    "page_type": "<profile|product|landing|article|service|unknown>",
    "regions": [
        {{
            "id": "<unique_id>",
            "content_type": "<image|headline|subheadline|body_text|badge|button|rating|location|tag|logo|other>",
            "raw_content": "<exact content>",
            "bbox": {{"x": <0-1>, "y": <0-1>, "width": <0-1>, "height": <0-1>}},
            "purpose": "<identity|value_prop|context|credibility|action|navigation|decoration>",
            "purpose_reasoning": "<why this purpose>",
            "visual_weight": "<hero|primary|secondary|tertiary|omit>",
            "priority_score": <0.0-1.0>,
            "priority_reasoning": "<why this priority>"
        }}
    ],
    "detected_palette": {{
        "primary": "<hex>",
        "secondary": "<hex>", 
        "accent": "<hex>"
    }},
    "analysis_confidence": <0.0-1.0>
}}

CRITICAL RULES:
1. Extract EXACT text content - no paraphrasing
2. Be PRECISE with bounding boxes
3. Provide GENUINE reasoning, not templates
4. Identify ALL visible regions, then filter by weight
5. HERO weight should be assigned to only ONE element
6. Navigation elements should usually be weight=omit
7. Duplicate/redundant content should be weight=omit"""


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
8. Include credibility only if meaningful (skip 0 ratings)

=== STAGE 5: LAYOUT SYNTHESIS ===
Assign included regions to layout slots:
- identity_slot: Main name/title (clean, no prefix like "Om" or "About")
- identity_image_slot: Profile image/avatar/logo
- tagline_slot: Brief professional descriptor (role, specialty)
- value_slot: Core value proposition or about text
- context_slots: Location, date, company (max 2)
- credibility_slots: Ratings, testimonials (max 2, skip if zero/empty)
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
        "identity_image_slot": "<region_id or null>",
        "tagline_slot": "<region_id or null>",
        "value_slot": "<region_id or null>",
        "context_slots": ["<region_id>"],
        "credibility_slots": ["<region_id>"],
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


def crop_region(image: Image.Image, bbox: Dict[str, float]) -> str:
    """Crop a region from the image."""
    left = int(bbox['x'] * image.width)
    top = int(bbox['y'] * image.height)
    right = int((bbox['x'] + bbox['width']) * image.width)
    bottom = int((bbox['y'] + bbox['height']) * image.height)
    
    # Clamp to image bounds
    left = max(0, left)
    top = max(0, top)
    right = min(image.width, right)
    bottom = min(image.height, bottom)
    
    if right <= left or bottom <= top:
        return ""
    
    cropped = image.crop((left, top, right, bottom))
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
    
    # Crop images for included regions
    for region in data.get("regions", []):
        if region.get("content_type") == "image" and region.get("bbox"):
            region["image_data"] = crop_region(pil_image, region["bbox"])
    
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
    
    # Extract primary identity
    title = get_region_content(layout_slots.get("identity_slot"), "identity") or "Untitled"
    
    # Extract subtitle/tagline
    subtitle = get_region_content(layout_slots.get("tagline_slot"), "tagline")
    
    # Extract value/description
    description = get_region_content(layout_slots.get("value_slot"), "value_prop")
    
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
    
    # Extract credibility items
    credibility_items = []
    for cred_id in layout_slots.get("credibility_slots", [])[:2]:
        if cred_id in region_map:
            region = region_map[cred_id]
            cred_type = region.get("content_type", "other")
            cred_text = get_region_content(cred_id)
            # Skip zero ratings
            if cred_text and not (cred_text.startswith("0 ") or cred_text == "0"):
                credibility_items.append({"type": cred_type, "value": cred_text})
    
    # Extract CTA
    cta_text = get_region_content(layout_slots.get("action_slot"))
    
    # Extract primary image
    primary_image = get_region_image(layout_slots.get("identity_image_slot"))
    
    return {
        "title": title,
        "subtitle": subtitle,
        "description": description,
        "tags": tags,
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
    
    result = ReasonedPreview(
        regions=analyzed_regions,
        blueprint=blueprint,
        title=final_content["title"],
        subtitle=final_content["subtitle"],
        description=final_content["description"],
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

