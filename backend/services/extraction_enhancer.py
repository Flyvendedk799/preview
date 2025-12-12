"""
Extraction Enhancement Layer

Integrates validation, quality scoring, and retry logic to ensure
high-quality AI extractions. This module wraps the base AI extraction
with intelligent quality gates and self-correction.

FEATURES:
1. Output validation (syntactic correctness)
2. Quality scoring (semantic quality)
3. Intelligent retry (when quality is poor)
4. Result correction (fix common errors)
5. Quality gates (minimum thresholds)

WORKFLOW:
Input → Extract → Validate → Score → [Retry if poor] → Fix → Output
"""

import logging
from typing import Dict, Any, Optional, Tuple, Callable, List
from dataclasses import dataclass, field
import time

# Import our validation and scoring modules
try:
    from backend.services.ai_output_validator import (
        AIOutputValidator,
        ValidationResult,
        ValidationSeverity
    )
    from backend.services.extraction_quality_scorer import (
        ExtractionQualityScorer,
        QualityBreakdown,
        QualityGrade
    )
    VALIDATION_AVAILABLE = True
except ImportError as e:
    VALIDATION_AVAILABLE = False
    logging.warning(f"Validation modules not available: {e}")

logger = logging.getLogger(__name__)


@dataclass
class EnhancedExtractionResult:
    """Result from enhanced extraction with quality metrics."""
    # Extraction result
    extraction: Dict[str, Any]
    
    # Quality metrics
    validation_result: Optional['ValidationResult'] = None
    quality_breakdown: Optional['QualityBreakdown'] = None
    
    # Metadata
    attempts: int = 1
    retry_performed: bool = False
    corrections_applied: List[str] = None
    processing_time_ms: int = 0
    
    # Quality flags
    is_valid: bool = True
    quality_grade: str = "C"
    should_use: bool = True
    
    def __post_init__(self):
        if self.corrections_applied is None:
            self.corrections_applied = []


