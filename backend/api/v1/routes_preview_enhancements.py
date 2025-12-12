"""
Preview Enhancement Routes - Advanced Preview Generation Features.

PHASE 3 IMPLEMENTATION:
Exposes the new enhancement systems via API endpoints:
- Multi-variant generation for user selection
- Platform-specific optimization
- Value proposition enhancement
- Image quality scoring and enhancement
- Readability auto-fix

These endpoints work with existing preview generation
to provide enhanced capabilities.
"""

import logging
from typing import Optional, List, Dict, Any
from io import BytesIO
import base64
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/preview-enhancements", tags=["preview-enhancements"])


# =============================================================================
# SCHEMAS
# =============================================================================

class ValuePropRequest(BaseModel):
    """Request for value proposition enhancement."""
    title: str = Field(..., description="Original page title")
    description: Optional[str] = Field(None, description="Original page description")
    features: Optional[List[str]] = Field(None, description="List of features")
    page_type: str = Field("default", description="Page type (saas, product, article, etc.)")


class ValuePropResponse(BaseModel):
    """Response with enhanced value proposition."""
    hook: str
    benefit: str
    secondary_benefits: List[str] = []
    cta: str
    emotional_trigger: Optional[str] = None
    social_proof: Optional[str] = None
    confidence: float
    enhanced: bool


class ImageQualityRequest(BaseModel):
    """Request for image quality scoring (uses base64 image)."""
    image_base64: str = Field(..., description="Base64 encoded image")
    expected_type: str = Field("generic", description="Expected content type")


class ImageQualityResponse(BaseModel):
    """Response with image quality scores."""
    overall_score: float
    resolution_score: float
    sharpness_score: float
    composition_score: float
    color_quality_score: float
    is_usable: bool
    is_stock_photo: bool
    recommendations: List[str]
    available: bool


class PlatformOptimizeRequest(BaseModel):
    """Request for platform-specific optimization."""
    image_base64: str = Field(..., description="Base64 encoded preview image")
    platforms: List[str] = Field(
        default=["linkedin", "twitter", "facebook"],
        description="Target platforms"
    )
    content: Optional[Dict[str, Any]] = Field(None, description="Content for text adaptation")


class PlatformVariantInfo(BaseModel):
    """Information about a platform variant."""
    platform: str
    width: int
    height: int
    image_base64: str


class PlatformOptimizeResponse(BaseModel):
    """Response with platform-optimized variants."""
    variants: List[PlatformVariantInfo]
    available: bool


class StyleVariantInfo(BaseModel):
    """Information about a style variant."""
    id: str
    name: str
    description: str
    image_base64: str
    readability_score: float
    visual_appeal_score: float
    is_default: bool
    tags: List[str]


class VariantGenerateRequest(BaseModel):
    """Request for style variant generation."""
    image_base64: str = Field(..., description="Base64 encoded preview image")
    count: int = Field(4, ge=2, le=8, description="Number of variants to generate")
    styles: Optional[List[str]] = Field(None, description="Specific styles to use")


class VariantGenerateResponse(BaseModel):
    """Response with generated style variants."""
    variants: List[StyleVariantInfo]
    default_id: str
    generation_time_ms: int
    available: bool


class ReadabilityFixRequest(BaseModel):
    """Request for readability auto-fix."""
    image_base64: str = Field(..., description="Base64 encoded preview image")


class ReadabilityFixResponse(BaseModel):
    """Response with readability-fixed image."""
    fixed: bool
    fixes_applied: List[str] = []
    improvement: float = 0.0
    final_contrast: float = 0.0
    meets_wcag_aa: bool = False
    meets_wcag_aaa: bool = False
    image_base64: Optional[str] = None


