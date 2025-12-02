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

STAGE_1_2_3_PROMPT = """You are a world-class conversion copywriter and UX expert analyzing a webpage to create the PERFECT social media preview.

MISSION: Extract content that makes this preview IRRESISTIBLE. Someone scrolling will see this for 1.5 seconds - make it count.

=== THE ONE RULE ===
Find THE SINGLE MOST COMPELLING THING about this page. Not everything - THE ONE THING.
Then find 2-3 supporting elements. That's it.

=== QUALITY STANDARDS ===
- Extract EXACT text (no paraphrasing, no "improvements")
- Prioritize SPECIFIC numbers over vague claims
- Focus on OUTCOMES and BENEFITS, not features
- Look for SOCIAL PROOF with concrete evidence
- Ignore generic marketing speak and filler content

=== WHAT TO FIND ===

1. **THE HOOK** (mandatory - the preview lives or dies by this)
   Look for the ONE statement that answers: "Why should I care?"
   - The main headline or hero text (EXACT wording, no changes)
   - A powerful stat or claim ("10x faster", "$2M saved", "50,000 users")
   - A compelling promise ("Never miss a deadline again")
   
   FOR PROFILE PAGES: The hook should be the PERSON'S NAME (e.g., "John Doe"), NOT their bio/description
   - Look for short text (2-4 words) that appears prominently (usually in title, h1, or dialog name)
   - Names are typically capitalized: "Celeste Hansen", "John Smith"
   - Avoid extracting long descriptions as names - names are concise
   
   BAD hooks: "Welcome to our website", "About Us", "Learn More", long bio descriptions
   GOOD hooks: "Ship 10x faster with AI", "The #1 rated CRM for startups", "Celeste Hansen" (for profiles)

2. **SOCIAL PROOF** (critical - makes people trust)
   Numbers and specifics ONLY. Find:
   - Star ratings with count: "4.9★ (2,847 reviews)" - INCLUDE THE NUMBER
   - User/customer counts: "Join 50,000+ teams" - EXACT NUMBER
   - Big names: "Used by Google, Stripe, Airbnb"
   - Awards/badges: "#1 Product Hunt", "Forbes 30 Under 30"
   
   If you see "★★★★★" extract it as "5★" or "4.9★"

3. **KEY BENEFIT** (one powerful benefit is better than three weak ones)
   Find the SPECIFIC value people get:
   - "Save 10 hours/week on reporting"
   - "Reduce costs by 40%"
   - "Get results in 24 hours, not 2 weeks"
   
   Avoid generic: "Powerful features", "Easy to use", "Great support"

4. **BRAND VISUAL** (logo or hero image for recognition)
   - Company logo (top-left, navigation, or footer)
   - Product screenshot or hero image
   - **Profile avatar/image** (circular images, profile photos, headshots - CRITICAL for profile pages)
   - Founder/team photo (for personal brands)
   
   FOR PROFILE PAGES: Prioritize circular/rounded profile images, avatars, headshots
   Look for images with classes like: avatar, profile, user, expert, person, headshot

=== WHAT TO IGNORE ===
- Navigation menus
- Footer content
- Cookie notices
- Generic stock photos
- Social media links
- Legal text
- "Sign up" without context

=== OUTPUT JSON ===
{{
    "page_type": "<saas|ecommerce|agency|portfolio|blog|startup|enterprise|marketplace|tool|landing|profile|unknown>",
    "the_hook": "<THE single most compelling statement on this page - exact text. FOR PROFILE PAGES: This should be the PERSON'S NAME (2-4 words), NOT their bio description>",
    "social_proof_found": "<best social proof with numbers, or null if none>",
    "key_benefit": "<most specific benefit found, or null>",
    "regions": [
        {{
            "id": "<unique_id>",
            "content_type": "<headline|subheadline|hero_image|logo|rating|user_count|testimonial|benefit|cta|statistic|badge|other>",
            "raw_content": "<EXACT text - preserve original wording>",
            "bbox": {{"x": <0-1>, "y": <0-1>, "width": <0-1>, "height": <0-1>}},
            "purpose": "<hook|proof|benefit|identity|action|filler>",
            "marketing_value": "<high|medium|low>",
            "why_it_matters": "<1 sentence on conversion value>",
            "visual_weight": "<hero|primary|secondary|omit>",
            "priority_score": <0.0-1.0>,
            "is_logo": <true|false>
        }}
    ],
    "detected_palette": {{
        "primary": "<hex - main brand color from logo/buttons>",
        "secondary": "<hex - background or secondary color>",
        "accent": "<hex - CTA button or highlight color>"
    }},
    "detected_logo": {{
        "region_id": "<id or null>",
        "confidence": <0.0-1.0>
    }},
    "analysis_confidence": <0.0-1.0>
}}

=== CRITICAL RULES ===
1. EXACT TEXT ONLY - No paraphrasing, no "improving" the copy, preserve original wording
2. NUMBERS WIN - "4.9★ from 2,847 reviews" beats "Great reviews" - Always include counts
3. SPECIFIC > GENERIC - "Save 10 hours/week" beats "Save time" - Quantify everything
4. ONE HERO ONLY - Don't mark multiple things as hero weight - Pick THE best
5. BBOX PRECISION - For logos and images, include padding for clean crops
6. CONTEXT MATTERS - Consider page type (product vs blog vs landing) when prioritizing
7. TRUST SIGNALS FIRST - Social proof, ratings, testimonials get highest priority
8. AVOID FILLER - Skip "Welcome", "About Us", navigation text, legal disclaimers"""


