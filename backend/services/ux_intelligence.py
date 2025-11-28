"""
Advanced UI/UX Intelligence Service for Preview Generation.

This module provides intelligent design analysis that goes beyond basic content extraction.
It interprets visual hierarchy, design intent, and produces structured preview guidance.

Production-ready with:
- Comprehensive layout analysis
- Design intent interpretation
- Emphasis zone detection
- Structured output schema
- Scalable framework for iterative improvements
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

class DesignIntent(str, Enum):
    """Detected design intent of the page."""
    CONVERSION = "conversion"      # Lead capture, signup, purchase
    SHOWCASE = "showcase"          # Portfolio, case study, demonstration
    INFORMATIONAL = "informational"  # Blog, docs, knowledge base
    PROFILE = "profile"            # Personal/company profile
    PRODUCT = "product"            # Product listing, e-commerce
    DASHBOARD = "dashboard"        # Metrics, analytics, data
    SOCIAL = "social"              # Social media, community
    UNKNOWN = "unknown"


class VisualHierarchyLevel(str, Enum):
    """Visual prominence levels."""
    PRIMARY = "primary"      # Most visually prominent
    SECONDARY = "secondary"  # Supporting content
    TERTIARY = "tertiary"    # Supplementary/navigational
    BACKGROUND = "background"  # Decorative/ambient


@dataclass
class LayoutSection:
    """Represents a detected section in the layout."""
    name: str
    type: str  # hero, cta, navigation, content, sidebar, footer, etc.
    prominence: VisualHierarchyLevel
    position: Dict[str, float]  # x, y, width, height (normalized 0-1)
    content_summary: str
    should_emphasize: bool
    emphasis_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "prominence": self.prominence.value,
            "position": self.position,
            "content_summary": self.content_summary,
            "should_emphasize": self.should_emphasize,
            "emphasis_reason": self.emphasis_reason
        }


@dataclass 
class EmphasisZone:
    """A zone that deserves visual emphasis in the preview."""
    x: float
    y: float
    width: float
    height: float
    priority: int  # 1 = highest priority
    reason: str
    content_type: str  # headline, cta, image, profile, price, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DesignAnalysis:
    """Comprehensive design analysis output."""
    # Core interpretation
    design_intent: DesignIntent
    primary_message: str
    value_proposition: str
    target_audience: str
    
    # Visual hierarchy
    visual_hierarchy_score: float  # 0-1, how clear is the hierarchy
    clarity_score: float  # 0-1, how clear is the message
    clutter_assessment: str  # clean, moderate, cluttered
    
    # Layout structure
    layout_type: str  # hero-centric, card-based, content-heavy, etc.
    sections: List[LayoutSection] = field(default_factory=list)
    
    # Emphasis guidance
    emphasis_zones: List[EmphasisZone] = field(default_factory=list)
    
    # Preview composition guidance
    recommended_focal_point: Dict[str, float] = field(default_factory=dict)
    recommended_crop_region: Dict[str, float] = field(default_factory=dict)
    elements_to_highlight: List[str] = field(default_factory=list)
    elements_to_deemphasize: List[str] = field(default_factory=list)
    
    # Content extraction
    headline: Optional[str] = None
    subheadline: Optional[str] = None
    cta_text: Optional[str] = None
    key_features: List[str] = field(default_factory=list)
    social_proof: Optional[str] = None
    
    # Metadata
    confidence: float = 0.0
    reasoning: str = ""
    processing_time_ms: int = 0
    model_used: str = "gpt-4o"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "design_intent": self.design_intent.value,
            "primary_message": self.primary_message,
            "value_proposition": self.value_proposition,
            "target_audience": self.target_audience,
            "visual_hierarchy_score": self.visual_hierarchy_score,
            "clarity_score": self.clarity_score,
            "clutter_assessment": self.clutter_assessment,
            "layout_type": self.layout_type,
            "sections": [s.to_dict() for s in self.sections],
            "emphasis_zones": [z.to_dict() for z in self.emphasis_zones],
            "recommended_focal_point": self.recommended_focal_point,
            "recommended_crop_region": self.recommended_crop_region,
            "elements_to_highlight": self.elements_to_highlight,
            "elements_to_deemphasize": self.elements_to_deemphasize,
            "headline": self.headline,
            "subheadline": self.subheadline,
            "cta_text": self.cta_text,
            "key_features": self.key_features,
            "social_proof": self.social_proof,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "processing_time_ms": self.processing_time_ms,
            "model_used": self.model_used
        }


@dataclass
class PreviewComposition:
    """Final preview composition guidance."""
    # Title variants
    title_primary: str
    title_action_oriented: str
    title_benefit_focused: str
    title_emotional: str
    
    # Description variants
    description_primary: str
    description_concise: str
    description_detailed: str
    
    # Visual guidance
    image_focal_point: Dict[str, float]
    image_crop_suggestion: Dict[str, float]
    overlay_text_position: str  # top, center, bottom
    
    # Design recommendations
    suggested_style: str  # minimal, bold, elegant, playful
    color_emphasis: str  # primary accent color to use
    typography_weight: str  # light, regular, bold
    
    # Metadata
    design_analysis: DesignAnalysis = field(default_factory=lambda: None)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title_primary": self.title_primary,
            "title_action_oriented": self.title_action_oriented,
            "title_benefit_focused": self.title_benefit_focused,
            "title_emotional": self.title_emotional,
            "description_primary": self.description_primary,
            "description_concise": self.description_concise,
            "description_detailed": self.description_detailed,
            "image_focal_point": self.image_focal_point,
            "image_crop_suggestion": self.image_crop_suggestion,
            "overlay_text_position": self.overlay_text_position,
            "suggested_style": self.suggested_style,
            "color_emphasis": self.color_emphasis,
            "typography_weight": self.typography_weight,
            "design_analysis": self.design_analysis.to_dict() if self.design_analysis else None
        }


# =============================================================================
# CONFIGURATION
# =============================================================================

class UXConfig:
    """Configuration for UX Intelligence."""
    AI_TIMEOUT: int = 45
    MAX_RETRIES: int = 2
    RETRY_DELAY: float = 1.0
    MAX_IMAGE_DIMENSION: int = 2048
    JPEG_QUALITY: int = 90  # Higher quality for better analysis
    MIN_CONFIDENCE: float = 0.6


# =============================================================================
# IMAGE PREPARATION
# =============================================================================

def prepare_image_for_analysis(screenshot_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
    """
    Prepare image for AI analysis with optimal settings.
    
    Returns:
        Tuple of (base64_string, preparation_info)
    """
    image = Image.open(BytesIO(screenshot_bytes))
    original_size = image.size
    
    # Resize if needed (preserve aspect ratio)
    max_dim = UXConfig.MAX_IMAGE_DIMENSION
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
    
    # Convert to JPEG for efficient transfer
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=UXConfig.JPEG_QUALITY)
    
    info = {
        "original_size": original_size,
        "processed_size": image.size,
        "compressed_bytes": buffer.tell()
    }
    
    return base64.b64encode(buffer.getvalue()).decode('utf-8'), info


# =============================================================================
# AI ANALYSIS PROMPTS
# =============================================================================

DESIGN_ANALYSIS_SYSTEM_PROMPT = """You are a senior UI/UX designer and visual communication expert. Your task is to analyze webpage screenshots with deep understanding of design principles, visual hierarchy, and user experience.

