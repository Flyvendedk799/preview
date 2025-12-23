"""
Quality Gates and Confidence Thresholds

Enforces minimum quality standards for AI extractions before they reach production.

QUALITY GATES:
1. Minimum confidence threshold (0.0-1.0)
2. Required fields validation
3. Content sensibility checks
4. Classification confidence gates
5. Extraction quality gates

ACTIONS:
- PASS: Use extraction immediately
- WARN: Use but log warning
- FAIL: Block and retry/fallback
- REJECT: Critical failure, use minimal fallback
"""

import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class GateStatus(str, Enum):
    """Quality gate status."""
    PASS = "pass"          # Meets all quality standards
    PASS_WITH_WARNINGS = "pass_with_warnings"  # Acceptable but has minor issues
    FAIL = "fail"          # Below standards, should retry
    REJECT = "reject"      # Critical failure, use fallback


@dataclass
class QualityGateResult:
    """Result from quality gate evaluation."""
    status: GateStatus
    overall_quality_score: float  # 0.0-1.0
    confidence_score: float  # 0.0-1.0
    
    # Gate results
    passed_gates: list
    failed_gates: list
    warnings: list
    
    # Recommendations
    should_use: bool
    should_retry: bool
    should_fallback: bool
    
    # Details
    gate_details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.gate_details is None:
            self.gate_details = {}


class QualityGateConfig:
    """
    UPGRADED: Professional-grade quality gate configuration.
    
    Higher standards for production marketing quality.
    """
    
    def __init__(
        self,
        min_extraction_quality: float = 0.65,  # UPGRADED from 0.60
        min_confidence: float = 0.55,           # UPGRADED from 0.50
        min_classification_confidence: float = 0.45,  # UPGRADED from 0.40
        require_hook: bool = True,
        allow_navigation_hooks: bool = False,
        require_social_proof_numbers: bool = False,
        enforce_profile_name_validation: bool = True,
        # NEW: Professional quality requirements
        min_visual_quality: float = 0.60,       # Minimum visual quality score
        min_contrast_ratio: float = 4.5,        # WCAG AA standard
        require_headline: bool = True,           # Must have a headline
        max_text_blur: float = 0.3               # Maximum acceptable blur
    ):
        """
        Initialize PROFESSIONAL quality gate configuration.
        
        Args:
            min_extraction_quality: Minimum overall quality score (0.65 for professional)
            min_confidence: Minimum AI confidence score (0.55 for reliability)
            min_classification_confidence: Minimum page classification confidence
            require_hook: Whether hook/title is mandatory
            allow_navigation_hooks: Whether to allow navigation text as hooks
            require_social_proof_numbers: Whether social proof must have numbers
            enforce_profile_name_validation: Whether to enforce strict name validation
            min_visual_quality: Minimum visual quality for the output image
            min_contrast_ratio: Minimum contrast ratio for text readability
            require_headline: Whether a headline is mandatory
            max_text_blur: Maximum acceptable text blur level
        """
        self.min_extraction_quality = min_extraction_quality
        self.min_confidence = min_confidence
        self.min_classification_confidence = min_classification_confidence
        self.require_hook = require_hook
        self.allow_navigation_hooks = allow_navigation_hooks
        self.require_social_proof_numbers = require_social_proof_numbers
        self.enforce_profile_name_validation = enforce_profile_name_validation
        # Professional standards
        self.min_visual_quality = min_visual_quality
        self.min_contrast_ratio = min_contrast_ratio
        self.require_headline = require_headline
        self.max_text_blur = max_text_blur