STAGE_4_5_PROMPT = """You're designing a preview that has 1.5 seconds to convince someone to click. Every element must earn its place.

EXTRACTED CONTENT:
{regions_json}

PAGE TYPE: {page_type}
COLORS: Primary={primary}, Secondary={secondary}, Accent={accent}

=== DECISION FRAMEWORK ===

For each region, ask: "Would removing this make the preview WORSE?"
- If YES → Include it
- If MAYBE → Probably exclude it
- If NO → Definitely exclude it

MUST INCLUDE (if available):
1. The HOOK (headline) - without this, nothing else matters
2. SOCIAL PROOF with numbers - this is what makes people trust and click
3. ONE visual element - logo for recognition OR hero for impact, not both

NICE TO HAVE:
4. One specific benefit - only if it adds real value
5. CTA text - only if it's compelling ("Start free trial" not "Submit")

ALWAYS EXCLUDE:
- Generic taglines ("Your trusted partner")
- Multiple headlines (pick ONE)
- Navigation and footers
- Vague benefits ("Easy to use", "Powerful")
- Anything you've seen on 100 other sites

=== LAYOUT DESIGN ===

The preview has THREE zones:
┌─────────────────────────────────────┐
│  HOOK (headline) - biggest, boldest │
│  The ONE thing people remember      │
├─────────────────────────────────────┤
│  PROOF - social proof with numbers  │
│  "4.9★ from 2,847 reviews"          │
├─────────────────────────────────────┤
│  BENEFIT/VISUAL - supporting value  │
│  Logo or one key benefit            │
└─────────────────────────────────────┘

OUTPUT JSON:
{{
    "composition_decisions": [
        {{
            "region_id": "<id>",
            "include": <true|false>,
            "slot_assignment": "<hook|proof|benefit|visual|none>",
            "decision_reasoning": "<why include/exclude - be specific>"
        }}
    ],
    "layout": {{
        "template_style": "<bold|professional|minimal|energetic>",
        "headline_slot": "<region_id for the main hook>",
        "visual_slot": "<region_id for logo/image, or null>",
        "proof_slot": "<region_id for social proof, or null>",
        "benefit_slot": "<region_id for key benefit, or null>",
        "cta_slot": "<region_id or null>"
    }},
    "layout_reasoning": "<2-3 sentences explaining the strategy>",
    "preview_strength": "<strong|moderate|weak> - honest assessment"
}}

GOLDEN RULES:
- 3 elements is better than 5 mediocre ones - Quality over quantity
- Numbers always beat vague claims - "50,000 users" > "Many users"
- Specificity wins - "Save 10 hours/week" > "Save time"
- Trust signals are non-negotiable - If there's proof, include it prominently
- Visual hierarchy matters - Biggest = most important
- Mobile-first thinking - Will this read well at small sizes?
- If there's no good social proof, don't fake it
- The hook must be SHORT (under 60 chars ideal) and SPECIFIC"""