class ExtractionEnhancer:
    """
    Enhances AI extractions with validation, scoring, and retry logic.
    
    This is the "quality assurance layer" for AI extractions.
    """
    
    def __init__(
        self,
        min_quality_threshold: float = 0.60,
        max_retry_attempts: int = 2,
        enable_auto_fix: bool = True
    ):
        """
        Initialize extraction enhancer.
        
        Args:
            min_quality_threshold: Minimum quality score (0.0-1.0) to accept without retry
            max_retry_attempts: Maximum number of retry attempts for poor extractions
            enable_auto_fix: Whether to automatically fix common errors
        """
        self.min_quality_threshold = min_quality_threshold
        self.max_retry_attempts = max_retry_attempts
        self.enable_auto_fix = enable_auto_fix
        
        if VALIDATION_AVAILABLE:
            self.validator = AIOutputValidator()
            self.scorer = ExtractionQualityScorer()
        else:
            logger.warning("⚠️  Validation/scoring unavailable, running without quality checks")
            self.validator = None
            self.scorer = None
    
    def enhance_extraction(
        self,
        extraction_func: Callable,
        *args,
        **kwargs
    ) -> EnhancedExtractionResult:
        """
        Enhance extraction with validation, scoring, and retry.
        
        Args:
            extraction_func: Function that performs extraction (e.g., run_stages_1_2_3)
            *args, **kwargs: Arguments to pass to extraction function
            
        Returns:
            EnhancedExtractionResult with quality metrics
        """
        start_time = time.time()
        attempts = 0
        best_result = None
        best_quality_score = -1.0
        
        while attempts < self.max_retry_attempts:
            attempts += 1
            
            try:
                # Perform extraction
                logger.info(f"📊 Extraction attempt {attempts}/{self.max_retry_attempts}")
                extraction = extraction_func(*args, **kwargs)
                
                # If validation not available, return immediately
                if not VALIDATION_AVAILABLE or not self.validator:
                    return EnhancedExtractionResult(
                        extraction=extraction,
                        attempts=attempts,
                        processing_time_ms=int((time.time() - start_time) * 1000),
                        quality_grade="Unknown"
                    )
                
                # Validate extraction
                validation_result = self.validator.validate_extraction(extraction)
                
                # Score quality
                quality_breakdown = self.scorer.score_extraction(extraction)
                
                # Apply auto-fixes if enabled
                corrections = []
                if self.enable_auto_fix:
                    extraction, fixes = self._apply_auto_fixes(
                        extraction,
                        validation_result,
                        quality_breakdown
                    )
                    corrections.extend(fixes)
                    
                    # Re-score after fixes
                    if fixes:
                        quality_breakdown = self.scorer.score_extraction(extraction)
                
                # Track best result
                if quality_breakdown.overall_score > best_quality_score:
                    best_quality_score = quality_breakdown.overall_score
                    best_result = EnhancedExtractionResult(
                        extraction=extraction,
                        validation_result=validation_result,
                        quality_breakdown=quality_breakdown,
                        attempts=attempts,
                        retry_performed=attempts > 1,
                        corrections_applied=corrections,
                        processing_time_ms=int((time.time() - start_time) * 1000),
                        is_valid=validation_result.is_valid,
                        quality_grade=quality_breakdown.grade.value,
                        should_use=quality_breakdown.overall_score >= self.min_quality_threshold
                    )
                
                # Check if quality is good enough
                if quality_breakdown.overall_score >= self.min_quality_threshold:
                    logger.info(
                        f"✅ Quality sufficient: {quality_breakdown.overall_score:.2f} "
                        f"(Grade {quality_breakdown.grade.value}) after {attempts} attempt(s)"
                    )
                    break
                
                # Quality too low, prepare for retry
                if attempts < self.max_retry_attempts:
                    logger.warning(
                        f"⚠️  Quality insufficient: {quality_breakdown.overall_score:.2f} "
                        f"(Grade {quality_breakdown.grade.value}), retrying... ({attempts}/{self.max_retry_attempts})"
                    )
                    
                    # Could add retry guidance here based on issues
                    # For now, just retry with same inputs
                    time.sleep(0.5)  # Brief pause before retry
                
            except Exception as e:
                logger.error(f"❌ Extraction attempt {attempts} failed: {e}", exc_info=True)
                
                if attempts >= self.max_retry_attempts:
                    # Return best result we have, or empty if none
                    if best_result:
                        logger.warning(f"Returning best available result (score: {best_quality_score:.2f})")
                        return best_result
                    else:
                        # Return failed result
                        return EnhancedExtractionResult(
                            extraction={},
                            attempts=attempts,
                            processing_time_ms=int((time.time() - start_time) * 1000),
                            is_valid=False,
                            quality_grade="F",
                            should_use=False
                        )
        
        # Return best result
        if best_result:
            if best_result.attempts > 1:
                logger.info(
                    f"🔄 Retry successful: improved from attempt 1 to {best_result.attempts} "
                    f"(final score: {best_quality_score:.2f})"
                )
            return best_result
        else:
            # Shouldn't reach here, but handle gracefully
            return EnhancedExtractionResult(
                extraction={},
                attempts=attempts,
                processing_time_ms=int((time.time() - start_time) * 1000),
                is_valid=False,
                quality_grade="F",
                should_use=False
            )
    
    def _apply_auto_fixes(
        self,
        extraction: Dict[str, Any],
        validation_result: 'ValidationResult',
        quality_breakdown: 'QualityBreakdown'
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Apply automatic fixes to common extraction issues.
        
        Returns:
            (fixed_extraction, list_of_corrections_applied)
        """
        corrections = []
        fixed = extraction.copy()
        
        # Fix 1: Truncate overly long hooks
        hook = fixed.get("the_hook", "")
        if hook and len(hook) > 150:
            sentences = hook.split(". ")
            if sentences:
                fixed["the_hook"] = sentences[0]
                corrections.append(f"Truncated long hook from {len(hook)} to {len(sentences[0])} chars")
        
        # Fix 2: Remove navigation hooks
        if hook:
            hook_lower = hook.lower().strip()
            nav_terms = ["home", "about", "contact", "welcome", "menu", "sign up", "login"]
            if hook_lower in nav_terms:
                # Try to use benefit or proof as hook instead
                if fixed.get("key_benefit"):
                    fixed["the_hook"] = fixed["key_benefit"]
                    corrections.append(f"Replaced navigation hook '{hook}' with benefit")
                elif fixed.get("social_proof_found"):
                    fixed["the_hook"] = fixed["social_proof_found"]
                    corrections.append(f"Replaced navigation hook '{hook}' with social proof")
        
        # Fix 3: For profiles, ensure hook is person name, not bio
        page_type = fixed.get("page_type", "").lower()
        is_profile = fixed.get("is_individual_profile", False)
        
        if (page_type == "profile" or is_profile) and hook:
            detected_name = fixed.get("detected_person_name")
            
            # If hook is long but detected_name is short, use detected_name
            if detected_name and len(detected_name) < len(hook) * 0.5:
                fixed["the_hook"] = detected_name
                corrections.append(f"Replaced bio with person name for profile")
        
        # Fix 4: Ensure profile classification consistency
        if is_profile and page_type not in ["profile", "personal"]:
            fixed["page_type"] = "profile"
            corrections.append(f"Fixed page_type to match is_individual_profile=true")
        elif page_type == "profile" and not is_profile:
            fixed["is_individual_profile"] = True
            corrections.append(f"Fixed is_individual_profile to match page_type='profile'")
        
        # Fix 5: Remove generic social proof without numbers
        proof = fixed.get("social_proof_found")
        if proof:
            has_numbers = any(char.isdigit() for char in proof)
            generic_proof = ["great reviews", "highly rated", "popular", "trusted"]
            
            if not has_numbers and any(gen in proof.lower() for gen in generic_proof):
                fixed["social_proof_found"] = None
                corrections.append(f"Removed generic social proof without numbers: '{proof}'")
        
        # Log corrections
        if corrections:
            logger.info(f"🔧 Applied {len(corrections)} auto-corrections")
            for correction in corrections:
                logger.debug(f"  - {correction}")
        
        return fixed, corrections
    
    def validate_and_score(
        self,
        extraction: Dict[str, Any]
    ) -> Tuple[ValidationResult, QualityBreakdown]:
        """
        Validate and score an extraction without retry.
        
        Useful for analyzing existing extractions.
        """
        if not VALIDATION_AVAILABLE:
            return None, None
        
        validation_result = self.validator.validate_extraction(extraction)
        quality_breakdown = self.scorer.score_extraction(extraction)
        
        return validation_result, quality_breakdown


# Convenience function
def enhance_extraction(
    extraction_func: Callable,
    *args,
    min_quality: float = 0.60,
    max_retries: int = 2,
    **kwargs
) -> EnhancedExtractionResult:
    """
    Convenience function to enhance an extraction.
    
    Args:
        extraction_func: Function that performs extraction
        *args, **kwargs: Arguments for extraction function
        min_quality: Minimum quality threshold
        max_retries: Maximum retry attempts
        
    Returns:
        EnhancedExtractionResult
    """
    enhancer = ExtractionEnhancer(
        min_quality_threshold=min_quality,
        max_retry_attempts=max_retries
    )
    return enhancer.enhance_extraction(extraction_func, *args, **kwargs)
