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

STAGE_1_2_3_PROMPT = """You are an elite marketing strategist and UI/UX analyst creating PREMIUM social media previews.

Your goal: Create a preview that makes people STOP SCROLLING and CLICK. Think like a conversion expert.

TASK: Analyze this webpage screenshot to extract the most COMPELLING content for a social media preview card.

=== STAGE 1: CONTENT DISCOVERY ===
Find the BEST content for a high-converting preview. Scan the entire page for:

MUST-FIND ELEMENTS (in order of importance):
1. **HEADLINE** - The single most compelling statement. Look for:
   - Main H1 or hero text (exact wording)
   - Value proposition that answers "Why should I care?"
   - Should be punchy, benefit-focused, under 60 characters ideally

2. **VISUAL ANCHOR** - The most eye-catching visual:
   - Product shot, hero image, or featured graphic
   - Logo/brand mark (for brand recognition)
   - Person/team photo (for personal brands/services)

3. **PROOF/CREDIBILITY** - What makes this trustworthy:
   - Star ratings (e.g., "4.9★ from 2,847 reviews")
   - User counts (e.g., "50,000+ users", "Trusted by 500 companies")
   - Press logos or "As seen in" badges
   - Certifications, awards, security badges
   - Testimonial quotes with attribution

4. **KEY BENEFITS** - 2-3 bullet points that sell:
   - Feature highlights that solve problems
   - Unique differentiators ("Only platform that...")
   - Time/money savings ("Save 10 hours/week")

5. **CALL-TO-ACTION** - What they want users to do:
   - Primary button text (exact wording)
   - Action-oriented, creates urgency

=== STAGE 2: MARKETING ANALYSIS ===
For each element found, assess its MARKETING VALUE:
- identity: Brand name/logo - instant recognition
- hook: The attention-grabber, the "wow" factor
- value_prop: Core promise - what problem does this solve?
- proof: Social proof, trust signals, credibility builders
- benefits: Specific advantages users get
- action: CTA that drives clicks
- filler: Nice-to-have but not essential (often omit)

Ask: "Would this make someone click?" If not, mark as lower priority.

=== STAGE 3: PRIORITY FOR PREVIEW ===
A great preview shows ONLY what matters in 3 seconds. Assign:
- hero: ONE dominant element (headline OR visual - not both fighting for attention)
- primary: 1-2 supporting elements (proof, key benefit)
- secondary: 1-2 extras if space allows (additional proof, minor context)
- omit: Everything else (navigation, footers, repetitive content, decorative elements)

MARKETING RULE: Less is more. A preview with 3 strong elements beats one with 7 weak ones.

OUTPUT JSON:
{{
    "page_type": "<saas|ecommerce|agency|portfolio|blog|startup|enterprise|personal|unknown>",
    "marketing_angle": "<what's the main selling point in one sentence>",
    "regions": [
        {{
            "id": "<unique_id>",
            "content_type": "<headline|subheadline|hero_image|logo|rating|user_count|testimonial|benefit|cta|badge|statistic|other>",
            "raw_content": "<EXACT text, no paraphrasing>",
            "bbox": {{"x": <0-1>, "y": <0-1>, "width": <0-1>, "height": <0-1>}},
            "purpose": "<identity|hook|value_prop|proof|benefits|action|filler>",
            "marketing_value": "<high|medium|low>",
            "purpose_reasoning": "<why this matters for conversion>",
            "visual_weight": "<hero|primary|secondary|omit>",
            "priority_score": <0.0-1.0>,
            "is_logo": <true|false>
        }}
    ],
    "detected_palette": {{
        "primary": "<hex from brand/buttons>",
        "secondary": "<hex from backgrounds>",
        "accent": "<hex from CTAs/highlights>"
    }},
    "detected_logo": {{
        "region_id": "<id or null>",
        "confidence": <0.0-1.0>
    }},
    "analysis_confidence": <0.0-1.0>,
    "preview_strategy": "<brief note on how to compose the preview for maximum impact>"
}}

CRITICAL:
- Extract EXACT text (users will read it!)
- Prioritize SPECIFIC numbers over vague claims ("10,000+ users" > "Many customers")
- Headlines should be compelling, not just descriptive
- If you find a great testimonial quote, include it!
- Bounding boxes must be precise for image cropping"""