STAGE_6_PROMPT = """Rate this preview honestly. Would YOU click on this? Be brutally honest.

LAYOUT:
{layout_json}

CONTENT:
{included_regions}

=== BRUTAL HONESTY CHECK ===

HOOK SCORE (0-1): How compelling is the main headline?
- 0.9-1.0: "I need to click this right now" - Specific, benefit-driven, creates urgency
- 0.7-0.8: "This looks interesting" - Clear value prop, somewhat specific
- 0.5-0.6: "It's okay, might click" - Generic but readable
- 0.3-0.4: "Meh, probably skip" - Vague, no clear benefit
- 0.0-0.2: "Generic/boring, definitely skip" - "Welcome", "About Us", filler text

TRUST SCORE (0-1): How trustworthy does this look?
- Has SPECIFIC numbers (reviews, users, stats)? +0.3
- Has recognizable proof (awards, logos, big names)? +0.3
- Looks professional, not spammy? +0.2
- Makes realistic, believable claims? +0.2
- If NO social proof at all, cap at 0.5

CLARITY SCORE (0-1): Can someone understand this instantly?
- Can understand the value in 2 seconds? +0.4
- One clear message, not multiple competing messages? +0.3
- Right amount of info (not overwhelming, not too sparse)? +0.3

CLICK MOTIVATION SCORE (0-1): What's the motivation to click?
- Clear, specific benefit to clicking? +0.4
- Creates curiosity gap or FOMO? +0.3
- Would someone share or remember this? +0.3

OUTPUT JSON:
{{
    "hook_score": <0.0-1.0>,
    "hook_notes": "<be specific - what works/doesn't>",
    "trust_score": <0.0-1.0>,
    "trust_notes": "<what proof exists or is missing>",
    "clarity_score": <0.0-1.0>,
    "clarity_notes": "<can someone get it instantly?>",
    "click_motivation_score": <0.0-1.0>,
    "click_notes": "<honest - would you click?>",
    "overall_quality": "<excellent|good|fair|poor>",
    "biggest_weakness": "<the ONE thing that would improve this most>",
    "improvement_suggestions": ["<specific, actionable fixes>"]
}}

BE HONEST: Most previews are "fair" or "good". Reserve "excellent" for previews you'd actually share."""


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
    Crop a region from the image with intelligent handling.
    
    For profile images, ensures a square, centered crop with smart padding
    and bias toward upper-center (where faces typically are).
    """
    # Calculate raw coordinates
    left = int(bbox['x'] * image.width)
    top = int(bbox['y'] * image.height)
    right = int((bbox['x'] + bbox['width']) * image.width)
    bottom = int((bbox['y'] + bbox['height']) * image.height)
    
    # Add generous padding for better coverage (25% for profile images, 15% for others)
    padding_factor = 0.25 if is_profile_image else 0.15
    padding_x = int((right - left) * padding_factor)
    padding_y = int((bottom - top) * padding_factor)
    
    left = max(0, left - padding_x)
    top = max(0, top - padding_y)
    right = min(image.width, right + padding_x)
    bottom = min(image.height, bottom + padding_y)
    
    if right <= left or bottom <= top:
        return ""
    
    # For profile images, ensure square crop with smart centering
    if is_profile_image:
        width = right - left
        height = bottom - top
        
        # Make it square by taking the larger dimension
        size = max(width, height)
        # Add 30% more to ensure we capture full circular avatar and some context
        size = int(size * 1.3)
        
        # Smart centering: bias toward upper-center for profile photos
        center_x = (left + right) // 2
        # For vertical centering, bias slightly upward (faces are usually in upper 2/3)
        center_y = top + int((bottom - top) * 0.35)  # 35% from top instead of 50%
        
        # Calculate new bounds
        half_size = size // 2
        left = max(0, center_x - half_size)
        top = max(0, center_y - half_size)
        right = min(image.width, center_x + half_size)
        bottom = min(image.height, center_y + half_size)
        
        # Re-adjust if we hit image bounds (maintain square, prefer keeping top)
        actual_width = right - left
        actual_height = bottom - top
        
        # If we lost size due to bounds, try to expand
        if actual_width < size or actual_height < size:
            # Try to expand horizontally first
            if right < image.width:
                right = min(image.width, left + size)
            elif left > 0:
                left = max(0, right - size)
            # Then vertically (but prefer keeping top position)
            if bottom < image.height:
                bottom = min(image.height, top + size)
            elif top > 0:
                # Only adjust top if we have room, otherwise keep it
                new_top = max(0, bottom - size)
                if new_top >= 0:
                    top = new_top
    
    if right <= left or bottom <= top:
        return ""
    
    cropped = image.crop((left, top, right, bottom))
    
    # For profile images, resize to high quality
    if is_profile_image and cropped.width > 0:
        # Use larger target size for better quality
        target_size = 400  # Increased from 256 for better quality
        cropped = cropped.resize((target_size, target_size), Image.Resampling.LANCZOS)
    
    buffer = BytesIO()
    # Use high quality for profile images
    quality = 95 if is_profile_image else 85
    cropped.save(buffer, format='PNG', optimize=True, quality=quality)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


# =============================================================================
# CORE REASONING ENGINE
# =============================================================================

def run_stages_1_2_3(screenshot_bytes: bytes) -> Tuple[List[Dict], Dict[str, str], str, float, Dict[str, Any]]:
    """
    Run Stages 1-3: Segmentation, Purpose Analysis, Priority Assignment.
    
    Returns:
        Tuple of (regions_list, color_palette, page_type, confidence, extracted_highlights)
    """
    image_base64, pil_image = prepare_image(screenshot_bytes)
    
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=60)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a conversion copywriter extracting the most compelling content from webpages. Be precise with text - extract EXACT wording. Prioritize SPECIFIC claims over generic ones. Numbers and social proof are gold. Output valid JSON only."
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
        max_tokens=3500,  # Optimized for faster responses while maintaining quality
        temperature=0.05  # Very low for consistent, precise extraction
    )
    
    content = response.choices[0].message.content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    # FIX 1: Robust JSON parsing with fallbacks
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parsing failed: {e}. Content preview: {content[:200]}...")
        # Try to extract JSON from content more aggressively
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                logger.info("✅ Recovered JSON using regex extraction")
            except:
                # Last resort: return minimal valid structure
                logger.warning("⚠️ Using fallback structure due to JSON parse failure")
                data = {
                    "page_type": "unknown",
                    "the_hook": None,
                    "social_proof_found": None,
                    "key_benefit": None,
                    "regions": [],
                    "detected_palette": {"primary": "#3B82F6", "secondary": "#1E293B", "accent": "#F59E0B"},
                    "detected_logo": {},
                    "analysis_confidence": 0.3
                }
        else:
            # No JSON found, use fallback
            logger.warning("⚠️ No JSON found in response, using fallback structure")
            data = {
                "page_type": "unknown",
                "the_hook": None,
                "social_proof_found": None,
                "key_benefit": None,
                "regions": [],
                "detected_palette": {"primary": "#3B82F6", "secondary": "#1E293B", "accent": "#F59E0B"},
                "detected_logo": {},
                "analysis_confidence": 0.3
            }
    
    # Extract highlights from the new prompt structure
    extracted_highlights = {
        "the_hook": data.get("the_hook"),
        "social_proof_found": data.get("social_proof_found"),
        "key_benefit": data.get("key_benefit")
    }
    
    logger.info(f"🎯 Extracted highlights: hook='{extracted_highlights.get('the_hook', 'none')[:50]}...', proof='{extracted_highlights.get('social_proof_found', 'none')}'")
    
    # Extract logo information if detected
    detected_logo = data.get("detected_logo", {})
    logo_region_id = detected_logo.get("region_id") if detected_logo else None
    
    # Crop images for included regions
    for region in data.get("regions", []):
        content_type = region.get("content_type", "").lower()
        if content_type in ["hero_image", "logo", "image", "profile_image", "avatar"] and region.get("bbox"):
            # Detect profile images more accurately
            is_profile = (
                region.get("purpose") == "identity" or
                content_type in ["profile_image", "avatar"] or
                "profile" in content_type or
                "avatar" in content_type
            )
            is_logo = region.get("is_logo", False) or region.get("id") == logo_region_id or content_type == "logo"
            
            try:
                image_data = crop_region(pil_image, region["bbox"], is_profile_image=(is_profile and not is_logo))
                if image_data:
                    region["image_data"] = image_data
                    if is_logo:
                        region["is_logo"] = True
                    if is_profile:
                        logger.info(f"✅ Cropped profile image from region {region.get('id')}")
            except Exception as e:
                logger.warning(f"Failed to crop region {region.get('id')}: {e}")
    
    return (
        data.get("regions", []),
        data.get("detected_palette", {"primary": "#3B82F6", "secondary": "#1E293B", "accent": "#F59E0B"}),
        data.get("page_type", "unknown"),
        data.get("analysis_confidence", 0.7),
        extracted_highlights
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
        max_tokens=1800,  # Optimized for faster responses
        temperature=0.1  # Lower temperature for more consistent, decisive layouts
    )
    
    content = response.choices[0].message.content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    # FIX 1: Robust JSON parsing with fallbacks
    try:
        result = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parsing failed in stage 4-5: {e}. Content preview: {content[:200]}...")
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                logger.info("✅ Recovered JSON using regex extraction")
            except:
                logger.warning("⚠️ Using fallback layout structure")
                result = {
                    "composition_decisions": [],
                    "layout": {
                        "template_style": page_type,
                        "headline_slot": None,
                        "visual_slot": None,
                        "proof_slot": None,
                        "benefit_slot": None,
                        "cta_slot": None
                    },
                    "layout_reasoning": "Fallback due to JSON parse error",
                    "preview_strength": "weak"
                }
        else:
            result = {
                "composition_decisions": [],
                "layout": {
                    "template_style": page_type,
                    "headline_slot": None,
                    "visual_slot": None,
                    "proof_slot": None,
                    "benefit_slot": None,
                    "cta_slot": None
                },
                "layout_reasoning": "Fallback due to JSON parse error",
                "preview_strength": "weak"
            }
    
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
        max_tokens=500,  # Reduced for faster responses
        temperature=0.05  # Lower temperature for more consistent, precise extraction
    )
    
    content = response.choices[0].message.content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    # FIX 1: Robust JSON parsing with fallbacks
    try:
        result = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parsing failed in stage 4-5: {e}. Content preview: {content[:200]}...")
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                logger.info("✅ Recovered JSON using regex extraction")
            except:
                logger.warning("⚠️ Using fallback layout structure")
                result = {
                    "composition_decisions": [],
                    "layout": {
                        "template_style": page_type,
                        "headline_slot": None,
                        "visual_slot": None,
                        "proof_slot": None,
                        "benefit_slot": None,
                        "cta_slot": None
                    },
                    "layout_reasoning": "Fallback due to JSON parse error",
                    "preview_strength": "weak"
                }
        else:
            result = {
                "composition_decisions": [],
                "layout": {
                    "template_style": page_type,
                    "headline_slot": None,
                    "visual_slot": None,
                    "proof_slot": None,
                    "benefit_slot": None,
                    "cta_slot": None
                },
                "layout_reasoning": "Fallback due to JSON parse error",
                "preview_strength": "weak"
            }
    
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
    Clean and validate display text.
    FIX 2: Content validation and sanitization.
    """
    if not raw_text or not isinstance(raw_text, str):
        return ""
    
    # Remove excessive whitespace
    cleaned = " ".join(raw_text.split())
    
    # Remove control characters but keep normal punctuation
    import re
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
    
    # Limit length based on purpose
    max_lengths = {
        "hook": 100,
        "identity": 80,
        "proof": 60,
        "benefits": 200,
        "description": 300,
        "tagline": 120
    }
    max_len = max_lengths.get(purpose, 200)
    
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rsplit(' ', 1)[0] + "..."
    
    # Validate minimum length
    if len(cleaned.strip()) < 3:
        return ""
    
    return cleaned.strip()
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
    composition_decisions: List[Dict],
    highlights: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Extract final content for rendering based on layout slots.
    
    Uses extracted highlights (the_hook, social_proof_found, key_benefit) 
    as primary sources, falling back to slot-based extraction.
    """
    # Build region lookup
    region_map = {r["id"]: r for r in regions}
    
    # Build inclusion map
    included = {d["region_id"]: d["include"] for d in composition_decisions}
    
    # Ensure highlights dict exists
    if highlights is None:
        highlights = {}
    
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
    
    # === TITLE EXTRACTION (prioritize based on page type) ===
    # For profile pages, prioritize identity/name over hook
    page_type = layout.get("page_type", "").lower() if isinstance(layout, dict) else ""
    is_profile = "profile" in page_type or any(r.get("content_type") == "profile_image" or r.get("content_type") == "avatar" for r in regions[:5])
    
    title = None
    
    if is_profile:
        # For profiles: Extract name from HTML metadata FIRST (most reliable)
        # This will be enhanced by preview_engine with HTML metadata
        # For now, look for short, name-like text in regions
        
        # PRIORITY 1: Look for short text that looks like a name (2-4 words, capitalized)
        # Names are typically: "First Last" or "First Middle Last"
        for region_id, include_flag in included.items():
            if include_flag and region_id in region_map:
                region = region_map[region_id]
                raw = region.get("raw_content", "").strip()
                
                # Check if this looks like a name (2-4 words, each capitalized, total < 50 chars)
                words = raw.split()
                if 2 <= len(words) <= 4 and len(raw) < 50:
                    # Check if most words start with capital letter (name pattern)
                    capitalized_words = sum(1 for w in words if w and w[0].isupper())
                    if capitalized_words >= len(words) * 0.75:  # At least 75% capitalized
                        # Avoid common non-name patterns
                        if not any(word.lower() in ["og", "and", "er", "is", "the", "med", "til"] for word in words):
                            title = raw
                            logger.info(f"📌 Using name-like region as profile name: '{title}'")
                            break
        
        # PRIORITY 2: Identity slot (person's name)
        if not title:
            title = get_region_content(layout_slots.get("identity_slot"), "identity")
            if title and len(title) < 80:  # Names are usually shorter
                logger.info(f"📌 Using identity slot as profile name: '{title}'")
        
        # PRIORITY 3: Look for identity-purpose regions
        if not title:
            for region_id, include_flag in included.items():
                if include_flag and region_id in region_map:
                    region = region_map[region_id]
                    if region.get("purpose") == "identity":
                        candidate = get_region_content(region_id, "identity")
                        # Filter out long descriptions - names are short
                        if candidate and 2 < len(candidate) < 60 and len(candidate.split()) <= 4:
                            title = candidate
                            logger.info(f"📌 Using identity region as profile name: '{title}'")
                            break
    
    # PRIORITY 2: Use the extracted "the_hook" (for non-profiles or fallback)
    if not title:
        title = highlights.get("the_hook")
        if title:
            title = clean_display_text(title, "hook")
            logger.info(f"📌 Using extracted hook as title: '{title[:50]}...'")
    
    # PRIORITY 3: Try slot-based extraction
    if not title or len(title) < 5:
        title = get_region_content(layout_slots.get("headline_slot"), "hook")
    if not title:
        title = get_region_content(layout_slots.get("identity_slot"), "identity")
    
    # PRIORITY 3: Search included regions for best title candidate
    if not title or title == "Untitled":
        for region_id, include_flag in included.items():
            if include_flag and region_id in region_map:
                region = region_map[region_id]
                if region.get("purpose") == "hook" or region.get("content_type") == "headline":
                    candidate = get_region_content(region_id, region.get("purpose", ""))
                    if candidate and 5 < len(candidate) < 120:
                        title = candidate
                        break
    
    # PRIORITY 4: High-priority text from any included region
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
    
    # === SUBTITLE/PROOF EXTRACTION (prioritize social proof) ===
    # PRIORITY 1: Use extracted social proof - this builds trust
    subtitle = highlights.get("social_proof_found")
    if subtitle:
        subtitle = clean_display_text(subtitle, "proof")
        logger.info(f"📌 Using extracted social proof as subtitle: '{subtitle}'")
    
    # PRIORITY 2: Try slot-based extraction
    if not subtitle:
        subtitle = get_region_content(layout_slots.get("proof_slot"), "proof")
    if not subtitle:
        subtitle = get_region_content(layout_slots.get("tagline_slot"), "tagline")
    
    # Track proof text separately for credibility_items
    proof_text = subtitle if subtitle else get_region_content(layout_slots.get("proof_slot"), "proof")
    
    # === DESCRIPTION/BENEFIT EXTRACTION (prioritize key benefit) ===
    # PRIORITY 1: Use extracted key benefit
    description = highlights.get("key_benefit")
    if description:
        description = clean_display_text(description, "benefit")
        logger.info(f"📌 Using extracted key benefit as description: '{description[:50]}...'")
    
    # PRIORITY 2: Try slot-based extraction
    if not description:
        description = get_region_content(layout_slots.get("benefit_slot"), "benefits")
    if not description:
        description = get_region_content(layout_slots.get("value_slot"), "value_prop")
    
    # Try secondary benefit as additional content
    secondary_benefit = get_region_content(layout_slots.get("secondary_benefit_slot"), "benefits")
    
    # PRIORITY 3: Search included regions for benefits
    if not description:
        for region_id, include_flag in included.items():
            if include_flag and region_id in region_map:
                region = region_map[region_id]
                if region.get("purpose") in ["benefit", "value_prop", "benefits"]:
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
    # For profile pages, prioritize profile images/avatars
    primary_image = None
    
    if is_profile:
        # PRIORITY 1: Look for profile_image or avatar content types
        for region in regions:
            if included.get(region.get("id"), False):
                content_type = region.get("content_type", "").lower()
                if content_type in ["profile_image", "avatar"] and region.get("image_data"):
                    primary_image = region.get("image_data")
                    logger.info("Using profile image/avatar as primary image")
                    break
        
        # PRIORITY 2: Visual slot (may contain profile image)
        if not primary_image:
            primary_image = get_region_image(layout_slots.get("visual_slot"))
    
    # PRIORITY 3: Try new visual_slot first, then old identity_image_slot
    if not primary_image:
        primary_image = get_region_image(layout_slots.get("visual_slot"))
    if not primary_image:
        primary_image = get_region_image(layout_slots.get("identity_image_slot"))
    
    # PRIORITY 4: Fallback: look for detected logo (but not for profiles - they need avatar)
    if not primary_image and not is_profile:
        for region in regions:
            if region.get("is_logo") and region.get("image_data"):
                primary_image = region.get("image_data")
                logger.info("Using detected logo as primary image")
                break
    
    # PRIORITY 5: For profiles, look for any image in included regions
    if not primary_image and is_profile:
        for region in regions:
            if included.get(region.get("id"), False) and region.get("image_data"):
                primary_image = region.get("image_data")
                logger.info("Using included region image as profile image")
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
    regions, palette, page_type, confidence, highlights = run_stages_1_2_3(screenshot_bytes)
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
    
    # Extract final content (pass highlights for prioritization)
    final_content = extract_final_content(regions, layout_result, composition_decisions, highlights)
    
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
    
    # Normalize page type to expected template types
    # Maps AI page types to frontend template types
    def normalize_template_type(page_type: str) -> str:
        pt = (page_type or "unknown").lower()
        
        # Profile: personal pages
        if pt in ["personal", "profile"]:
            return "profile"
        
        # Product: e-commerce
        if pt in ["product", "ecommerce", "marketplace", "shop"]:
            return "product"
        
        # Article: content pages
        if pt in ["article", "blog", "news", "documentation"]:
            return "article"
        
        # Service: agencies, portfolios
        if pt in ["service", "agency", "portfolio"]:
            return "service"
        
        # Landing: SaaS, startups, companies (DEFAULT for most business pages)
        # This should be the default for unknown types too
        if pt in ["landing", "saas", "startup", "enterprise", "tool", "company", "unknown"]:
            return "landing"
        
        # Fallback to landing (most versatile)
        return "landing"
    
    # Build layout blueprint
    layout_data = layout_result.get("layout", {})
    normalized_type = normalize_template_type(page_type)
    
    blueprint = LayoutBlueprint(
        template_type=normalized_type,
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

