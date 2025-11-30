"""
Background job for demo preview generation (public, no auth required).
This job runs the same optimized preview generation logic as the synchronous endpoint,
but in a background worker to avoid Railway's 60-second load balancer timeout.
"""
from typing import Dict, Any
from uuid import uuid4
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from rq.job import Job, get_current_job
from backend.services.playwright_screenshot import capture_screenshot_and_html
from backend.services.r2_client import upload_file_to_r2
from backend.services.preview_reasoning import generate_reasoned_preview
from backend.services.preview_image_generator import generate_and_upload_preview_image
from backend.services.brand_extractor import extract_all_brand_elements
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
    Background job to generate demo preview with parallel processing and brand extraction.
    
    This is the async version of the synchronous generate_demo_preview_optimized endpoint.
    It runs the same logic but in a background worker to avoid Railway's timeout.
    
    Args:
        url: URL to generate preview for
        
    Returns:
        Dictionary with preview data matching DemoPreviewResponse schema
    """
    try:
        start_time = time.time()
        url_str = str(url)
        
        logger.info(f"🚀 Starting demo preview job for: {url_str}")
        
        # Update initial progress
        _update_job_progress(0.05, "Initializing...")
        
        # Check cache first
        redis_client = get_redis_client()
        cache_key = generate_cache_key(url_str, "demo:preview:v2:")
        
        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    logger.info(f"✅ Cache hit for: {url_str[:50]}...")
                    _update_job_progress(1.0, "Loaded from cache")
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
        
        # =========================================================================
        # STEP 1: Capture screenshot + HTML (single browser session)
        # =========================================================================
        _update_job_progress(0.10, "Capturing page screenshot...")
        try:
            logger.info(f"📸 Capturing screenshot + HTML for: {url_str}")
            screenshot_bytes, html_content = capture_screenshot_and_html(url_str)
            logger.info(f"✅ Screenshot captured ({len(screenshot_bytes)} bytes)")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Screenshot capture failed: {error_msg}", exc_info=True)
            _update_job_progress(0.0, f"Failed: {error_msg}")
            raise ValueError(f"Failed to capture page screenshot: {error_msg}")
        
        # =========================================================================
        # STEP 2: Parallel processing - Brand extraction + Screenshot upload
        # =========================================================================
        _update_job_progress(0.30, "Extracting brand elements and uploading screenshot...")
        screenshot_url = None
        brand_elements = None
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}
            
            # Task 1: Upload screenshot to R2
            future_upload = executor.submit(
                upload_file_to_r2,
                screenshot_bytes,
                f"screenshots/demo/{uuid4()}.png",
                "image/png"
            )
            futures[future_upload] = "screenshot_upload"
            
            # Task 2: Extract brand elements (logo, colors, hero image)
            future_brand = executor.submit(
                extract_all_brand_elements,
                html_content,
                url_str,
                screenshot_bytes
            )
            futures[future_brand] = "brand_extraction"
            
            # Wait for both to complete
            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    if task_name == "screenshot_upload":
                        screenshot_url = future.result()
                        logger.info(f"✅ Screenshot uploaded: {screenshot_url}")
                    elif task_name == "brand_extraction":
                        brand_elements = future.result()
                        logger.info(f"✅ Brand elements extracted: {brand_elements.get('brand_name') if brand_elements and isinstance(brand_elements, dict) else 'N/A'}")
                except Exception as e:
                    logger.warning(f"⚠️  {task_name} failed: {e}")
        
        # =========================================================================
        # STEP 3: Run multi-stage AI reasoning
        # =========================================================================
        _update_job_progress(0.60, "Running AI reasoning...")
        try:
            logger.info(f"🤖 Running AI reasoning for: {url_str}")
            result = generate_reasoned_preview(screenshot_bytes, url_str)
            logger.info(f"✅ AI reasoning complete")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ AI reasoning failed: {error_msg}", exc_info=True)
            
            if "429" in error_msg or "rate limit" in error_msg.lower():
                _update_job_progress(0.0, "OpenAI rate limit reached")
                raise ValueError("OpenAI rate limit reached. Please wait a moment and try again.")
            
            _update_job_progress(0.0, f"AI reasoning failed: {error_msg}")
            raise ValueError(f"Failed to analyze page: {error_msg}. Please try again.")
        
        # =========================================================================
        # STEP 4: Generate og:image with enhanced brand elements
        # =========================================================================
        _update_job_progress(0.80, "Generating final preview image...")
        composited_image_url = None
        try:
            logger.info("🎨 Generating brand-aligned og:image")
            
            # Use brand colors if available, otherwise use AI-extracted colors
            if brand_elements and isinstance(brand_elements, dict) and "colors" in brand_elements:
                brand_colors = brand_elements.get("colors", {})
                blueprint_colors = {
                    "primary_color": brand_colors.get("primary_color", result.blueprint.primary_color) if isinstance(brand_colors, dict) else result.blueprint.primary_color,
                    "secondary_color": brand_colors.get("secondary_color", result.blueprint.secondary_color) if isinstance(brand_colors, dict) else result.blueprint.secondary_color,
                    "accent_color": brand_colors.get("accent_color", result.blueprint.accent_color) if isinstance(brand_colors, dict) else result.blueprint.accent_color,
                }
            else:
                blueprint_colors = {
                    "primary_color": result.blueprint.primary_color,
                    "secondary_color": result.blueprint.secondary_color,
                    "accent_color": result.blueprint.accent_color,
                }
            
            # Use logo if available, otherwise use primary_image from AI
            image_for_preview = None
            if brand_elements and isinstance(brand_elements, dict) and brand_elements.get("logo_base64"):
                image_for_preview = brand_elements["logo_base64"]
                logger.info("Using extracted brand logo for preview")
            elif brand_elements and isinstance(brand_elements, dict) and brand_elements.get("hero_image_base64"):
                image_for_preview = brand_elements["hero_image_base64"]
                logger.info("Using extracted hero image for preview")
            else:
                image_for_preview = result.primary_image_base64
                logger.info("Using AI-extracted primary image for preview")
            
            composited_image_url = generate_and_upload_preview_image(
                screenshot_bytes=screenshot_bytes,
                url=url_str,
                title=result.title,
                subtitle=result.subtitle,
                description=result.description,
                cta_text=result.cta_text,
                blueprint=blueprint_colors,
                template_type=result.blueprint.template_type,
                tags=result.tags,
                context_items=[
                    {"icon": c["icon"], "text": c["text"]}
                    for c in result.context_items
                ],
                credibility_items=[
                    {"type": c["type"], "value": c["value"]}
                    for c in result.credibility_items
                ],
                primary_image_base64=image_for_preview
            )
            
            if composited_image_url:
                logger.info(f"✅ og:image generated: {composited_image_url}")
        except Exception as e:
            logger.warning(f"⚠️  og:image generation failed: {e}", exc_info=True)
            if screenshot_url:
                composited_image_url = screenshot_url
                logger.info(f"Using screenshot as fallback")
        
        # =========================================================================
        # STEP 5: Build response
        # =========================================================================
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Build brand elements dict
        brand_dict = {}
        if brand_elements and isinstance(brand_elements, dict):
            brand_dict = {
                "brand_name": brand_elements.get("brand_name"),
                "logo_base64": brand_elements.get("logo_base64"),
                "hero_image_base64": brand_elements.get("hero_image_base64")
            }
        
        response_data = {
            "url": url_str,
            
            # Content
            "title": result.title,
            "subtitle": result.subtitle,
            "description": result.description,
            "tags": result.tags,
            "context_items": [
                {"icon": c["icon"], "text": c["text"]}
                for c in result.context_items
            ],
            "credibility_items": [
                {"type": c["type"], "value": c["value"]}
                for c in result.credibility_items
            ],
            "cta_text": result.cta_text,
            
            # Images
            "primary_image_base64": result.primary_image_base64,
            "screenshot_url": screenshot_url,
            "composited_preview_image_url": composited_image_url,
            
            # Brand elements
            "brand": brand_dict,
            
            # Blueprint (use enhanced colors)
            "blueprint": {
                "template_type": result.blueprint.template_type,
                "primary_color": blueprint_colors["primary_color"],
                "secondary_color": blueprint_colors["secondary_color"],
                "accent_color": blueprint_colors["accent_color"],
                "coherence_score": result.blueprint.coherence_score,
                "balance_score": result.blueprint.balance_score,
                "clarity_score": result.blueprint.clarity_score,
                "overall_quality": result.blueprint.overall_quality,
                "layout_reasoning": result.blueprint.layout_reasoning,
                "composition_notes": result.blueprint.composition_notes
            },
            
            # Metrics
            "reasoning_confidence": result.reasoning_confidence,
            "processing_time_ms": processing_time_ms,
            
            # Metadata
            "is_demo": True,
            "message": "AI-reconstructed preview with enhanced brand extraction."
        }
        
        # Cache the result
        if redis_client:
            try:
                cache_data = json.dumps(response_data)
                ttl_seconds = CacheConfig.DEFAULT_TTL_HOURS * 3600
                redis_client.setex(cache_key, ttl_seconds, cache_data)
                logger.info(f"✅ Cached result for: {url_str[:50]}...")
            except Exception as e:
                logger.warning(f"⚠️  Failed to cache result: {e}")
        
        # Update final progress
        _update_job_progress(1.0, "Preview generation complete!")
        
        logger.info(f"🎉 Preview generated in {processing_time_ms}ms")
        return response_data
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Fatal error in demo preview job: {error_msg}", exc_info=True)
        try:
            _update_job_progress(0.0, f"Failed: {error_msg}")
        except:
            pass  # Don't fail if progress update fails
        raise