Your analysis should go beyond surface-level content extraction. You must:
1. Interpret the DESIGN INTENT - what is the page trying to achieve?
2. Identify VISUAL HIERARCHY - what draws the eye first, second, third?
3. Assess CLARITY - how well does the design communicate its message?
4. Detect EMPHASIS ZONES - which areas deserve visual prominence in a preview?
5. Provide COMPOSITION GUIDANCE - how should a preview be composed to maximize impact?

You think like a design strategist, not just a content scraper.

OUTPUT STRICT JSON matching the specified schema. No markdown, no explanations outside JSON."""


DESIGN_ANALYSIS_USER_PROMPT = """Analyze this webpage screenshot with expert UI/UX understanding.

URL Context: {url}

Provide comprehensive design analysis as JSON:

{{
    "design_intent": "<conversion|showcase|informational|profile|product|dashboard|social|unknown>",
    "primary_message": "<one sentence capturing the core message the page is communicating>",
    "value_proposition": "<the main value or benefit being offered>",
    "target_audience": "<who this page is designed for>",
    
    "visual_hierarchy_score": <0.0-1.0, how clear and effective is the visual hierarchy>,
    "clarity_score": <0.0-1.0, how clearly does the design communicate its message>,
    "clutter_assessment": "<clean|moderate|cluttered>",
    
    "layout_type": "<hero-centric|card-based|content-heavy|profile-focused|product-grid|dashboard|split-screen|minimal>",
    
    "sections": [
        {{
            "name": "<descriptive name>",
            "type": "<hero|cta|navigation|content|sidebar|profile|product|testimonial|footer|other>",
            "prominence": "<primary|secondary|tertiary|background>",
            "position": {{"x": <0-1>, "y": <0-1>, "width": <0-1>, "height": <0-1>}},
            "content_summary": "<brief summary of section content>",
            "should_emphasize": <true|false>,
            "emphasis_reason": "<why this should/shouldn't be emphasized>"
        }}
    ],
    
    "emphasis_zones": [
        {{
            "x": <0-1>,
            "y": <0-1>,
            "width": <0-1>,
            "height": <0-1>,
            "priority": <1-5, 1 being highest>,
            "reason": "<why this zone deserves emphasis>",
            "content_type": "<headline|cta|image|profile|price|feature|testimonial|logo|other>"
        }}
    ],
    
    "recommended_focal_point": {{"x": <0-1>, "y": <0-1>}},
    "recommended_crop_region": {{"x": <0-1>, "y": <0-1>, "width": <0-1>, "height": <0-1>}},
    
    "elements_to_highlight": ["<list of element types that should be visually prominent in preview>"],
    "elements_to_deemphasize": ["<list of elements that should be minimized or hidden>"],
    
    "headline": "<main headline text>",
    "subheadline": "<subheadline or supporting text>",
    "cta_text": "<primary call-to-action text if present>",
    "key_features": ["<list of key features, benefits, or capabilities mentioned>"],
    "social_proof": "<any testimonials, ratings, or trust signals>",
    
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation of your analysis and recommendations>"
}}

