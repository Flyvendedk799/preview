"""
Content Quality Validator - Validates Extracted Content Quality

Validates content quality before it's used in previews:
- Title quality (specificity, clarity, length)
- Description quality (value, clarity, length)
- Content completeness
- Relevance scoring
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ContentQualityScore:
    """Quality score for content."""
    score: float  # 0.0-1.0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    passed: bool = False


@dataclass
class ContentQualityReport:
    """Complete quality report for extracted content."""
    title_score: ContentQualityScore
    description_score: ContentQualityScore
    overall_score: float
    passed: bool
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class ContentQualityValidator:
    """
    Validates content quality before use in previews.
    
    Checks:
    - Title specificity and clarity
    - Description value and clarity
    - Content completeness
    - Relevance
    """
    
    def __init__(self):
        """Initialize content quality validator."""
        self.logger = logging.getLogger(__name__)
        
        # Quality thresholds
        self.min_title_length = 10
        self.max_title_length = 100
        self.min_description_length = 50
        self.max_description_length = 300
        self.min_quality_score = 0.60
    
    def validate_content(
        self,
        title: Optional[str],
        description: Optional[str],
        tags: Optional[List[str]] = None
    ) -> ContentQualityReport:
        """
        Validate content quality.
        
        Args:
            title: Title text
            description: Description text
            tags: Optional tags
            
        Returns:
            ContentQualityReport with scores and feedback
        """
        # Validate title
        title_score = self._validate_title(title)
        
        # Validate description
        description_score = self._validate_description(description, title)
        
        # Calculate overall score
        overall_score = (title_score.score * 0.6 + description_score.score * 0.4)
        
        # Determine if passed
        passed = (
            overall_score >= self.min_quality_score and
            title_score.passed and
            description_score.passed
        )
        
        # Collect all issues and suggestions
        issues = title_score.issues + description_score.issues
        suggestions = title_score.suggestions + description_score.suggestions
        
        report = ContentQualityReport(
            title_score=title_score,
            description_score=description_score,
            overall_score=overall_score,
            passed=passed,
            issues=issues,
            suggestions=suggestions
        )
        
        self.logger.info(
            f"Content quality validation: overall={overall_score:.2f}, "
            f"passed={passed}, issues={len(issues)}"
        )
        
        return report
    
    def _validate_title(
        self,
        title: Optional[str]
    ) -> ContentQualityScore:
        """
        Validate title quality.
        
        Args:
            title: Title text
            
        Returns:
            ContentQualityScore
        """
        issues = []
        suggestions = []
        score = 0.0
        
        if not title:
            issues.append("Title is missing")
            suggestions.append("Extract title from HTML metadata or page content")
            return ContentQualityScore(score=0.0, issues=issues, suggestions=suggestions, passed=False)
        
        title = title.strip()
        
        # Check length
        if len(title) < self.min_title_length:
            issues.append(f"Title too short ({len(title)} chars, min {self.min_title_length})")
            suggestions.append("Extract more complete title from page")
            score -= 0.2
        elif len(title) > self.max_title_length:
            issues.append(f"Title too long ({len(title)} chars, max {self.max_title_length})")
            suggestions.append("Truncate title to optimal length")
            score -= 0.1
        
        # Check for generic words
        generic_words = ["untitled", "home", "page", "welcome", "index"]
        if any(word in title.lower() for word in generic_words):
            issues.append("Title contains generic words")
            suggestions.append("Extract more specific title from page content")
            score -= 0.3
        
        # Check for specificity (has numbers, specific terms)
        has_numbers = any(c.isdigit() for c in title)
        has_specific_terms = len(title.split()) >= 3
        
        if has_numbers:
            score += 0.1
        if has_specific_terms:
            score += 0.1
        
        # Base score
        score = max(0.0, min(1.0, 0.7 + score))
        
        passed = score >= self.min_quality_score and len(issues) == 0
        
        return ContentQualityScore(
            score=score,
            issues=issues,
            suggestions=suggestions,
            passed=passed
        )
    
    def _validate_description(
        self,
        description: Optional[str],
        title: Optional[str] = None
    ) -> ContentQualityScore:
        """
        Validate description quality.
        
        Args:
            description: Description text
            title: Optional title for comparison
            
        Returns:
            ContentQualityScore
        """
        issues = []
        suggestions = []
        score = 0.0
        
        if not description:
            issues.append("Description is missing")
            suggestions.append("Extract description from HTML metadata or page content")
            return ContentQualityScore(score=0.0, issues=issues, suggestions=suggestions, passed=False)
        
        description = description.strip()
        
        # Check length
        if len(description) < self.min_description_length:
            issues.append(f"Description too short ({len(description)} chars, min {self.min_description_length})")
            suggestions.append("Extract more complete description from page")
            score -= 0.3
        elif len(description) > self.max_description_length:
            issues.append(f"Description too long ({len(description)} chars, max {self.max_description_length})")
            suggestions.append("Truncate description to optimal length")
            score -= 0.1
        
        # Check if description is just repeating title
        if title and description.lower() == title.lower():
            issues.append("Description is identical to title")
            suggestions.append("Extract unique description from page content")
            score -= 0.4
        
        # Check for value (specific claims, numbers, benefits)
        has_numbers = any(c.isdigit() for c in description)
        has_specific_claims = len(description.split()) >= 10
        
        if has_numbers:
            score += 0.1
        if has_specific_claims:
            score += 0.1
        
        # Base score
        score = max(0.0, min(1.0, 0.6 + score))
        
        passed = score >= self.min_quality_score and len(issues) == 0
        
        return ContentQualityScore(
            score=score,
            issues=issues,
            suggestions=suggestions,
            passed=passed
        )