class QualityGateEvaluator:
    """
    Evaluates extractions against quality gates.
    
    Determines if extraction meets minimum standards for production use.
    """
    
    def __init__(self, config: Optional[QualityGateConfig] = None):
        """
        Initialize quality gate evaluator.
        
        Args:
            config: Quality gate configuration (uses defaults if None)
        """
        self.config = config or QualityGateConfig()
        self._navigation_terms = {
            "home", "about", "contact", "services", "products",
            "welcome", "menu", "login", "sign up"
        }
    
    def evaluate(
        self,
        extraction: Dict[str, Any],
        quality_score: Optional[float] = None,
        validation_result: Optional[Any] = None
    ) -> QualityGateResult:
        """
        Evaluate extraction against all quality gates.
        
        Args:
            extraction: AI extraction result
            quality_score: Quality score from scorer (if available)
            validation_result: Validation result from validator (if available)
            
        Returns:
            QualityGateResult with pass/fail status and recommendations
        """
        passed_gates = []
        failed_gates = []
        warnings = []
        gate_details = {}
        
        # Gate 1: Minimum overall quality
        if quality_score is not None:
            if quality_score >= self.config.min_extraction_quality:
                passed_gates.append("overall_quality")
                gate_details["overall_quality"] = {"score": quality_score, "threshold": self.config.min_extraction_quality}
            else:
                failed_gates.append("overall_quality")
                gate_details["overall_quality"] = {"score": quality_score, "threshold": self.config.min_extraction_quality, "gap": self.config.min_extraction_quality - quality_score}
        
        # Gate 2: Minimum AI confidence
        ai_confidence = extraction.get("analysis_confidence", 0.5)
        if ai_confidence >= self.config.min_confidence:
            passed_gates.append("ai_confidence")
            gate_details["ai_confidence"] = {"score": ai_confidence, "threshold": self.config.min_confidence}
        else:
            if ai_confidence < self.config.min_confidence * 0.7:  # Significantly below
                failed_gates.append("ai_confidence")
            else:
                warnings.append(f"Low AI confidence: {ai_confidence:.2f}")
            gate_details["ai_confidence"] = {"score": ai_confidence, "threshold": self.config.min_confidence}
        
        # Gate 3: Hook/title quality
        hook = extraction.get("the_hook", "")
        if self.config.require_hook:
            if not hook or len(hook.strip()) < 3:
                failed_gates.append("hook_required")
                gate_details["hook"] = {"present": False, "length": len(hook) if hook else 0}
            else:
                # Check if hook is navigation text
                if not self.config.allow_navigation_hooks:
                    hook_lower = hook.lower().strip()
                    if hook_lower in self._navigation_terms:
                        failed_gates.append("hook_is_navigation")
                        gate_details["hook"] = {"is_navigation": True, "value": hook}
                    else:
                        passed_gates.append("hook_quality")
                        gate_details["hook"] = {"present": True, "length": len(hook), "is_navigation": False}
                else:
                    passed_gates.append("hook_present")
        
        # Gate 4: Profile name validation
        page_type = extraction.get("page_type", "").lower()
        is_profile = extraction.get("is_individual_profile", False)
        
        if (page_type == "profile" or is_profile) and self.config.enforce_profile_name_validation:
            detected_name = extraction.get("detected_person_name") or hook
            
            if not detected_name:
                failed_gates.append("profile_name_missing")
                gate_details["profile_name"] = {"present": False}
            else:
                # Validate name looks like a person name
                name_valid = self._validate_person_name(detected_name)
                if name_valid:
                    passed_gates.append("profile_name_valid")
                    gate_details["profile_name"] = {"valid": True, "name": detected_name}
                else:
                    failed_gates.append("profile_name_invalid")
                    gate_details["profile_name"] = {"valid": False, "name": detected_name}
        
        # Gate 5: Social proof quality (if present)
        if self.config.require_social_proof_numbers:
            proof = extraction.get("social_proof_found")
            if proof:
                has_numbers = any(char.isdigit() for char in proof)
                if has_numbers:
                    passed_gates.append("social_proof_numbers")
                    gate_details["social_proof"] = {"has_numbers": True, "value": proof}
                else:
                    warnings.append(f"Social proof lacks numbers: '{proof}'")
                    gate_details["social_proof"] = {"has_numbers": False, "value": proof}
        
        # Gate 6: Page classification consistency
        company_indicators = extraction.get("company_indicators", [])
        if (page_type == "profile" or is_profile) and len(company_indicators) > 2:
            failed_gates.append("profile_classification_inconsistent")
            gate_details["classification_consistency"] = {
                "issue": "profile_with_company_indicators",
                "company_indicators": company_indicators
            }
            warnings.append(f"Profile classification inconsistent (has {len(company_indicators)} company indicators)")
        else:
            passed_gates.append("classification_consistency")
        
        # Gate 7: Critical validation issues
        if validation_result and hasattr(validation_result, 'get_critical_issues'):
            critical_issues = validation_result.get_critical_issues()
            if len(critical_issues) > 0:
                failed_gates.append("critical_validation_issues")
                gate_details["validation"] = {
                    "critical_issues": len(critical_issues),
                    "issues": [issue.message for issue in critical_issues[:3]]
                }
            else:
                passed_gates.append("no_critical_issues")
        
        # Determine overall status
        total_gates = len(passed_gates) + len(failed_gates)
        pass_rate = len(passed_gates) / total_gates if total_gates > 0 else 0.0
        
        if len(failed_gates) == 0:
            if len(warnings) == 0:
                status = GateStatus.PASS
            else:
                status = GateStatus.PASS_WITH_WARNINGS
        elif len(failed_gates) <= 2 and pass_rate >= 0.6:
            # Minor failures, can still use
            status = GateStatus.FAIL
        else:
            # Major failures
            status = GateStatus.REJECT
        
        # Determine recommendations
        if status == GateStatus.PASS:
            should_use = True
            should_retry = False
            should_fallback = False
        elif status == GateStatus.PASS_WITH_WARNINGS:
            should_use = True
            should_retry = False
            should_fallback = False
        elif status == GateStatus.FAIL:
            should_use = False
            should_retry = True  # Worth retrying
            should_fallback = False
        else:  # REJECT
            should_use = False
            should_retry = False
            should_fallback = True  # Use fallback immediately
        
        # Log results
        if status == GateStatus.PASS:
            logger.info(f"✅ Quality gates PASSED ({len(passed_gates)}/{total_gates} gates)")
        elif status == GateStatus.PASS_WITH_WARNINGS:
            logger.info(f"⚠️  Quality gates passed with {len(warnings)} warnings")
        elif status == GateStatus.FAIL:
            logger.warning(f"❌ Quality gates FAILED ({len(failed_gates)} gates failed): {', '.join(failed_gates)}")
        else:
            logger.error(f"🚫 Quality gates REJECTED ({len(failed_gates)} critical failures): {', '.join(failed_gates)}")
        
        return QualityGateResult(
            status=status,
            overall_quality_score=quality_score if quality_score is not None else 0.0,
            confidence_score=ai_confidence,
            passed_gates=passed_gates,
            failed_gates=failed_gates,
            warnings=warnings,
            should_use=should_use,
            should_retry=should_retry,
            should_fallback=should_fallback,
            gate_details=gate_details
        )
    
    def _validate_person_name(self, name: str) -> bool:
        """Validate if string looks like a person name."""
        if not name or len(name) < 3:
            return False
        
        words = name.strip().split()
        
        # Names typically 2-4 words
        if len(words) < 2 or len(words) > 5:
            return False
        
        # Names typically < 60 characters
        if len(name) > 60:
            return False
        
        # Most words should be capitalized
        caps_count = sum(1 for w in words if w and w[0].isupper())
        if caps_count < len(words) * 0.6:
            return False
        
        # Check for job title keywords (names don't have these)
        job_keywords = [
            "senior", "junior", "lead", "director", "manager",
            "developer", "designer", "engineer", "architect"
        ]
        name_lower = name.lower()
        if any(keyword in name_lower for keyword in job_keywords):
            return False
        
        return True


def evaluate_quality_gates(
    extraction: Dict[str, Any],
    quality_score: Optional[float] = None,
    validation_result: Optional[Any] = None,
    config: Optional[QualityGateConfig] = None
) -> QualityGateResult:
    """
    Convenience function to evaluate quality gates.
    
    Args:
        extraction: AI extraction result
        quality_score: Quality score (if available)
        validation_result: Validation result (if available)
        config: Quality gate configuration
        
    Returns:
        QualityGateResult
    """
    evaluator = QualityGateEvaluator(config)
    return evaluator.evaluate(extraction, quality_score, validation_result)