class EnhancementsStatusResponse(BaseModel):
    """Response with available enhancements."""
    readability_auto_fixer: bool
    value_prop_extractor: bool
    smart_image_processor: bool
    platform_optimizer: bool
    variant_generator: bool
    visual_quality_validator: bool
    composition_intelligence: bool


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/status", response_model=EnhancementsStatusResponse)
def get_enhancement_status():
    """
    Get status of all enhancement systems.
    
    Returns which enhancement features are available.
    """
    try:
        from backend.services.preview_engine import get_available_enhancements
        status = get_available_enhancements()
        return EnhancementsStatusResponse(**status)
    except Exception as e:
        logger.error(f"Failed to get enhancement status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get enhancement status"
        )


@router.post("/value-prop", response_model=ValuePropResponse)
def enhance_value_proposition(request: ValuePropRequest):
    """
    Enhance content with value proposition intelligence.
    
    Transforms raw titles and descriptions into compelling hooks
    that drive engagement.
    """
    try:
        from backend.services.preview_engine import PreviewEngine, PreviewEngineConfig
        
        engine = PreviewEngine(PreviewEngineConfig())
        result = engine.enhance_content_with_value_prop(
            title=request.title,
            description=request.description,
            features=request.features,
            page_type=request.page_type
        )
        
        return ValuePropResponse(
            hook=result.get("hook", request.title),
            benefit=result.get("benefit", request.description or ""),
            secondary_benefits=result.get("secondary_benefits", []),
            cta=result.get("cta", "Learn More"),
            emotional_trigger=result.get("emotional_trigger"),
            social_proof=result.get("social_proof"),
            confidence=result.get("confidence", 0.0),
            enhanced=result.get("enhanced", False)
        )
    except Exception as e:
        logger.error(f"Value proposition enhancement failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Value proposition enhancement failed: {str(e)}"
        )


@router.post("/score-image", response_model=ImageQualityResponse)
def score_image_quality_endpoint(request: ImageQualityRequest):
    """
    Score image quality and get enhancement recommendations.
    
    Analyzes sharpness, composition, color quality, and detects stock photos.
    """
    try:
        from backend.services.preview_engine import PreviewEngine, PreviewEngineConfig
        
        # Decode image
        image_bytes = base64.b64decode(request.image_base64)
        
        engine = PreviewEngine(PreviewEngineConfig())
        result = engine.score_hero_image(image_bytes, request.expected_type)
        
        if not result.get("available", False):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Image quality scoring not available"
            )
        
        return ImageQualityResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image quality scoring failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image quality scoring failed: {str(e)}"
        )


@router.post("/optimize-platforms", response_model=PlatformOptimizeResponse)
def optimize_for_platforms_endpoint(request: PlatformOptimizeRequest):
    """
    Generate optimized variants for multiple platforms.
    
    Creates platform-specific versions with proper dimensions and styling.
    Supported platforms: linkedin, twitter, facebook, slack, discord, instagram, pinterest, whatsapp
    """
    try:
        from backend.services.preview_engine import PreviewEngine, PreviewEngineConfig
        
        # Decode image
        image_bytes = base64.b64decode(request.image_base64)
        
        engine = PreviewEngine(PreviewEngineConfig())
        result = engine.generate_platform_variants(
            image_bytes=image_bytes,
            platforms=request.platforms,
            content=request.content
        )
        
        if "default" in result and len(result) == 1:
            # Only default returned, platform optimizer not available
            return PlatformOptimizeResponse(variants=[], available=False)
        
        variants = []
        for platform, variant_bytes in result.items():
            from PIL import Image
            img = Image.open(BytesIO(variant_bytes))
            
            variants.append(PlatformVariantInfo(
                platform=platform,
                width=img.width,
                height=img.height,
                image_base64=base64.b64encode(variant_bytes).decode('utf-8')
            ))
        
        return PlatformOptimizeResponse(variants=variants, available=True)
    except Exception as e:
        logger.error(f"Platform optimization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Platform optimization failed: {str(e)}"
        )