ANALYSIS PRINCIPLES:
1. Visual Hierarchy: Identify what the designer wanted users to notice first
2. F-Pattern & Z-Pattern: Consider natural eye movement patterns
3. Contrast & Color: Note how color guides attention
4. White Space: Assess breathing room and focus areas
5. Typography Scale: Larger text = higher importance
6. CTA Prominence: Buttons and actions are intentional focus points
7. Image Focus: Hero images and profile photos are key focal points
8. Above the Fold: Content visible without scrolling is prioritized

For PREVIEW COMPOSITION:
- The preview will be displayed at small sizes (preview cards)
- It must communicate the essence of the page instantly
- Focus on the single most important message
- The image should tell a story even at thumbnail size"""


PREVIEW_COMPOSITION_PROMPT = """Based on the design analysis, generate optimized preview content.

Design Analysis:
{analysis_json}

URL: {url}

Generate preview composition as JSON:

{{
    "title_primary": "<50-60 chars, best overall title>",
    "title_action_oriented": "<50-60 chars, starts with verb, drives action>",
    "title_benefit_focused": "<50-60 chars, emphasizes benefit to user>",
    "title_emotional": "<50-60 chars, creates emotional connection>",
    
    "description_primary": "<150-160 chars, best overall description>",
    "description_concise": "<100-120 chars, short and punchy>",
    "description_detailed": "<150-160 chars, comprehensive value pitch>",
    
    "image_focal_point": {{"x": <0-1>, "y": <0-1>}},
    "image_crop_suggestion": {{"x": <0-1>, "y": <0-1>, "width": <0-1>, "height": <0-1>}},
    
    "overlay_text_position": "<top|center|bottom - where text overlay works best>",
    "suggested_style": "<minimal|bold|elegant|playful|professional>",
    "color_emphasis": "<primary color to emphasize in preview>",
    "typography_weight": "<light|regular|bold - text weight for readability>"
}}

