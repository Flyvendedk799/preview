"""
Quality Framework for ensuring consistent quality across all extractions.

This framework provides quality gates that validate content and design
extractions to ensure equal quality regardless of source (HTML, semantic, vision).
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class QualityLevel(str, Enum):
    """Quality levels."""
    EXCELLENT = "excellent"  # 0.9-1.0
    GOOD = "good"  # 0.7-0.9
    FAIR = "fair"  # 0.5-0.7
    POOR = "poor"  # 0.0-0.5


@dataclass
class QualityScore:
    """Quality score for a field."""
    score: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    source: str  # "html", "semantic", "vision"
    issues: List[str]  # Quality issues found
    passed_gates: bool  # Whether passed quality gates
    level: QualityLevel  # Quality level


class QualityGate(ABC):
    """Base class for quality gates."""
    
    @abstractmethod
    def validate(self, content: Any, context: Dict[str, Any]) -> QualityScore:
        """Validate content quality."""
        pass
    
    @abstractmethod
    def get_threshold(self) -> float:
        """Get minimum quality threshold."""
        pass
    
    def _calculate_level(self, score: float) -> QualityLevel:
        """Calculate quality level from score."""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.7:
            return QualityLevel.GOOD
        elif score >= 0.5:
            return QualityLevel.FAIR
        else:
            return QualityLevel.POOR


class ContentQualityGate(QualityGate):
    """Validates content quality."""
    
    GENERIC_PATTERNS = [
        "welcome", "about us", "learn more", "click here",
        "read more", "get started", "sign up", "home page"
    ]
    
    NAV_PATTERNS = [
        "home", "contact", "menu", "navigation", "footer",
        "skip to", "cookie", "privacy policy"
    ]
    
    def validate(self, content: str, context: Dict[str, Any]) -> QualityScore:
        """Validate content quality."""
        issues = []
        score = 1.0
        
        # Check if content exists
        if not content or not isinstance(content, str):
            return QualityScore(
                score=0.0,
                confidence=0.0,
                source=context.get("source", "unknown"),
                issues=["Content is empty or invalid"],
                passed_gates=False,
                level=QualityLevel.POOR
            )
        
        content_lower = content.lower().strip()
        content_length = len(content_lower)
        
        # Check length
        if content_length < 3:
            issues.append("Content too short")
            score -= 0.5
        elif content_length < 10:
            issues.append("Content very short")
            score -= 0.2
        elif content_length > 200:
            # Very long content might be problematic for titles
            if context.get("field") == "title":
                issues.append("Title too long")
                score -= 0.2
        
        # Check for generic content
        for pattern in self.GENERIC_PATTERNS:
            if pattern in content_lower:
                issues.append(f"Generic pattern detected: {pattern}")
                score -= 0.3
                break
        
        # Check for navigation text
        for pattern in self.NAV_PATTERNS:
            if pattern in content_lower and content_length < 30:
                issues.append(f"Navigation text detected: {pattern}")
                score -= 0.2
                break
        
        # Check for excessive capitalization (might be spam)
        if content.isupper() and content_length > 10:
            issues.append("Excessive capitalization")
            score -= 0.1
        
        # Check for only numbers or symbols
        if content_length > 0 and not any(c.isalpha() for c in content):
            issues.append("No alphabetic characters")
            score -= 0.3
        
        # Calculate confidence
        confidence = max(0.0, min(1.0, score))
        
        # Check if passes threshold
        passed = confidence >= self.get_threshold()
        
        return QualityScore(
            score=score,
            confidence=confidence,
            source=context.get("source", "unknown"),
            issues=issues,
            passed_gates=passed,
            level=self._calculate_level(confidence)
        )
    
    def get_threshold(self) -> float:
        return 0.6  # Minimum quality threshold


class DesignQualityGate(QualityGate):
    """Validates design extraction quality."""
    
    def validate(self, design: Dict[str, Any], context: Dict[str, Any]) -> QualityScore:
        """Validate design extraction quality."""
        issues = []
        score = 1.0
        
        # Check color palette
        color_palette = design.get("color_palette", {})
        if not color_palette or not color_palette.get("primary"):
            issues.append("Missing primary color")
            score -= 0.3
        
        # Check if colors are valid hex
        if color_palette.get("primary"):
            primary = color_palette["primary"]
            if not (primary.startswith("#") and len(primary) in [4, 7]):
                issues.append("Invalid primary color format")
                score -= 0.2
        
        # Check secondary color (optional but nice to have)
        if not color_palette.get("secondary"):
            issues.append("Missing secondary color")
            score -= 0.1
        
        # Check typography (optional but nice to have)
        typography = design.get("typography", {})
        if not typography or not typography.get("font_family"):
            issues.append("Missing typography information")
            score -= 0.1  # Less critical
        
        # Check layout structure (optional)
        layout = design.get("layout_structure", {})
        if not layout:
            issues.append("Missing layout structure")
            score -= 0.1  # Less critical
        
        confidence = max(0.0, min(1.0, score))
        passed = confidence >= self.get_threshold()
        
        return QualityScore(
            score=score,
            confidence=confidence,
            source=context.get("source", "unknown"),
            issues=issues,
            passed_gates=passed,
            level=self._calculate_level(confidence)
        )
    
    def get_threshold(self) -> float:
        return 0.5  # Minimum design quality threshold


class CompletenessGate(QualityGate):
    """Validates completeness of extraction."""
    
    def validate(self, result: Dict[str, Any], context: Dict[str, Any]) -> QualityScore:
        """Validate completeness."""
        issues = []
        score = 1.0
        
        required_fields = ["title", "description"]
        optional_fields = ["image", "tags"]
        
        # Check required fields
        for field in required_fields:
            if not result.get(field):
                issues.append(f"Missing required field: {field}")
                score -= 0.4
        
        # Check optional fields
        missing_optional = sum(1 for field in optional_fields if not result.get(field))
        if missing_optional > 0:
            issues.append(f"Missing {missing_optional} optional field(s)")
            score -= 0.1 * missing_optional
        
        confidence = max(0.0, min(1.0, score))
        passed = confidence >= self.get_threshold()
        
        return QualityScore(
            score=score,
            confidence=confidence,
            source=context.get("source", "unknown"),
            issues=issues,
            passed_gates=passed,
            level=self._calculate_level(confidence)
        )
    
    def get_threshold(self) -> float:
        return 0.6  # Must have title and description


class QualityFramework:
    """
    Framework for ensuring consistent quality across all extractions.
    
    This ensures equal quality standards regardless of source (HTML, semantic, vision).
    """
    
    def __init__(self):
        self.content_gate = ContentQualityGate()
        self.design_gate = DesignQualityGate()
        self.completeness_gate = CompletenessGate()
        logger.info("Quality Framework initialized")
    
    def validate_content(
        self,
        title: Optional[str],
        description: Optional[str],
        source: str
    ) -> Dict[str, QualityScore]:
        """Validate content quality."""
        scores = {}
        
        if title:
            scores["title"] = self.content_gate.validate(
                title,
                {"source": source, "field": "title"}
            )
            if scores["title"].issues:
                logger.debug(f"Title quality issues ({source}): {scores['title'].issues}")
        
        if description:
            scores["description"] = self.content_gate.validate(
                description,
                {"source": source, "field": "description"}
            )
            if scores["description"].issues:
                logger.debug(f"Description quality issues ({source}): {scores['description'].issues}")
        
        return scores
    
    def validate_design(
        self,
        design: Dict[str, Any],
        source: str
    ) -> QualityScore:
        """Validate design extraction quality."""
        score = self.design_gate.validate(
            design,
            {"source": source}
        )
        if score.issues:
            logger.debug(f"Design quality issues ({source}): {score.issues}")
        return score
    
    def validate_completeness(
        self,
        result: Dict[str, Any],
        source: str
    ) -> QualityScore:
        """Validate completeness."""
        score = self.completeness_gate.validate(
            result,
            {"source": source}
        )
        if score.issues:
            logger.debug(f"Completeness issues ({source}): {score.issues}")
        return score
    
    def should_use_source(
        self,
        scores: Dict[str, QualityScore]
    ) -> bool:
        """Determine if source should be used based on quality scores."""
        if not scores:
            return False
        
        # All fields must pass quality gates
        return all(score.passed_gates for score in scores.values())
    
    def get_best_source(
        self,
        source_scores: Dict[str, Dict[str, QualityScore]]
    ) -> Optional[str]:
        """
        Get the best source based on quality scores.
        
        Args:
            source_scores: Dict mapping source name to field scores
            
        Returns:
            Best source name or None
        """
        if not source_scores:
            return None
        
        # Calculate average confidence per source
        source_confidences = {}
        for source, scores in source_scores.items():
            if scores:
                avg_confidence = sum(s.confidence for s in scores.values()) / len(scores)
                source_confidences[source] = avg_confidence
        
        if not source_confidences:
            return None
        
        # Return source with highest average confidence
        best_source = max(source_confidences.items(), key=lambda x: x[1])
        return best_source[0]
