"""
Graceful Degradation - Tiered fallback system for preview generation.

Instead of binary success/failure, this module provides tiered degradation:
- Tier 1 (Best): Full multi-agent extraction + DNA-aware rendering
- Tier 2 (Good): Single-agent extraction + template rendering  
- Tier 3 (Acceptable): HTML metadata + basic rendering
- Tier 4 (Fallback): URL-based minimal preview

Each tier provides progressively simpler but still useful previews.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class QualityTier(str, Enum):
    """Quality tiers for degradation."""
    TIER_1_FULL = "tier_1_full"  # Best: Multi-agent + DNA
    TIER_2_STANDARD = "tier_2_standard"  # Good: Single-agent + template
    TIER_3_BASIC = "tier_3_basic"  # Acceptable: HTML metadata + basic
    TIER_4_MINIMAL = "tier_4_minimal"  # Fallback: URL-based minimal


@dataclass
class DegradationResult:
    """Result from degradation attempt."""
    tier: QualityTier
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    latency_ms: float = 0.0
    fallback_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tier": self.tier.value,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "latency_ms": self.latency_ms,
            "fallback_reason": self.fallback_reason
        }


@dataclass
class TierConfig:
    """Configuration for a quality tier."""
    tier: QualityTier
    timeout_seconds: float
    min_confidence: float
    retry_on_failure: bool
    description: str


# Tier configurations
TIER_CONFIGS: Dict[QualityTier, TierConfig] = {
    QualityTier.TIER_1_FULL: TierConfig(
        tier=QualityTier.TIER_1_FULL,
        timeout_seconds=45.0,
        min_confidence=0.7,
        retry_on_failure=False,  # Fall to next tier instead
        description="Full multi-agent extraction with Design DNA rendering"
    ),
    QualityTier.TIER_2_STANDARD: TierConfig(
        tier=QualityTier.TIER_2_STANDARD,
        timeout_seconds=30.0,
        min_confidence=0.5,
        retry_on_failure=False,
        description="Single-agent vision extraction with template rendering"
    ),
    QualityTier.TIER_3_BASIC: TierConfig(
        tier=QualityTier.TIER_3_BASIC,
        timeout_seconds=15.0,
        min_confidence=0.3,
        retry_on_failure=True,  # Retry once before final fallback
        description="HTML metadata extraction with basic rendering"
    ),
    QualityTier.TIER_4_MINIMAL: TierConfig(
        tier=QualityTier.TIER_4_MINIMAL,
        timeout_seconds=5.0,
        min_confidence=0.0,
        retry_on_failure=False,
        description="URL-based minimal preview (always succeeds)"
    ),
}


class GracefulDegradationHandler:
    """
    Handles graceful degradation through quality tiers.
    
    Attempts preview generation at each tier, falling back to
    simpler tiers on failure or timeout.
    """
    
    def __init__(self):
        """Initialize the handler."""
        logger.info("🛡️ GracefulDegradationHandler initialized")
    
    def execute_with_degradation(
        self,
        tier_handlers: Dict[QualityTier, Callable[[], Tuple[bool, Dict[str, Any], float]]],
        start_tier: QualityTier = QualityTier.TIER_1_FULL,
        url: Optional[str] = None
    ) -> DegradationResult:
        """
        Execute with graceful degradation through tiers.
        
        Args:
            tier_handlers: Dict mapping tiers to handler functions
                Each handler returns: (success, data, confidence)
            start_tier: Tier to start at
            url: URL for fallback generation
            
        Returns:
            DegradationResult from the successful tier
        """
        tiers = [
            QualityTier.TIER_1_FULL,
            QualityTier.TIER_2_STANDARD,
            QualityTier.TIER_3_BASIC,
            QualityTier.TIER_4_MINIMAL
        ]
        
        # Start from the specified tier
        start_idx = tiers.index(start_tier)
        tiers_to_try = tiers[start_idx:]
        
        last_error = None
        
        for tier in tiers_to_try:
            config = TIER_CONFIGS[tier]
            
            # Check if we have a handler for this tier
            if tier not in tier_handlers:
                logger.debug(f"No handler for {tier.value}, skipping")
                continue
            
            handler = tier_handlers[tier]
            start_time = time.time()
            
            try:
                logger.info(f"🎯 Attempting {tier.value}: {config.description}")
                
                # Execute with timeout
                success, data, confidence = self._execute_with_timeout(
                    handler, config.timeout_seconds
                )
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Check if result meets tier requirements
                if success and confidence >= config.min_confidence:
                    logger.info(
                        f"✅ {tier.value} succeeded: "
                        f"confidence={confidence:.2f}, "
                        f"latency={latency_ms:.0f}ms"
                    )
                    
                    return DegradationResult(
                        tier=tier,
                        success=True,
                        data=data,
                        latency_ms=latency_ms
                    )
                else:
                    reason = f"confidence {confidence:.2f} < {config.min_confidence}" if not success else "handler returned failure"
                    logger.warning(f"⚠️ {tier.value} failed: {reason}")
                    last_error = reason
                    
                    # Retry if configured
                    if config.retry_on_failure:
                        logger.info(f"🔄 Retrying {tier.value}...")
                        success, data, confidence = self._execute_with_timeout(
                            handler, config.timeout_seconds
                        )
                        latency_ms = (time.time() - start_time) * 1000
                        
                        if success and confidence >= config.min_confidence:
                            logger.info(f"✅ {tier.value} retry succeeded")
                            return DegradationResult(
                                tier=tier,
                                success=True,
                                data=data,
                                latency_ms=latency_ms
                            )
                    
            except TimeoutError:
                latency_ms = (time.time() - start_time) * 1000
                logger.warning(
                    f"⏱️ {tier.value} timed out after {config.timeout_seconds}s"
                )
                last_error = f"Timeout after {config.timeout_seconds}s"
                
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                logger.error(f"❌ {tier.value} error: {e}")
                last_error = str(e)
        
        # All tiers failed - return minimal fallback
        logger.warning("⚠️ All tiers failed, generating minimal preview")
        return self._generate_minimal_fallback(url, last_error)
    
    def _execute_with_timeout(
        self,
        handler: Callable[[], Tuple[bool, Dict[str, Any], float]],
        timeout_seconds: float
    ) -> Tuple[bool, Dict[str, Any], float]:
        """Execute a handler with timeout."""
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(handler)
            try:
                return future.result(timeout=timeout_seconds)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(f"Handler timed out after {timeout_seconds}s")
    
    def _generate_minimal_fallback(
        self,
        url: Optional[str],
        last_error: Optional[str]
    ) -> DegradationResult:
        """Generate minimal fallback preview."""
        from urllib.parse import urlparse
        
        # Extract domain from URL
        if url:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            path = parsed.path.strip("/")
            
            # Generate title from domain
            title = domain.replace(".", " ").title()
            
            # Generate description from path
            if path:
                path_parts = path.split("/")
                description = " - ".join(
                    p.replace("-", " ").replace("_", " ").title()
                    for p in path_parts[:2]
                    if p
                )
            else:
                description = f"Visit {domain}"
        else:
            title = "Preview"
            description = ""
            domain = "unknown"
        
        data = {
            "title": title,
            "description": description,
            "url": url or "",
            "domain": domain,
            "is_fallback": True,
            "fallback_tier": QualityTier.TIER_4_MINIMAL.value
        }
        
        return DegradationResult(
            tier=QualityTier.TIER_4_MINIMAL,
            success=True,
            data=data,
            fallback_reason=last_error,
            latency_ms=0.0
        )


class PreviewGenerationTiers:
    """
    Provides tier-specific preview generation handlers.
    
    Each tier implements a different level of preview generation:
    - Tier 1: Full multi-agent + Design DNA
    - Tier 2: Single vision agent + template
    - Tier 3: HTML metadata + basic template
    - Tier 4: URL-based minimal
    """
    
    def __init__(
        self,
        screenshot_bytes: Optional[bytes] = None,
        html_content: Optional[str] = None,
        url: Optional[str] = None
    ):
        """
        Initialize with page data.
        
        Args:
            screenshot_bytes: Page screenshot
            html_content: HTML content
            url: Page URL
        """
        self.screenshot_bytes = screenshot_bytes
        self.html_content = html_content
        self.url = url
    
    def get_tier_handlers(self) -> Dict[QualityTier, Callable[[], Tuple[bool, Dict[str, Any], float]]]:
        """Get handlers for each tier."""
        return {
            QualityTier.TIER_1_FULL: self._tier_1_full,
            QualityTier.TIER_2_STANDARD: self._tier_2_standard,
            QualityTier.TIER_3_BASIC: self._tier_3_basic,
            QualityTier.TIER_4_MINIMAL: self._tier_4_minimal
        }
    
    def _tier_1_full(self) -> Tuple[bool, Dict[str, Any], float]:
        """
        Tier 1: Full multi-agent extraction with Design DNA rendering.
        
        Uses:
        - Visual Analyst agent
        - Content Curator agent
        - Design Archaeologist agent
        - Context Fusion agent
        - DNA Applicator for rendering
        """
        try:
            from backend.services.ai_orchestrator import AIOrchestrator
            from backend.services.design_dna_applicator import apply_design_dna
            
            if not self.screenshot_bytes or not self.html_content:
                return False, {}, 0.0
            
            # Run multi-agent orchestration
            orchestrator = AIOrchestrator()
            result = orchestrator.orchestrate_preview_generation(
                url=self.url or "",
                screenshot_bytes=self.screenshot_bytes,
                html_content=self.html_content,
                complexity="medium"
            )
            
            if not result.success:
                return False, {}, 0.0
            
            # Apply Design DNA
            design_dna = result.fused_result.get("design_dna", {})
            color_palette = result.fused_result.get("color_palette", {})
            
            rendering_params = apply_design_dna(
                design_dna,
                color_palette,
                page_type=result.fused_result.get("page_type", "landing")
            )
            
            data = {
                **result.fused_result,
                "rendering_params": rendering_params.to_dict(),
                "tier": "tier_1_full"
            }
            
            return True, data, result.quality_score
            
        except Exception as e:
            logger.error(f"Tier 1 failed: {e}")
            return False, {}, 0.0
    
    def _tier_2_standard(self) -> Tuple[bool, Dict[str, Any], float]:
        """
        Tier 2: Single vision agent extraction with template rendering.
        
        Uses:
        - Vision extraction only (no multi-agent)
        - Standard template selection
        """
        try:
            from backend.services.multi_modal_fusion import MultiModalFusionEngine
            
            if not self.screenshot_bytes:
                return False, {}, 0.0
            
            # Use multi-modal fusion (simpler than full orchestration)
            engine = MultiModalFusionEngine()
            result = engine.extract_preview_content(
                html_content=self.html_content or "",
                screenshot_bytes=self.screenshot_bytes,
                url=self.url or ""
            )
            
            confidence = result.get("confidence", 0.5)
            
            data = {
                "title": result.get("title"),
                "description": result.get("description"),
                "design": result.get("design", {}),
                "tier": "tier_2_standard"
            }
            
            return True, data, confidence
            
        except Exception as e:
            logger.error(f"Tier 2 failed: {e}")
            return False, {}, 0.0
    
    def _tier_3_basic(self) -> Tuple[bool, Dict[str, Any], float]:
        """
        Tier 3: HTML metadata extraction with basic rendering.
        
        Uses:
        - HTML metadata extraction only (no AI)
        - Basic template
        """
        try:
            from backend.services.metadata_extractor import extract_metadata_from_html
            
            if not self.html_content:
                return False, {}, 0.0
            
            metadata = extract_metadata_from_html(self.html_content)
            
            title = (
                metadata.get("og_title") or
                metadata.get("title") or
                metadata.get("h1")
            )
            
            description = (
                metadata.get("og_description") or
                metadata.get("description")
            )
            
            if not title:
                return False, {}, 0.0
            
            data = {
                "title": title,
                "description": description,
                "image_url": metadata.get("og_image"),
                "tier": "tier_3_basic"
            }
            
            # Calculate simple confidence based on completeness
            completeness = 0.0
            if title:
                completeness += 0.4
            if description:
                completeness += 0.3
            if metadata.get("og_image"):
                completeness += 0.3
            
            return True, data, completeness
            
        except Exception as e:
            logger.error(f"Tier 3 failed: {e}")
            return False, {}, 0.0
    
    def _tier_4_minimal(self) -> Tuple[bool, Dict[str, Any], float]:
        """
        Tier 4: URL-based minimal preview (always succeeds).
        
        Uses:
        - URL parsing only
        - Minimal display
        """
        from urllib.parse import urlparse
        
        parsed = urlparse(self.url or "")
        domain = parsed.netloc.replace("www.", "")
        
        data = {
            "title": domain.replace(".", " ").title() if domain else "Preview",
            "description": f"Visit {domain}" if domain else "",
            "url": self.url or "",
            "tier": "tier_4_minimal"
        }
        
        return True, data, 0.3  # Low but non-zero confidence


# Singleton handler
_handler_instance: Optional[GracefulDegradationHandler] = None


def get_degradation_handler() -> GracefulDegradationHandler:
    """Get or create the degradation handler singleton."""
    global _handler_instance
    if _handler_instance is None:
        _handler_instance = GracefulDegradationHandler()
    return _handler_instance


def execute_with_graceful_degradation(
    screenshot_bytes: Optional[bytes],
    html_content: Optional[str],
    url: Optional[str],
    start_tier: QualityTier = QualityTier.TIER_1_FULL
) -> DegradationResult:
    """Convenience function to execute with graceful degradation."""
    handler = get_degradation_handler()
    tiers = PreviewGenerationTiers(screenshot_bytes, html_content, url)
    
    return handler.execute_with_degradation(
        tier_handlers=tiers.get_tier_handlers(),
        start_tier=start_tier,
        url=url
    )