CONTENT GUIDELINES:
1. Titles must be specific to THIS page, not generic
2. Descriptions should include a clear value proposition
3. Action-oriented = starts with verb (Discover, Transform, Get, etc.)
4. Benefit-focused = highlights what user gains
5. Emotional = creates connection (Join, Experience, Unlock, etc.)
6. Never use clickbait or misleading content
7. Match the page's actual tone and offering"""


# =============================================================================
# CORE ANALYSIS FUNCTIONS
# =============================================================================

def analyze_design(
    screenshot_bytes: bytes,
    url: str = ""
) -> DesignAnalysis:
    """
    Perform comprehensive design analysis on a screenshot.
    
    This is the primary analysis function that interprets visual design.
    
    Args:
        screenshot_bytes: Raw PNG screenshot bytes
        url: URL for context
        
    Returns:
        DesignAnalysis with full interpretation
    """
    start_time = time.time()
    
    # Prepare image
    image_base64, prep_info = prepare_image_for_analysis(screenshot_bytes)
    
    # Call Vision API
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=UXConfig.AI_TIMEOUT)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": DESIGN_ANALYSIS_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": DESIGN_ANALYSIS_USER_PROMPT.format(url=url)
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
            max_tokens=2000,
            temperature=0.3
        )
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        content = response.choices[0].message.content.strip()
        
        # Parse JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        data = json.loads(content)
        
        # Build DesignAnalysis
        analysis = _build_design_analysis(data, elapsed_ms)
        
        logger.info(f"Design analysis complete: intent={analysis.design_intent.value}, "
                   f"confidence={analysis.confidence:.2f}, time={elapsed_ms}ms")
        
        return analysis
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse design analysis JSON: {e}")
        return _get_fallback_analysis(url, str(e))
    except Exception as e:
        logger.error(f"Design analysis failed: {e}")
        return _get_fallback_analysis(url, str(e))