STAGE_4_5_PROMPT = """You are a conversion-focused designer creating a preview that DRIVES CLICKS.

ANALYZED CONTENT:
{regions_json}

PAGE TYPE: {page_type}
BRAND COLORS: Primary={primary}, Secondary={secondary}, Accent={accent}

=== STAGE 4: CONTENT SELECTION ===
Select ONLY what creates desire to click. Ask: "Does this make someone want to learn more?"

INCLUDE (high-value for conversion):
✓ Compelling headline that creates curiosity
✓ ONE strong visual (product, hero, or logo)
✓ Social proof with NUMBERS (ratings, user counts, testimonials)
✓ 1-2 key benefits that solve real problems
✓ CTA text that indicates the action

EXCLUDE (no conversion value):
✗ Navigation menus, footers
✗ Generic descriptions without specific value
✗ Multiple similar images
✗ Vague claims without proof
✗ Internal links and secondary CTAs

=== STAGE 5: PREVIEW LAYOUT ===
Create a layout that SELLS. Order matters - most important first:

PRIMARY ZONE (always visible):
- headline_slot: The hook - most compelling statement (SHORT and punchy)
- visual_slot: One strong image (logo OR hero, not both)

PROOF ZONE (builds trust):
- proof_slot: Best social proof element ("4.9★ • 10k+ users")
- benefit_slot: Single strongest benefit or differentiator

OPTIONAL (only if exceptional):
- secondary_benefit_slot: Another strong selling point
- cta_slot: Action text if compelling

OUTPUT JSON:
{{
    "composition_decisions": [
        {{
            "region_id": "<id>",
            "include": <true|false>,
            "conversion_value": "<high|medium|low>",
            "decision_reasoning": "<why this helps/hurts conversion>"
        }}
    ],
    "layout": {{
        "template_style": "<bold|minimal|professional|vibrant>",
        "headline_slot": "<region_id - the main hook>",
        "visual_slot": "<region_id - primary visual>",
        "proof_slot": "<region_id - best social proof>",
        "benefit_slot": "<region_id - key benefit>",
        "secondary_benefit_slot": "<region_id or null>",
        "cta_slot": "<region_id or null>"
    }},
    "layout_reasoning": "<explain the conversion strategy>",
    "visual_balance": "<text-heavy|visual-heavy|balanced>",
    "energy_level": "<calm|confident|energetic|urgent>"
}}

DESIGN PHILOSOPHY:
1. LESS IS MORE - 3-4 elements max
2. HIERARCHY MATTERS - Most important = most prominent
3. PROOF CONVERTS - Always include social proof if available
4. SPECIFICITY WINS - "4.9★ from 2,847 reviews" > "Great reviews"
5. ACTION ORIENTED - Preview should hint at what clicking does"""


