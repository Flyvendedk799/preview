"""Main preview generation pipeline job."""
from typing import Dict
from backend.db.session import SessionLocal
from backend.models.domain import Domain as DomainModel
from backend.models.brand import BrandSettings as BrandSettingsModel
from backend.schemas.brand import BrandSettings as BrandSettingsSchema
from backend.utils.url_sanitizer import sanitize_url
from backend.services.preview_generator import fetch_page_html
from backend.services.metadata_extractor import extract_metadata_from_html
from backend.services.semantic_extractor import extract_semantic_structure
from backend.jobs.ai_generation import generate_ai_metadata
from backend.services.ai_validation import validate_ai_output
from backend.services.preview_type_predictor import predict_preview_type
from backend.jobs.screenshot_generation import generate_screenshot
from backend.jobs.preview_upsert import upsert_preview
from backend.services.brand_rewriter import rewrite_to_brand_voice
from backend.services.preview_image_generator import generate_and_upload_preview_image
from backend.services.playwright_screenshot import capture_screenshot
from backend.models.preview_variant import PreviewVariant as PreviewVariantModel
from backend.models.preview_job_failure import PreviewJobFailure as PreviewJobFailureModel
from backend.core.config import settings
from backend.exceptions.screenshot_failed import ScreenshotFailedException
from backend.services.activity_logger import log_activity
import logging
import traceback

logger = logging.getLogger("preview_worker")


def _derive_brand_tone_hint(brand_schema):
    """Derive brand tone hint from brand settings."""
    primary = brand_schema.primary_color.lower()
    if any(c in primary for c in ['ff', 'f00', 'e00']):
        return "bold"
    elif any(c in primary for c in ['00f', '009', '006']):
        return "professional"
    else:
        return "neutral"