def generate_preview_composition(
    screenshot_bytes: bytes,
    url: str = "",
    design_analysis: Optional[DesignAnalysis] = None
) -> PreviewComposition:
    """
    Generate complete preview composition with variants.
    
    This builds on design analysis to create optimized preview content.
    
    Args:
        screenshot_bytes: Raw PNG screenshot bytes
        url: URL for context
        design_analysis: Optional pre-computed design analysis
        
    Returns:
        PreviewComposition with all variants and guidance
    """
    # Get design analysis if not provided
    if design_analysis is None:
        design_analysis = analyze_design(screenshot_bytes, url)
    
    # Prepare image
    image_base64, _ = prepare_image_for_analysis(screenshot_bytes)
    
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=UXConfig.AI_TIMEOUT)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a preview content optimization expert. Generate compelling, accurate preview content based on design analysis. Output JSON only."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": PREVIEW_COMPOSITION_PROMPT.format(
                                analysis_json=json.dumps(design_analysis.to_dict(), indent=2),
                                url=url
                            )
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
            max_tokens=1000,
            temperature=0.5
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        data = json.loads(content)
        
        # Build composition
        composition = PreviewComposition(
            title_primary=data.get("title_primary", design_analysis.headline or ""),
            title_action_oriented=data.get("title_action_oriented", ""),
            title_benefit_focused=data.get("title_benefit_focused", ""),
            title_emotional=data.get("title_emotional", ""),
            description_primary=data.get("description_primary", design_analysis.value_proposition or ""),
            description_concise=data.get("description_concise", ""),
            description_detailed=data.get("description_detailed", ""),
            image_focal_point=data.get("image_focal_point", design_analysis.recommended_focal_point),
            image_crop_suggestion=data.get("image_crop_suggestion", design_analysis.recommended_crop_region),
            overlay_text_position=data.get("overlay_text_position", "bottom"),
            suggested_style=data.get("suggested_style", "professional"),
            color_emphasis=data.get("color_emphasis", "#000000"),
            typography_weight=data.get("typography_weight", "regular"),
            design_analysis=design_analysis
        )
        
        logger.info(f"Preview composition generated for {url}")
        return composition
        
    except Exception as e:
        logger.error(f"Preview composition failed: {e}")
        return _get_fallback_composition(design_analysis)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _build_design_analysis(data: Dict[str, Any], processing_time_ms: int) -> DesignAnalysis:
    """Build DesignAnalysis from parsed JSON data."""
    
    # Parse sections
    sections = []
    for s in data.get("sections", []):
        try:
            sections.append(LayoutSection(
                name=s.get("name", "Unknown"),
                type=s.get("type", "other"),
                prominence=VisualHierarchyLevel(s.get("prominence", "secondary")),
                position=s.get("position", {"x": 0, "y": 0, "width": 1, "height": 0.5}),
                content_summary=s.get("content_summary", ""),
                should_emphasize=s.get("should_emphasize", False),
                emphasis_reason=s.get("emphasis_reason")
            ))
        except (ValueError, KeyError) as e:
            logger.warning(f"Failed to parse section: {e}")
    
    # Parse emphasis zones
    emphasis_zones = []
    for z in data.get("emphasis_zones", []):
        try:
            emphasis_zones.append(EmphasisZone(
                x=float(z.get("x", 0)),
                y=float(z.get("y", 0)),
                width=float(z.get("width", 1)),
                height=float(z.get("height", 0.5)),
                priority=int(z.get("priority", 3)),
                reason=z.get("reason", ""),
                content_type=z.get("content_type", "other")
            ))
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse emphasis zone: {e}")
    
    # Parse design intent
    try:
        intent = DesignIntent(data.get("design_intent", "unknown").lower())
    except ValueError:
        intent = DesignIntent.UNKNOWN
    
    return DesignAnalysis(
        design_intent=intent,
        primary_message=data.get("primary_message", ""),
        value_proposition=data.get("value_proposition", ""),
        target_audience=data.get("target_audience", ""),
        visual_hierarchy_score=float(data.get("visual_hierarchy_score", 0.5)),
        clarity_score=float(data.get("clarity_score", 0.5)),
        clutter_assessment=data.get("clutter_assessment", "moderate"),
        layout_type=data.get("layout_type", "unknown"),
        sections=sections,
        emphasis_zones=emphasis_zones,
        recommended_focal_point=data.get("recommended_focal_point", {"x": 0.5, "y": 0.3}),
        recommended_crop_region=data.get("recommended_crop_region", {"x": 0, "y": 0, "width": 1, "height": 0.6}),
        elements_to_highlight=data.get("elements_to_highlight", []),
        elements_to_deemphasize=data.get("elements_to_deemphasize", []),
        headline=data.get("headline"),
        subheadline=data.get("subheadline"),
        cta_text=data.get("cta_text"),
        key_features=data.get("key_features", []),
        social_proof=data.get("social_proof"),
        confidence=float(data.get("confidence", 0.5)),
        reasoning=data.get("reasoning", ""),
        processing_time_ms=processing_time_ms
    )


