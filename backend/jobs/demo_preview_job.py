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
    CacheConfig
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
        
        # Configure engine for demo mode
        config = PreviewEngineConfig(
            is_demo=True,
            enable_brand_extraction=True,
            enable_ai_reasoning=True,
            enable_composited_image=True,
            enable_cache=True,
            progress_callback=_update_job_progress
        )
        
        # Create engine and generate preview
        engine = PreviewEngine(config)
        result = engine.generate(url_str, cache_key_prefix="demo:preview:v2:")
        
        # Convert PreviewEngineResult to response dict
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
            "screenshot_url": screenshot_url,
            "composited_preview_image_url": result.composited_preview_image_url,
            
            # Brand elements
            "brand": result.brand,
            
            # Blueprint
            "blueprint": result.blueprint,
            
            # Metrics
            "reasoning_confidence": result.reasoning_confidence,
            "processing_time_ms": result.processing_time_ms,
            
            # Metadata
            "is_demo": True,
            "message": result.message
        }
        
        # Add warnings if any
        if result.warnings:
            logger.warning(f"Preview generated with warnings: {result.warnings}")
        
        logger.info(f"🎉 Preview generated in {result.processing_time_ms}ms")
        return response_data
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Fatal error in demo preview job: {error_msg}", exc_info=True)
        try:
            _update_job_progress(0.0, f"Failed: {error_msg}")
        except:
            pass  # Don't fail if progress update fails
        raise

