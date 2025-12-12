"""
Quality Orchestrator - Central Quality Control System

Coordinates all quality checks and enforces quality gates before previews are returned.
This is the single source of truth for quality validation in the preview generation pipeline.

RESPONSIBILITIES:
1. Coordinate quality assessment across all systems
2. Enforce quality gates before preview is returned
3. Trigger automatic improvements when quality is below threshold
4. Provide unified quality metrics and reporting
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Quality system imports
try:
    from backend.services.quality_assurance_engine import QualityAssuranceEngine, QualityScore
    QUALITY_ASSURANCE_AVAILABLE = True
except ImportError:
    QUALITY_ASSURANCE_AVAILABLE = False
    logger.warning("QualityAssuranceEngine not available")

try:
    from backend.services.design_fidelity_validator import (
        validate_design_fidelity,
        DesignFidelityResult
    )
    DESIGN_FIDELITY_AVAILABLE = True
except ImportError:
    DESIGN_FIDELITY_AVAILABLE = False
    logger.warning("DesignFidelityValidator not available")

try:
    from backend.services.extraction_quality_scorer import (
        ExtractionQualityScorer,
        score_extraction_quality
    )
    EXTRACTION_QUALITY_AVAILABLE = True
except ImportError:
    EXTRACTION_QUALITY_AVAILABLE = False
    logger.warning("ExtractionQualityScorer not available")

try:
    from backend.services.quality_gates import (
        QualityGateEvaluator,
        QualityGateConfig,
        evaluate_quality_gates,
        GateStatus
    )
    QUALITY_GATES_AVAILABLE = True
except ImportError:
    QUALITY_GATES_AVAILABLE = False
    logger.warning("QualityGates not available")


class QualityLevel(str, Enum):
    """Quality level classification."""
    EXCELLENT = "excellent"  # >= 0.90
    GOOD = "good"  # >= 0.75
    FAIR = "fair"  # >= 0.60
    POOR = "poor"  # < 0.60


class QualityTier(str, Enum):
    """
    PHASE 5: Graduated quality tier system.
    
    Instead of binary pass/fail, this system uses tiers to make
    more nuanced decisions about preview quality and actions.
    """
    PREMIUM = "premium"       # >= 0.85 - Use as-is, no improvements needed
    STANDARD = "standard"     # >= 0.70 - Use with minor enhancements
    ACCEPTABLE = "acceptable" # >= 0.55 - Use with warnings, suggest improvements
    RETRY = "retry"           # >= 0.40 - Retry with different extraction
    FALLBACK = "fallback"     # < 0.40 - Use smart fallback instead


@dataclass
class UnifiedQualityMetrics:
    """Unified quality metrics from all systems."""
    # Overall scores
    overall_quality_score: float  # 0.0-1.0
    design_fidelity_score: float  # 0.0-1.0
    extraction_quality_score: float  # 0.0-1.0
    visual_quality_score: float  # 0.0-1.0
    
    # Quality level
    quality_level: QualityLevel
    
    # PHASE 5: Quality tier for graduated decisions
    quality_tier: QualityTier = QualityTier.STANDARD
    
    # Gate status
    gate_status: GateStatus = GateStatus.PASS
    
    # Detailed scores
    quality_assurance_score: Optional[QualityScore] = None
    design_fidelity_result: Optional[DesignFidelityResult] = None
    
    # Issues and suggestions
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    # Recommendations
    should_use: bool = True
    should_retry: bool = False
    should_improve: bool = False
    
    # PHASE 5: Enhanced recommendations
    recommended_action: str = "use"  # use, enhance, retry, fallback
    enhancement_priority: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/API."""
        result = {
            "overall_quality_score": self.overall_quality_score,
            "design_fidelity_score": self.design_fidelity_score,
            "extraction_quality_score": self.extraction_quality_score,
            "visual_quality_score": self.visual_quality_score,
            "quality_level": self.quality_level.value,
            "quality_tier": self.quality_tier.value,
            "gate_status": self.gate_status.value,
            "should_use": self.should_use,
            "should_retry": self.should_retry,
            "should_improve": self.should_improve,
            "recommended_action": self.recommended_action,
            "enhancement_priority": self.enhancement_priority,
            "issues": self.issues,
            "suggestions": self.suggestions
        }
        
        if self.quality_assurance_score:
            result["quality_assurance"] = {
                "overall": self.quality_assurance_score.overall,
                "grade": self.quality_assurance_score.grade,
                "accessibility": self.quality_assurance_score.accessibility,
                "visual_balance": self.quality_assurance_score.visual_balance,
                "typography": self.quality_assurance_score.typography,
                "brand_fidelity": self.quality_assurance_score.brand_fidelity,
                "technical": self.quality_assurance_score.technical
            }
        
        if self.design_fidelity_result:
            result["design_fidelity"] = self.design_fidelity_result.to_dict()
        
        return result
    
    def get_tier_action(self) -> str:
        """Get recommended action based on quality tier."""
        tier_actions = {
            QualityTier.PREMIUM: "use",
            QualityTier.STANDARD: "use",
            QualityTier.ACCEPTABLE: "use_with_warning",
            QualityTier.RETRY: "retry",
            QualityTier.FALLBACK: "fallback"
        }
        return tier_actions.get(self.quality_tier, "use")