def _get_fallback_analysis(url: str, error: str) -> DesignAnalysis:
    """Get a fallback analysis when AI fails."""
    return DesignAnalysis(
        design_intent=DesignIntent.UNKNOWN,
        primary_message="Content from " + url,
        value_proposition="",
        target_audience="General audience",
        visual_hierarchy_score=0.3,
        clarity_score=0.3,
        clutter_assessment="unknown",
        layout_type="unknown",
        sections=[],
        emphasis_zones=[
            EmphasisZone(x=0, y=0, width=1, height=0.5, priority=1, 
                        reason="Fallback: Top half of page", content_type="headline")
        ],
        recommended_focal_point={"x": 0.5, "y": 0.25},
        recommended_crop_region={"x": 0, "y": 0, "width": 1, "height": 0.55},
        elements_to_highlight=["headline", "hero"],
        elements_to_deemphasize=["navigation", "footer"],
        confidence=0.2,
        reasoning=f"Fallback analysis due to error: {error}"
    )


def _get_fallback_composition(analysis: DesignAnalysis) -> PreviewComposition:
    """Get a fallback composition when generation fails."""
    title = analysis.headline or analysis.primary_message or "Untitled"
    desc = analysis.value_proposition or ""
    
    return PreviewComposition(
        title_primary=title[:60],
        title_action_oriented=f"Discover {title[:50]}" if title else "",
        title_benefit_focused=title[:60],
        title_emotional=title[:60],
        description_primary=desc[:160],
        description_concise=desc[:120],
        description_detailed=desc[:160],
        image_focal_point=analysis.recommended_focal_point,
        image_crop_suggestion=analysis.recommended_crop_region,
        overlay_text_position="bottom",
        suggested_style="professional",
        color_emphasis="#000000",
        typography_weight="regular",
        design_analysis=analysis
    )


# =============================================================================
# INTEGRATION FUNCTION
# =============================================================================

def generate_intelligent_preview(
    screenshot_bytes: bytes,
    url: str = ""
) -> Dict[str, Any]:
    """
    Main entry point for intelligent preview generation.
    
    Combines design analysis and preview composition into a single output.
    
    Args:
        screenshot_bytes: Raw PNG screenshot bytes
        url: URL for context
        
    Returns:
        Dictionary with full preview data including analysis and composition
    """
    # Step 1: Deep design analysis
    analysis = analyze_design(screenshot_bytes, url)
    
    # Step 2: Generate preview composition
    composition = generate_preview_composition(screenshot_bytes, url, analysis)
    
    # Step 3: Combine into final output
    return {
        "analysis": analysis.to_dict(),
        "composition": composition.to_dict(),
        
        # Convenience fields for backward compatibility
        "title": composition.title_primary,
        "description": composition.description_primary,
        "type": analysis.design_intent.value,
        "confidence": analysis.confidence,
        
        # Variants for A/B testing
        "variants": {
            "action_oriented": {
                "title": composition.title_action_oriented,
                "description": composition.description_concise
            },
            "benefit_focused": {
                "title": composition.title_benefit_focused,
                "description": composition.description_detailed
            },
            "emotional": {
                "title": composition.title_emotional,
                "description": composition.description_primary
            }
        },
        
        # Visual guidance
        "visual_guidance": {
            "focal_point": composition.image_focal_point,
            "crop_region": composition.image_crop_suggestion,
            "emphasis_zones": [z.to_dict() for z in analysis.emphasis_zones],
            "style": composition.suggested_style,
            "overlay_position": composition.overlay_text_position
        },
        
        # Content extraction
        "content": {
            "headline": analysis.headline,
            "subheadline": analysis.subheadline,
            "cta": analysis.cta_text,
            "features": analysis.key_features,
            "social_proof": analysis.social_proof
        },
        
        # Quality metrics
        "quality": {
            "hierarchy_score": analysis.visual_hierarchy_score,
            "clarity_score": analysis.clarity_score,
            "clutter": analysis.clutter_assessment
        },
        
        # Reasoning for transparency
        "reasoning": analysis.reasoning
    }