STAGE_6_PROMPT = """Rate this preview's CONVERSION POTENTIAL.

LAYOUT:
{layout_json}

CONTENT:
{included_regions}

=== CONVERSION QUALITY CHECK ===

1. HOOK POWER (0-1): Does the headline make people STOP scrolling?
   - Is it specific, not generic?
   - Does it create curiosity or promise value?
   - Would YOU click based on this headline alone?

2. TRUST FACTOR (0-1): Does it feel credible?
   - Is there proof (numbers, ratings, testimonials)?
   - Does it look professional, not spammy?
   - Would a skeptical user give it a chance?

3. CLARITY (0-1): Can someone understand it in 2 seconds?
   - Is the main offer/value immediately obvious?
   - Is there too much text or too little?
   - Is the visual hierarchy clear?

4. CLICK MOTIVATION (0-1): Does it create desire to click?
   - Is there a clear benefit to clicking?
   - Does it leave something to discover (curiosity gap)?
   - Is the CTA clear if present?

OUTPUT JSON:
{{
    "hook_score": <0.0-1.0>,
    "hook_notes": "<what makes it strong/weak>",
    "trust_score": <0.0-1.0>,
    "trust_notes": "<credibility assessment>",
    "clarity_score": <0.0-1.0>,
    "clarity_notes": "<readability assessment>",
    "click_motivation_score": <0.0-1.0>,
    "click_notes": "<why would/wouldn't someone click>",
    "overall_quality": "<excellent|good|fair|poor>",
    "improvement_suggestions": ["<actionable improvement>"]
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
    
    # 7X QUALITY: Enhanced system prompt and parameters
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an elite UI/UX expert performing systematic visual analysis with exceptional precision. Your analysis must be thorough, accurate, and context-aware. Extract exact content, provide genuine reasoning, and identify all meaningful elements. Output valid JSON only."
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
        max_tokens=4000,  # 7X: Increased for more detailed analysis
        temperature=0.1  # 7X: Lower temperature for more consistent, precise results
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
        Layout plan dictionary with normalized slot names for backward compatibility.
    """
    # Filter to non-omit regions for composition decisions
    relevant_regions = [r for r in regions if r.get("visual_weight") != "omit"]
    
    # OPTIMIZATION: Remove image_data from regions to reduce token usage
    regions_for_ai = []
    for r in relevant_regions:
        region_copy = {k: v for k, v in r.items() if k != "image_data"}
        if r.get("image_data"):
            region_copy["has_image"] = True
        regions_for_ai.append(region_copy)
    
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=45)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a conversion-focused designer. Create layouts that DRIVE CLICKS. Be decisive - include only high-value content. Output valid JSON only."
            },
            {
                "role": "user",
                "content": STAGE_4_5_PROMPT.format(
                    regions_json=json.dumps(regions_for_ai, indent=2),
                    page_type=page_type,
                    primary=palette.get("primary", "#3B82F6"),
                    secondary=palette.get("secondary", "#1E293B"),
                    accent=palette.get("accent", "#F59E0B")
                )
            }
        ],
        max_tokens=2000,
        temperature=0.15  # Low temperature for consistent, decisive layouts
    )
    
    content = response.choices[0].message.content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    result = json.loads(content)
    
    # Normalize new-style layout to include old-style slots for backward compatibility
    layout = result.get("layout", {})
    
    # Map new slots to old slots if they exist
    if "headline_slot" in layout and "identity_slot" not in layout:
        layout["identity_slot"] = layout["headline_slot"]
    if "visual_slot" in layout and "identity_image_slot" not in layout:
        layout["identity_image_slot"] = layout["visual_slot"]
    if "benefit_slot" in layout and "value_slot" not in layout:
        layout["value_slot"] = layout["benefit_slot"]
    if "cta_slot" in layout and "action_slot" not in layout:
        layout["action_slot"] = layout["cta_slot"]
    if "proof_slot" in layout:
        if "credibility_slots" not in layout:
            layout["credibility_slots"] = [layout["proof_slot"]]
        elif layout["proof_slot"] not in layout["credibility_slots"]:
            layout["credibility_slots"].insert(0, layout["proof_slot"])
    
    # Ensure required fields exist
    layout.setdefault("template_type", layout.get("template_style", page_type))
    layout.setdefault("context_slots", [])
    layout.setdefault("tags_slots", [])
    layout.setdefault("credibility_slots", [])
    layout.setdefault("benefits_slots", [])
    
    # Add secondary benefit to benefits if present
    if layout.get("secondary_benefit_slot"):
        if layout["secondary_benefit_slot"] not in layout["benefits_slots"]:
            layout["benefits_slots"].append(layout["secondary_benefit_slot"])
    
    result["layout"] = layout
    return result


