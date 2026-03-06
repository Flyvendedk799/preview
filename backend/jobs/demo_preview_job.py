"""
Background job for demo preview generation (public, no auth required).
This job uses the unified preview engine for consistent, high-quality previews.
"""
from typing import Dict, Any
from uuid import uuid4
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from rq.job import Job, get_current_job
from backend.services.preview_engine import PreviewEngine, PreviewEngineConfig, PreviewEngineResult
from backend.services.r2_client import upload_file_to_r2
from backend.services.preview_cache import (
    generate_cache_key,
    get_redis_client,
    CacheConfig,
    is_demo_cache_disabled
)
import json

logger = logging.getLogger(__name__)


def _update_job_progress(progress: float, message: str) -> None:
    """Update job progress in Redis for frontend polling."""
    try:
        job = get_current_job()
        if job:
            job.meta['progress'] = progress
            job.meta['message'] = message
            job.save_meta()
    except Exception as e:
        # Don't fail the job if progress update fails
        logger.warning(f"Failed to update job progress: {e}")


def generate_demo_preview_job(url: str) -> Dict[str, Any]:
    """
    Background job to generate demo preview using unified preview engine.
    
    This uses the unified PreviewEngine for consistent, high-quality previews
    with robust edge case handling and intelligent fallbacks.
    
    Args:
        url: URL to generate preview for
        
    Returns:
        Dictionary with preview data matching DemoPreviewResponse schema
    """
    try:
        url_str = str(url)
        logger.info(f"🚀 Starting demo preview job for: {url_str}")
        
        # Check if demo caching is disabled via admin toggle
        cache_disabled = is_demo_cache_disabled()
        
        if cache_disabled:
            logger.info(f"🚫 Cache DISABLED - generating fresh preview for: {url_str[:50]}...")
            # Invalidate any existing cache to ensure fresh results
            from backend.services.preview_cache import invalidate_cache
            invalidate_cache(url_str)
            logger.info(f"🗑️  Cleared existing cache entries for: {url_str[:50]}...")
        else:
            logger.info(f"✅ Cache ENABLED - checking cache first for: {url_str[:50]}...")
        
        # Update initial progress
        _update_job_progress(0.05, "Starting preview generation...")
        
        # Configure engine for demo mode (optimized for speed)
        config = PreviewEngineConfig(
            is_demo=True,
            enable_brand_extraction=True,
            enable_ai_reasoning=True,
            enable_composited_image=True,
            enable_cache=not cache_disabled,  # Disable cache if admin toggle is enabled
            enable_multi_agent=False,  # Demo: skip expensive multi-agent orchestration
            enable_ui_element_extraction=False,  # Demo: skip UI element extraction for speed
            progress_callback=_update_job_progress
        )
        
        # Create engine and generate preview
        engine = PreviewEngine(config)
        result = engine.generate(url_str, cache_key_prefix="demo:preview:v2:")
        
        # Ensure progress is at 100% when job completes successfully
        # Do this BEFORE returning to ensure it's saved to Redis
        _update_job_progress(1.0, "Preview generation complete!")
        
        # Small delay to ensure progress update is saved before job completes
        import time
        time.sleep(0.1)
        
        # Prepare brand elements with fallbacks
        brand_data = result.brand if result.brand else {}
        brand_elements = {
            "brand_name": brand_data.get("brand_name"),
            "logo_base64": brand_data.get("logo_base64"),
            "hero_image_base64": brand_data.get("hero_image_base64")
        }

        # Prepare layout blueprint with fallbacks to avoid validation errors
        blueprint_data = result.blueprint if result.blueprint else {}
        layout_blueprint = {
            "template_type": blueprint_data.get("template_type", "article"),
            "primary_color": blueprint_data.get("primary_color", "#2563EB"),
            "secondary_color": blueprint_data.get("secondary_color", "#1E40AF"),
            "accent_color": blueprint_data.get("accent_color", "#F59E0B"),
            "coherence_score": blueprint_data.get("coherence_score", 0.0),
            "balance_score": blueprint_data.get("balance_score", 0.0),
            "clarity_score": blueprint_data.get("clarity_score", 0.0),
            "design_fidelity_score": blueprint_data.get("design_fidelity_score"),
            "overall_quality": str(blueprint_data.get("overall_quality", "good")),
            "layout_reasoning": blueprint_data.get("layout_reasoning", ""),
            "composition_notes": blueprint_data.get("composition_notes", "")
        }

        # Prepare design DNA if available
        design_dna = None
        if hasattr(result, 'design_dna') and result.design_dna:
            # Need to convert string to float for formality if it's not already
            formality = result.design_dna.get("formality", 0.5)
            try:
                formality = float(formality)
            except (ValueError, TypeError):
                formality = 0.5
                
            design_dna = {
                "style": result.design_dna.get("style", "corporate"),
                "mood": result.design_dna.get("mood", "balanced"),
                "formality": formality,
                "typography_personality": result.design_dna.get("typography_personality", "bold"),
                "color_emotion": result.design_dna.get("color_emotion", "trust"),
                "spacing_feel": result.design_dna.get("spacing_feel", "balanced"),
                "brand_adjectives": result.design_dna.get("brand_adjectives", []),
                "design_reasoning": result.design_dna.get("design_reasoning", "")
            }

        # Convert PreviewEngineResult to response dict exactly matching DemoPreviewResponse via Pydantic mapping
        response_data = {
            "url": result.url,
            
            # Content
            "title": result.title,
            "subtitle": result.subtitle,
            "description": result.description,
            "tags": result.tags,
            "context_items": result.context_items,
            "credibility_items": result.credibility_items,
            "cta_text": result.cta_text,
            
            # Images
            "primary_image_base64": result.primary_image_base64,
            "screenshot_url": result.screenshot_url,
            "composited_preview_image_url": result.composited_preview_image_url,
            
            # Brand elements
            "brand": brand_elements,
            
            # Blueprint
            "blueprint": layout_blueprint,
            
            # Design DNA
            "design_dna": design_dna,
            
            # Metrics
            "reasoning_confidence": result.reasoning_confidence,
            "design_fidelity_score": getattr(result, 'design_fidelity_score', layout_blueprint.get("design_fidelity_score")),
            "processing_time_ms": result.processing_time_ms,
            
            # Metadata
            "is_demo": True,
            "message": result.message
        }
        
        # Add quality scores and warnings from pipeline
        if result.quality_scores:
            response_data["quality_scores"] = result.quality_scores
        if result.warnings:
            response_data["warnings"] = result.warnings
            logger.warning(f"Preview generated with warnings: {result.warnings}")

        logger.info(f"Preview generated in {result.processing_time_ms}ms")
        return response_data
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Fatal error in demo preview job: {error_msg}", exc_info=True)
        try:
            _update_job_progress(0.0, f"Failed: {error_msg}")
        except:
            pass  # Don't fail if progress update fails
        raise