@router.post("/generate-variants", response_model=VariantGenerateResponse)
def generate_style_variants_endpoint(request: VariantGenerateRequest):
    """
    Generate multiple style variants for user selection.
    
    Creates diverse variants with different visual treatments.
    Available styles: hero, text, minimal, gradient, dark, light, bold, subtle
    """
    try:
        from backend.services.preview_engine import PreviewEngine, PreviewEngineConfig
        
        # Decode image
        image_bytes = base64.b64decode(request.image_base64)
        
        engine = PreviewEngine(PreviewEngineConfig())
        result = engine.generate_style_variants(
            image_bytes=image_bytes,
            count=request.count,
            styles=request.styles
        )
        
        if not result.get("available", False):
            return VariantGenerateResponse(
                variants=[],
                default_id="original",
                generation_time_ms=0,
                available=False
            )
        
        variants = []
        for v in result.get("variants", []):
            variants.append(StyleVariantInfo(
                id=v["id"],
                name=v["name"],
                description=v["description"],
                image_base64=base64.b64encode(v["image_bytes"]).decode('utf-8'),
                readability_score=v["readability_score"],
                visual_appeal_score=v["visual_appeal_score"],
                is_default=v["is_default"],
                tags=v["tags"]
            ))
        
        return VariantGenerateResponse(
            variants=variants,
            default_id=result.get("default_id", "original"),
            generation_time_ms=result.get("generation_time_ms", 0),
            available=True
        )
    except Exception as e:
        logger.error(f"Variant generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Variant generation failed: {str(e)}"
        )


@router.post("/fix-readability", response_model=ReadabilityFixResponse)
def fix_readability_endpoint(request: ReadabilityFixRequest):
    """
    Automatically fix readability issues in a preview image.
    
    Applies contrast adjustments, overlays, and shadows to meet WCAG standards.
    """
    try:
        from backend.services.preview_engine import PreviewEngine, PreviewEngineConfig
        
        # Decode image
        image_bytes = base64.b64decode(request.image_base64)
        
        engine = PreviewEngine(PreviewEngineConfig())
        fixed_bytes, report = engine.auto_fix_preview_readability(image_bytes)
        
        return ReadabilityFixResponse(
            fixed=report.get("fixed", False),
            fixes_applied=report.get("fixes", []),
            improvement=report.get("improvement", 0.0),
            final_contrast=report.get("final_contrast", 0.0),
            meets_wcag_aa=report.get("meets_wcag_aa", False),
            meets_wcag_aaa=report.get("meets_wcag_aaa", False),
            image_base64=base64.b64encode(fixed_bytes).decode('utf-8') if report.get("fixed") else None
        )
    except Exception as e:
        logger.error(f"Readability fix failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Readability fix failed: {str(e)}"
        )


@router.get("/available-styles")
def get_available_styles():
    """
    Get list of available variant styles.
    """
    try:
        from backend.services.variant_generator import get_available_styles, VARIANT_PRESETS
        
        styles = []
        for style_name in get_available_styles():
            preset = VARIANT_PRESETS.get(style_name)
            if preset:
                styles.append({
                    "name": style_name,
                    "style_type": preset.style.value,
                    "layout": preset.layout.value,
                    "use_gradient": preset.use_gradient,
                    "headline_scale": preset.headline_size_multiplier
                })
        
        return {"styles": styles, "available": True}
    except Exception as e:
        logger.warning(f"Could not get available styles: {e}")
        return {"styles": [], "available": False}


@router.get("/available-platforms")
def get_available_platforms():
    """
    Get list of available platforms for optimization.
    """
    try:
        from backend.services.platform_optimizer import PLATFORM_CONFIGS, Platform
        
        platforms = []
        for platform, config in PLATFORM_CONFIGS.items():
            platforms.append({
                "name": config.name,
                "display_name": config.display_name,
                "width": config.width,
                "height": config.height,
                "style": config.style,
                "max_headline_chars": config.max_headline_chars,
                "max_description_chars": config.max_description_chars
            })
        
        return {"platforms": platforms, "available": True}
    except Exception as e:
        logger.warning(f"Could not get available platforms: {e}")
        return {"platforms": [], "available": False}