class QualityOrchestrator:
    """
    Central quality control system that coordinates all quality checks.
    
    This orchestrator:
    1. Runs all quality assessments in parallel where possible
    2. Aggregates results into unified metrics
    3. Enforces quality gates
    4. Triggers improvements when needed
    5. Provides comprehensive quality reporting
    """
    
    def __init__(
        self,
        min_quality_threshold: float = 0.65,  # High standards - improve quality, not lower bar
        min_design_fidelity: float = 0.50,    # Reasonable fidelity requirement
        enable_auto_improvement: bool = True
    ):
        """
        Initialize quality orchestrator.
        
        Args:
            min_quality_threshold: Minimum overall quality score (0.0-1.0)
            min_design_fidelity: Minimum design fidelity score (0.0-1.0)
            enable_auto_improvement: Whether to trigger automatic improvements
        """
        self.min_quality_threshold = min_quality_threshold
        self.min_design_fidelity = min_design_fidelity
        self.enable_auto_improvement = enable_auto_improvement
        
        # Initialize quality engines
        self.quality_assurance_engine = None
        if QUALITY_ASSURANCE_AVAILABLE:
            self.quality_assurance_engine = QualityAssuranceEngine()
        
        self.quality_gate_evaluator = None
        if QUALITY_GATES_AVAILABLE:
            self.quality_gate_evaluator = QualityGateEvaluator()
        
        logger.info(
            f"Quality Orchestrator initialized: "
            f"min_quality={min_quality_threshold}, "
            f"min_fidelity={min_design_fidelity}, "
            f"auto_improvement={enable_auto_improvement}"
        )
    
    def assess_quality(
        self,
        preview_result: Dict[str, Any],
        preview_image: Optional[Any] = None,  # PIL Image
        design_dna: Optional[Dict[str, Any]] = None,
        brand_colors: Optional[Dict[str, Any]] = None
    ) -> UnifiedQualityMetrics:
        """
        Comprehensive quality assessment across all systems.
        
        Args:
            preview_result: Preview generation result with content, blueprint, etc.
            preview_image: Generated preview image (PIL Image)
            design_dna: Original design DNA
            brand_colors: Original brand colors
            
        Returns:
            UnifiedQualityMetrics with all quality assessments
        """
        logger.info("🔍 Starting comprehensive quality assessment")
        
        # Initialize metrics
        extraction_quality_score = 0.0
        visual_quality_score = 0.0
        design_fidelity_score = 0.0
        quality_assurance_score = None
        design_fidelity_result = None
        gate_status = GateStatus.PASS
        issues = []
        suggestions = []
        
        # 1. Extraction Quality Assessment
        if EXTRACTION_QUALITY_AVAILABLE:
            try:
                quality_breakdown = score_extraction_quality(preview_result)
                extraction_quality_score = quality_breakdown.overall_score
                logger.info(f"📊 Extraction quality: {extraction_quality_score:.2f}")
            except Exception as e:
                logger.warning(f"Extraction quality assessment failed: {e}")
        
        # 2. Visual Quality Assessment (if image provided)
        if preview_image and self.quality_assurance_engine:
            try:
                design_data = {
                    "colors": preview_result.get("blueprint", {}),
                    "typography": preview_result.get("blueprint", {}),
                    "layout": preview_result.get("blueprint", {})
                }
                
                quality_assurance_score = self.quality_assurance_engine.assess_quality(
                    preview_image,
                    design_data,
                    brand_colors
                )
                visual_quality_score = quality_assurance_score.overall
                issues.extend(quality_assurance_score.issues)
                suggestions.extend(quality_assurance_score.suggestions)
                logger.info(f"📊 Visual quality: {visual_quality_score:.2f} (Grade: {quality_assurance_score.grade})")
            except Exception as e:
                logger.warning(f"Visual quality assessment failed: {e}")
        
        # 3. Design Fidelity Assessment (if DNA provided)
        if design_dna and DESIGN_FIDELITY_AVAILABLE:
            try:
                preview_config = preview_result.get("blueprint", {})
                preview_content = {
                    "has_logo": bool(preview_result.get("primary_image_base64")),
                    "template_style": preview_config.get("template_type", "landing")
                }
                
                design_fidelity_result = validate_design_fidelity(
                    design_dna,
                    preview_config,
                    preview_content
                )
                design_fidelity_score = design_fidelity_result.overall_score
                suggestions.extend(design_fidelity_result.improvement_priority)
                logger.info(f"📊 Design fidelity: {design_fidelity_score:.2f} ({design_fidelity_result.verdict})")
            except Exception as e:
                logger.warning(f"Design fidelity assessment failed: {e}")
        
        # 4. Quality Gate Evaluation
        if self.quality_gate_evaluator:
            try:
                gate_config = QualityGateConfig(
                    min_extraction_quality=self.min_quality_threshold,
                    min_confidence=preview_result.get("reasoning_confidence", 0.5)
                )
                
                gate_result = evaluate_quality_gates(
                    preview_result,
                    extraction_quality_score,
                    None,  # validation_result - could be enhanced
                    gate_config
                )
                gate_status = gate_result.status
                
                if gate_result.failed_gates:
                    issues.extend([f"Gate failed: {gate}" for gate in gate_result.failed_gates])
                
                logger.info(f"📊 Quality gate: {gate_status.value}")
            except Exception as e:
                logger.warning(f"Quality gate evaluation failed: {e}")
        
        # 5. Calculate overall quality score (weighted average)
        weights = {
            "extraction": 0.30,
            "visual": 0.25,
            "design_fidelity": 0.25,
            "gate": 0.20
        }
        
        # Gate score (pass=1.0, pass_with_warnings=0.8, fail=0.5, reject=0.0)
        gate_score = {
            GateStatus.PASS: 1.0,
            GateStatus.PASS_WITH_WARNINGS: 0.8,
            GateStatus.FAIL: 0.5,
            GateStatus.REJECT: 0.0
        }.get(gate_status, 0.5)
        
        overall_quality_score = (
            extraction_quality_score * weights["extraction"] +
            visual_quality_score * weights["visual"] +
            design_fidelity_score * weights["design_fidelity"] +
            gate_score * weights["gate"]
        )
        
        # Determine quality level
        if overall_quality_score >= 0.90:
            quality_level = QualityLevel.EXCELLENT
        elif overall_quality_score >= 0.75:
            quality_level = QualityLevel.GOOD
        elif overall_quality_score >= 0.60:
            quality_level = QualityLevel.FAIR
        else:
            quality_level = QualityLevel.POOR
        
        # PHASE 5: Determine quality tier (graduated system)
        if overall_quality_score >= 0.85:
            quality_tier = QualityTier.PREMIUM
        elif overall_quality_score >= 0.70:
            quality_tier = QualityTier.STANDARD
        elif overall_quality_score >= 0.55:
            quality_tier = QualityTier.ACCEPTABLE
        elif overall_quality_score >= 0.40:
            quality_tier = QualityTier.RETRY
        else:
            quality_tier = QualityTier.FALLBACK
        
        # PHASE 5: Determine recommended action based on tier
        tier_to_action = {
            QualityTier.PREMIUM: "use",
            QualityTier.STANDARD: "use",
            QualityTier.ACCEPTABLE: "enhance",
            QualityTier.RETRY: "retry",
            QualityTier.FALLBACK: "fallback"
        }
        recommended_action = tier_to_action.get(quality_tier, "use")
        
        # Determine recommendations (enhanced logic)
        should_use = quality_tier in [QualityTier.PREMIUM, QualityTier.STANDARD, QualityTier.ACCEPTABLE]
        should_retry = quality_tier == QualityTier.RETRY
        should_improve = quality_tier in [QualityTier.ACCEPTABLE, QualityTier.RETRY]
        
        # Build enhancement priority
        enhancement_priority = []
        if design_fidelity_score < 0.70:
            enhancement_priority.append("design_fidelity")
        if extraction_quality_score < 0.70:
            enhancement_priority.append("content_extraction")
        if visual_quality_score < 0.70:
            enhancement_priority.append("visual_quality")
        if not preview_result.get("primary_image_base64"):
            enhancement_priority.append("logo_extraction")
        
        metrics = UnifiedQualityMetrics(
            overall_quality_score=overall_quality_score,
            design_fidelity_score=design_fidelity_score,
            extraction_quality_score=extraction_quality_score,
            visual_quality_score=visual_quality_score,
            quality_level=quality_level,
            quality_tier=quality_tier,
            gate_status=gate_status,
            quality_assurance_score=quality_assurance_score,
            design_fidelity_result=design_fidelity_result,
            issues=issues,
            suggestions=suggestions,
            should_use=should_use,
            should_retry=should_retry,
            should_improve=should_improve,
            recommended_action=recommended_action,
            enhancement_priority=enhancement_priority
        )
        
        logger.info(
            f"✅ Quality assessment complete: "
            f"Overall={overall_quality_score:.2f} ({quality_level.value}), "
            f"Tier={quality_tier.value}, "
            f"Action={recommended_action}, "
            f"Gate={gate_status.value}"
        )
        
        return metrics
    
    def enforce_quality_gates(
        self,
        metrics: UnifiedQualityMetrics
    ) -> bool:
        """
        PHASE 5: Enforce quality gates with graduated tier system.
        
        Instead of strict pass/fail, uses tiers to allow "good enough" previews
        to pass with warnings while still blocking truly poor quality.
        
        Args:
            metrics: Quality metrics from assess_quality
            
        Returns:
            True if preview passes gates (PREMIUM, STANDARD, or ACCEPTABLE tier)
        """
        # PHASE 5: Use tier system for more nuanced decisions
        
        # PREMIUM and STANDARD always pass
        if metrics.quality_tier in [QualityTier.PREMIUM, QualityTier.STANDARD]:
            logger.info(f"✅ Quality gates passed: {metrics.quality_tier.value}")
            return True
        
        # ACCEPTABLE passes with warnings
        if metrics.quality_tier == QualityTier.ACCEPTABLE:
            logger.warning(
                f"⚠️ Quality gates passed with warnings: "
                f"score={metrics.overall_quality_score:.2f}, "
                f"tier={metrics.quality_tier.value}"
            )
            return True
        
        # RETRY tier - check if we should allow with severe warnings
        if metrics.quality_tier == QualityTier.RETRY:
            # If design fidelity is good but extraction is weak, allow with warning
            if metrics.design_fidelity_score >= 0.60:
                logger.warning(
                    f"⚠️ Quality gates passed (design OK): "
                    f"score={metrics.overall_quality_score:.2f}, "
                    f"fidelity={metrics.design_fidelity_score:.2f}"
                )
                return True
            
            logger.warning(
                f"❌ Quality gate failed - retry recommended: "
                f"score={metrics.overall_quality_score:.2f}"
            )
            return False
        
        # FALLBACK tier - never passes, use smart fallback
        if metrics.quality_tier == QualityTier.FALLBACK:
            logger.warning(
                f"❌ Quality gate failed - fallback required: "
                f"score={metrics.overall_quality_score:.2f}"
            )
            return False
        
        # Legacy threshold checks for backward compatibility
        if metrics.gate_status == GateStatus.REJECT:
            logger.warning("❌ Quality gate rejected by gate evaluator")
            return False
        
        logger.info("✅ Quality gates passed")
        return True
    
    def get_smart_fallback_colors(
        self,
        brand_colors: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        PHASE 5: Get smart fallback colors that use brand colors instead of generic.
        
        When quality gates fail, we still want the fallback to look branded.
        
        Args:
            brand_colors: Extracted brand colors
            
        Returns:
            Color palette for fallback preview
        """
        # Default branded fallback (MetaView orange theme)
        fallback_colors = {
            "primary_color": "#F97316",  # MetaView orange
            "secondary_color": "#1E293B",  # Dark gray
            "accent_color": "#FBBF24",  # Amber
            "background_color": "#0F172A",  # Dark blue-gray
            "text_color": "#FFFFFF"
        }
        
        # If brand colors are available, use them
        if brand_colors:
            if brand_colors.get("primary_color"):
                fallback_colors["primary_color"] = brand_colors["primary_color"]
            if brand_colors.get("secondary_color"):
                fallback_colors["secondary_color"] = brand_colors["secondary_color"]
            if brand_colors.get("accent_color"):
                fallback_colors["accent_color"] = brand_colors["accent_color"]
        
        return fallback_colors
    
    def get_tier_specific_enhancements(
        self,
        metrics: UnifiedQualityMetrics
    ) -> List[str]:
        """
        PHASE 5: Get tier-specific enhancement actions.
        
        Returns specific actions to take based on quality tier.
        
        Args:
            metrics: Quality metrics
            
        Returns:
            List of enhancement actions
        """
        enhancements = []
        
        if metrics.quality_tier == QualityTier.PREMIUM:
            # Already premium - no enhancements needed
            return []
        
        if metrics.quality_tier == QualityTier.STANDARD:
            # Minor enhancements
            if metrics.design_fidelity_score < 0.80:
                enhancements.append("apply_stronger_brand_colors")
            if not metrics.enhancement_priority or "logo_extraction" in metrics.enhancement_priority:
                enhancements.append("verify_logo_present")
        
        if metrics.quality_tier == QualityTier.ACCEPTABLE:
            # Moderate enhancements
            enhancements.append("enhance_content_extraction")
            if metrics.design_fidelity_score < 0.60:
                enhancements.append("reapply_design_dna")
            if metrics.visual_quality_score < 0.60:
                enhancements.append("improve_layout_balance")
        
        if metrics.quality_tier == QualityTier.RETRY:
            # Major enhancements via retry
            enhancements.append("retry_with_enhanced_extraction")
            enhancements.append("use_ai_logo_detection")
            enhancements.append("apply_full_design_dna")
        
        if metrics.quality_tier == QualityTier.FALLBACK:
            # Fallback actions
            enhancements.append("use_smart_fallback")
            enhancements.append("use_brand_colors_only")
        
        return enhancements
    
    def get_improvement_suggestions(
        self,
        metrics: UnifiedQualityMetrics
    ) -> List[str]:
        """
        Get prioritized improvement suggestions.
        
        Args:
            metrics: Quality metrics
            
        Returns:
            List of improvement suggestions, prioritized
        """
        suggestions = []
        
        # Add suggestions from quality assurance
        if metrics.quality_assurance_score:
            suggestions.extend(metrics.quality_assurance_score.suggestions)
        
        # Add suggestions from design fidelity
        if metrics.design_fidelity_result:
            suggestions.extend(metrics.design_fidelity_result.improvement_priority)
        
        # Add general suggestions based on scores
        if metrics.overall_quality_score < 0.75:
            suggestions.append("Overall quality below threshold - consider retry with enhanced extraction")
        
        if metrics.design_fidelity_score < 0.70:
            suggestions.append("Design fidelity below threshold - ensure Design DNA is properly extracted and applied")
        
        if metrics.extraction_quality_score < 0.70:
            suggestions.append("Extraction quality below threshold - verify content extraction accuracy")
        
        if metrics.visual_quality_score < 0.70:
            suggestions.append("Visual quality below threshold - review layout, typography, and color choices")
        
        return suggestions