def generate_preview_job(user_id: int, organization_id: int, url: str, domain: str) -> Dict:
    """
    Main background job to generate preview for a URL.
    
    This is the entry point called by RQ worker.
    
    Args:
        user_id: ID of the user requesting the preview
        organization_id: ID of the organization
        url: URL to generate preview for
        domain: Domain name
        
    Returns:
        Dictionary with preview_id and preview data
    """
    db = SessionLocal()
    try:
        # Step 1: Validate domain ownership
        domain_obj = db.query(DomainModel).filter(
            DomainModel.name == domain,
            DomainModel.organization_id == organization_id
        ).first()
        
        if not domain_obj:
            raise ValueError("Domain not found or not owned by the organization")
        
        # Step 2: Sanitize URL
        sanitized_url = sanitize_url(url, domain)
        
        # Step 3: Fetch HTML
        html_content = fetch_page_html(sanitized_url)
        
        # Step 4: Extract metadata using BeautifulSoup
        metadata = extract_metadata_from_html(html_content)
        
        # Step 4.5: Extract semantic structure for validation and fallbacks
        semantic_data = extract_semantic_structure(html_content)
        
        # Step 5: Load brand settings
        brand_settings = db.query(BrandSettingsModel).filter(
            BrandSettingsModel.organization_id == organization_id
        ).first()
        
        # If no brand settings exist, create default ones
        if not brand_settings:
            brand_settings = BrandSettingsModel(
                primary_color="#2979FF",
                secondary_color="#0A1A3C",
                accent_color="#3FFFD3",
                font_family="Inter",
                logo_url=None,
                user_id=user_id,
                organization_id=organization_id,
            )
            db.add(brand_settings)
            db.commit()
            db.refresh(brand_settings)
        
        # Step 6: Convert to schema for AI generator
        brand_schema = BrandSettingsSchema.model_validate(brand_settings)
        
        # Step 7: Generate AI metadata with enhanced prompt
        ai_result = generate_ai_metadata(sanitized_url, brand_schema, html_content)
        
        # Step 8: Validate AI output with semantic data and brand tone
        brand_tone_hint = _derive_brand_tone_hint(brand_schema)
        validated_ai = validate_ai_output(ai_result, metadata, brand_tone_hint, semantic_data)
        
        # Step 9: Predict preview type
        preview_type = predict_preview_type(metadata, sanitized_url, validated_ai)
        
        # Step 10: Apply brand tone rewriting to main description
        main_description = validated_ai.get("description") or ""
        rewritten_description = rewrite_to_brand_voice(main_description, brand_schema)
        
        # Step 11: Capture screenshot and upload to R2 (returns main + highlight)
        main_image_url = None
        highlight_image_url = None
        try:
            main_image_url, highlight_image_url = generate_screenshot(sanitized_url)
        except ScreenshotFailedException as e:
            logger.error("Screenshot generation failed, using fallback", exc_info=True)
            # Fallback to AI-generated image URL if available
            main_image_url = ai_result.get("image_url") or ""
            highlight_image_url = main_image_url
        
        # Step 12: Use placeholder if both screenshot and AI image failed
        if not main_image_url:
            main_image_url = settings.PLACEHOLDER_IMAGE_URL
            highlight_image_url = settings.PLACEHOLDER_IMAGE_URL
            logger.warning(f"Using placeholder image for URL: {sanitized_url}")
        
        # Step 12.5: Generate composited preview image (designed UI card)
        composited_image_url = None
        try:
            # Capture screenshot bytes for composited image generation
            screenshot_bytes = capture_screenshot(sanitized_url)
            
            # Generate designed og:image with typography overlay
            composited_image_url = generate_and_upload_preview_image(
                screenshot_bytes=screenshot_bytes,
                url=sanitized_url,
                title=validated_ai["title"],
                subtitle=None,  # Can be enhanced later
                description=rewritten_description,
                cta_text=None,  # Can be enhanced later
                blueprint={
                    "primary_color": brand_schema.primary_color,
                    "secondary_color": brand_schema.secondary_color,
                    "accent_color": brand_schema.accent_color
                },
                template_type=preview_type
            )
            if composited_image_url:
                logger.info(f"Generated composited preview image: {composited_image_url}")
        except Exception as e:
            logger.warning(f"Failed to generate composited preview image: {e}", exc_info=True)
            # Continue without composited image - will use highlight_image_url as fallback
        
        # Step 13: Upsert preview in database with all metadata
        keywords_str = ",".join(validated_ai.get("keywords", [])) if validated_ai.get("keywords") else None
        
        preview = upsert_preview(
            db=db,
            url=sanitized_url,
            domain=domain,
            title=validated_ai["title"],
            description=rewritten_description,  # Use rewritten description
            image_url=main_image_url,
            highlight_image_url=highlight_image_url,
            composited_image_url=composited_image_url,
            preview_type=preview_type,
            user_id=user_id,
            organization_id=organization_id,
            keywords=keywords_str,
            tone=validated_ai.get("tone"),
            ai_reasoning=validated_ai.get("reasoning")
        )
        
        # Step 14: Create preview variants
        variants_data = [
            ("a", validated_ai.get("variant_a", {})),
            ("b", validated_ai.get("variant_b", {})),
            ("c", validated_ai.get("variant_c", {})),
        ]
        
        for variant_key, variant_info in variants_data:
            if variant_info and variant_info.get("title"):
                # Apply brand rewriting to variant descriptions
                variant_desc = variant_info.get("description", "")
                rewritten_variant_desc = rewrite_to_brand_voice(variant_desc, brand_schema) if variant_desc else None
                
                variant = PreviewVariantModel(
                    preview_id=preview.id,
                    variant_key=variant_key,
                    title=variant_info.get("title", "")[:200],
                    description=rewritten_variant_desc[:500] if rewritten_variant_desc else None,
                    tone=validated_ai.get("tone"),
                    keywords=keywords_str,  # Reuse main keywords
                    image_url=highlight_image_url,  # Use highlight image for variants
                )
                db.add(variant)
        
        db.commit()
        db.refresh(preview)
        
        # Log successful job completion
        log_activity(
            db,
            user_id=user_id,
            action="preview.ai_job.completed",
            metadata={"preview_id": preview.id, "url": sanitized_url, "domain": domain, "type": preview_type},
            request=None  # No request in background job
        )
        
        return {
            "preview_id": preview.id,
            "preview": {
                "id": preview.id,
                "url": preview.url,
                "domain": preview.domain,
                "title": preview.title,
                "type": preview.type,
                "image_url": preview.image_url,
                "description": preview.description,
                "keywords": preview.keywords,
                "tone": preview.tone,
                "ai_reasoning": preview.ai_reasoning,
                "created_at": preview.created_at.isoformat(),
                "monthly_clicks": preview.monthly_clicks,
            }
        }
        
    except Exception as e:
        logger.error("Preview generation job failed", exc_info=True)
        
        # Save to Dead Letter Queue (DLQ)
        try:
            failure_record = PreviewJobFailureModel(
                job_id=None,  # Could be passed from RQ if available
                preview_id=None,  # Preview wasn't created yet
                url=url,
                organization_id=organization_id,
                error_message=str(e),
                stacktrace=traceback.format_exc()
            )
            db.add(failure_record)
            db.commit()
        except Exception as dlq_error:
            logger.error(f"Failed to save job failure to DLQ: {dlq_error}", exc_info=True)
        
        # Log job failure
        try:
            log_activity(
                db,
                user_id=user_id,
                action="preview.ai_job.failed",
                metadata={"url": url, "domain": domain, "error": str(e)},
                request=None
            )
        except Exception:
            pass  # Don't fail if logging fails
        
        raise
    finally:
        # Always close DB session
        db.close()