def run_stage_6(layout: Dict[str, Any], included_regions: List[Dict]) -> Dict[str, Any]:
    """
    Run Stage 6: Conversion Quality Check.
    
    Returns:
        Quality scores dictionary with normalized field names.
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a conversion expert. Rate this preview's ability to drive clicks. Be critical but fair. Output valid JSON only."
            },
            {
                "role": "user",
                "content": STAGE_6_PROMPT.format(
                    layout_json=json.dumps(layout, indent=2),
                    included_regions=json.dumps(included_regions, indent=2)
                )
            }
        ],
        max_tokens=600,
        temperature=0.1
    )
    
    content = response.choices[0].message.content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    result = json.loads(content)
    
    # Normalize new-style scores to old-style for backward compatibility
    if "hook_score" in result and "coherence_score" not in result:
        result["coherence_score"] = result["hook_score"]
    if "trust_score" in result and "balance_score" not in result:
        result["balance_score"] = result["trust_score"]
    if "click_motivation_score" in result:
        # Use click motivation as a factor in overall quality
        click_score = result["click_motivation_score"]
        if click_score >= 0.8:
            result["overall_quality"] = "excellent"
        elif click_score >= 0.6:
            result["overall_quality"] = "good"
        elif click_score >= 0.4:
            result["overall_quality"] = "fair"
        else:
            result["overall_quality"] = "poor"
    
    # Ensure required fields exist
    result.setdefault("coherence_score", 0.7)
    result.setdefault("balance_score", 0.7)
    result.setdefault("clarity_score", 0.7)
    result.setdefault("overall_quality", "good")
    result.setdefault("improvement_suggestions", [])
    
    return result


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
    
    Works with both old-style (identity_slot, tagline_slot, etc.) and 
    new-style (headline_slot, visual_slot, proof_slot) layouts.
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
    
    # === TITLE EXTRACTION (with fallbacks) ===
    # Try new-style first, then old-style
    title = get_region_content(layout_slots.get("headline_slot"), "hook")
    if not title:
        title = get_region_content(layout_slots.get("identity_slot"), "identity")
    if not title:
        title = get_region_content(layout_slots.get("tagline_slot"), "tagline")
    
    # Fallback: Search included regions for best title candidate
    if not title or title == "Untitled":
        for region_id, include_flag in included.items():
            if include_flag and region_id in region_map:
                region = region_map[region_id]
                # Look for hook, identity, or headline content types
                if region.get("purpose") in ["hook", "identity", "value_prop"]:
                    candidate = get_region_content(region_id, region.get("purpose", ""))
                    if candidate and len(candidate) > 3 and len(candidate) < 120:
                        title = candidate
                        break
                if region.get("content_type") == "headline":
                    candidate = get_region_content(region_id, "headline")
                    if candidate and len(candidate) > 3 and len(candidate) < 120:
                        title = candidate
                        break
    
    # Last resort: find any high-priority text
    if not title or title == "Untitled":
        for region in sorted(regions, key=lambda r: r.get("priority_score", 0), reverse=True):
            if included.get(region["id"], False):
                raw = region.get("raw_content", "")
                if raw and 5 < len(raw.strip()) < 100:
                    title = clean_display_text(raw, "identity")
                    if title and title != "Untitled":
                        break
    
    if not title or title == "Untitled":
        title = "Untitled"
    
    # === SUBTITLE/PROOF EXTRACTION ===
    # Try new proof_slot first (for social proof), then fallback to tagline
    subtitle = get_region_content(layout_slots.get("proof_slot"), "proof")
    if not subtitle:
        subtitle = get_region_content(layout_slots.get("tagline_slot"), "tagline")
    
    # If proof slot had content, also check for dedicated subtitle
    proof_text = get_region_content(layout_slots.get("proof_slot"), "proof")
    
    # === DESCRIPTION/BENEFIT EXTRACTION ===
    description = get_region_content(layout_slots.get("benefit_slot"), "benefits")
    if not description:
        description = get_region_content(layout_slots.get("value_slot"), "value_prop")
    
    # Try secondary benefit as additional description
    secondary_benefit = get_region_content(layout_slots.get("secondary_benefit_slot"), "benefits")
    
    # Fallback: search for value_prop in included regions
    if not description:
        for region_id, include_flag in included.items():
            if include_flag and region_id in region_map:
                region = region_map[region_id]
                if region.get("purpose") in ["value_prop", "benefits"]:
                    description = get_region_content(region_id, region.get("purpose", ""))
                    if description:
                        break
    
    # === BENEFITS EXTRACTION ===
    benefits = []
    benefit_text = get_region_content(layout_slots.get("benefit_slot"), "benefits")
    if benefit_text:
        benefits.append(benefit_text)
    if secondary_benefit and secondary_benefit not in benefits:
        benefits.append(secondary_benefit)
    
    # Old-style benefits slots
    for benefit_id in layout_slots.get("benefits_slots", [])[:3]:
        benefit_text = get_region_content(benefit_id, "benefits")
        if benefit_text and benefit_text not in benefits:
            benefits.append(benefit_text)
    
    # === CREDIBILITY/PROOF EXTRACTION ===
    credibility_items = []
    
    # New-style: proof_slot
    if proof_text:
        credibility_items.append({"type": "proof", "value": proof_text})
    
    # Old-style: credibility_slots
    for cred_id in layout_slots.get("credibility_slots", [])[:3]:
        if cred_id in region_map:
            region = region_map[cred_id]
            cred_type = region.get("content_type", "other")
            cred_text = get_region_content(cred_id)
            if cred_text and cred_text not in [c["value"] for c in credibility_items]:
                credibility_items.append({"type": cred_type, "value": cred_text})
    
    # Search for proof/credibility in included regions
    if not credibility_items:
        for region_id, include_flag in included.items():
            if include_flag and region_id in region_map:
                region = region_map[region_id]
                if region.get("purpose") in ["proof", "credibility"]:
                    cred_text = get_region_content(region_id)
                    if cred_text:
                        credibility_items.append({
                            "type": region.get("content_type", "proof"),
                            "value": cred_text
                        })
                        if len(credibility_items) >= 2:
                            break
    
    # === TAGS EXTRACTION ===
    tags = []
    for tag_id in layout_slots.get("tags_slots", [])[:4]:
        tag_text = get_region_content(tag_id)
        if tag_text:
            tags.append(tag_text)
    
    # === CONTEXT EXTRACTION ===
    context_items = []
    for ctx_id in layout_slots.get("context_slots", [])[:2]:
        if ctx_id in region_map:
            region = region_map[ctx_id]
            ctx_type = region.get("content_type", "other")
            ctx_text = get_region_content(ctx_id)
            if ctx_text:
                icon = "location" if "location" in ctx_type.lower() else "info"
                context_items.append({"icon": icon, "text": ctx_text})
    
    # === CTA EXTRACTION ===
    cta_text = get_region_content(layout_slots.get("cta_slot"))
    if not cta_text:
        cta_text = get_region_content(layout_slots.get("action_slot"))
    
    # === PRIMARY IMAGE EXTRACTION ===
    # Try new visual_slot first, then old identity_image_slot
    primary_image = get_region_image(layout_slots.get("visual_slot"))
    if not primary_image:
        primary_image = get_region_image(layout_slots.get("identity_image_slot"))
    
    # Fallback: look for detected logo
    if not primary_image:
        for region in regions:
            if region.get("is_logo") and region.get("image_data"):
                primary_image = region.get("image_data")
                logger.info("Using detected logo as primary image")
                break
    
    # === ENRICH THIN CONTENT ===
    # If description is thin, enrich with benefit
    if description and len(description) < 60 and benefits:
        if benefits[0] not in description:
            description = f"{description} {benefits[0]}"
    
    # If subtitle is missing but we have proof, use that
    if not subtitle and credibility_items:
        subtitle = credibility_items[0]["value"]
    
    return {
        "title": title,
        "subtitle": subtitle,
        "description": description,
        "tags": tags,
        "benefits": benefits,
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

