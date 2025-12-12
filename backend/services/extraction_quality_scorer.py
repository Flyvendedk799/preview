"""
Extraction Quality Scoring Module

Scores AI extraction results for quality to enable:
- Retry decisions (low quality → retry)
- A/B testing comparisons
- Quality monitoring and alerts
- Progressive improvement tracking

SCORING DIMENSIONS:
1. Hook quality (compelling, specific, not generic)
2. Social proof quality (has numbers, credible)
3. Benefit quality (specific, quantified)
4. Completeness (all expected fields present)
5. Consistency (no contradictions)
6. Specificity (numbers, names, details)

OUTPUT: Quality score (0.0-1.0) + detailed breakdown
"""

import re
import logging
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class QualityGrade(str, Enum):
    """Quality grade levels."""
    EXCELLENT = "A"    # 0.90-1.0 - Exceptional, use immediately
    GOOD = "B"         # 0.75-0.89 - Good quality, use with confidence
    ACCEPTABLE = "C"   # 0.60-0.74 - Acceptable, minor issues
    POOR = "D"         # 0.40-0.59 - Poor quality, consider retry
    FAILING = "F"      # 0.0-0.39 - Failed, must retry or use fallback


@dataclass
class QualityBreakdown:
    """Detailed quality score breakdown."""
    overall_score: float  # 0.0-1.0
    grade: QualityGrade
    
    # Component scores
    hook_score: float = 0.0
    social_proof_score: float = 0.0
    benefit_score: float = 0.0
    completeness_score: float = 0.0
    consistency_score: float = 0.0
    specificity_score: float = 0.0
    
    # Flags
    has_numbers: bool = False
    has_specific_claims: bool = False
    is_generic: bool = False
    has_contradictions: bool = False
    
    # Detailed feedback
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    def should_retry(self) -> bool:
        """Determine if extraction should be retried due to poor quality."""
        return self.overall_score < 0.60 or self.grade in [QualityGrade.POOR, QualityGrade.FAILING]


class ExtractionQualityScorer:
    """
    Score extraction quality to enable retry decisions and quality monitoring.
    
    Higher score = better extraction quality = more likely to convert users
    """
    
    def __init__(self):
        self._generic_phrases = self._build_generic_blacklist()
        self._positive_indicators = self._build_positive_indicators()
    
    def score_extraction(self, result: Dict[str, Any]) -> QualityBreakdown:
        """
        Score extraction quality across all dimensions.
        
        Args:
            result: AI extraction result dictionary
            
        Returns:
            QualityBreakdown with scores and recommendations
        """
        # Score individual components
        hook_score = self._score_hook(result)
        social_proof_score = self._score_social_proof(result)
        benefit_score = self._score_benefit(result)
        completeness_score = self._score_completeness(result)
        consistency_score = self._score_consistency(result)
        specificity_score = self._score_specificity(result)
        
        # Calculate weighted overall score
        # Hook is most important (40%), then proof (25%), then rest
        overall_score = (
            hook_score * 0.40 +
            social_proof_score * 0.25 +
            benefit_score * 0.15 +
            completeness_score * 0.10 +
            consistency_score * 0.05 +
            specificity_score * 0.05
        )
        
        # Determine grade
        if overall_score >= 0.90:
            grade = QualityGrade.EXCELLENT
        elif overall_score >= 0.75:
            grade = QualityGrade.GOOD
        elif overall_score >= 0.60:
            grade = QualityGrade.ACCEPTABLE
        elif overall_score >= 0.40:
            grade = QualityGrade.POOR
        else:
            grade = QualityGrade.FAILING
        
        # Analyze flags
        hook = result.get("the_hook", "")
        proof = result.get("social_proof_found", "") or ""
        benefit = result.get("key_benefit", "") or ""
        all_text = f"{hook} {proof} {benefit}"
        
        has_numbers = any(char.isdigit() for char in all_text)
        is_generic = self._is_generic_content(hook)
        has_specific_claims = self._has_specific_claims(all_text)
        has_contradictions = self._check_contradictions(result)
        
        # Generate feedback
        strengths = []
        weaknesses = []
        suggestions = []
        
        if hook_score >= 0.8:
            strengths.append(f"Strong hook: '{hook[:50]}...'")
        elif hook_score < 0.5:
            weaknesses.append(f"Weak hook: '{hook[:50]}...'")
            suggestions.append("Find more compelling, specific headline")
        
        if social_proof_score >= 0.7:
            strengths.append("Good social proof with numbers")
        elif proof:
            weaknesses.append("Social proof lacks specificity")
            suggestions.append("Include specific numbers/metrics")
        
        if has_numbers:
            strengths.append("Contains specific numbers")
        else:
            weaknesses.append("Lacks specific numbers")
            suggestions.append("Add quantifiable metrics")
        
        if is_generic:
            weaknesses.append("Contains generic phrases")
            suggestions.append("Replace generic claims with specific value")
        
        if has_contradictions:
            weaknesses.append("Has inconsistent information")
            suggestions.append("Verify page type and classifications")
        
        # Build result
        breakdown = QualityBreakdown(
            overall_score=overall_score,
            grade=grade,
            hook_score=hook_score,
            social_proof_score=social_proof_score,
            benefit_score=benefit_score,
            completeness_score=completeness_score,
            consistency_score=consistency_score,
            specificity_score=specificity_score,
            has_numbers=has_numbers,
            has_specific_claims=has_specific_claims,
            is_generic=is_generic,
            has_contradictions=has_contradictions,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions
        )
        
        # Log score
        if grade == QualityGrade.EXCELLENT:
            logger.info(f"✨ Excellent extraction quality: {overall_score:.2f} (Grade {grade.value})")
        elif grade in [QualityGrade.GOOD, QualityGrade.ACCEPTABLE]:
            logger.info(f"✓ {grade.name.capitalize()} extraction quality: {overall_score:.2f} (Grade {grade.value})")
        else:
            logger.warning(f"⚠️  {grade.name.capitalize()} extraction quality: {overall_score:.2f} (Grade {grade.value}) - Consider retry")
        
        return breakdown
    
    def _score_hook(self, result: Dict[str, Any]) -> float:
        """Score hook/title quality (0.0-1.0)."""
        hook = result.get("the_hook", "")
        
        if not hook:
            return 0.0
        
        score = 0.5  # Base score for having something
        
        # Length check (ideal 10-80 chars)
        length = len(hook.strip())
        if 10 <= length <= 80:
            score += 0.2
        elif 5 <= length < 10 or 80 < length <= 120:
            score += 0.1
        elif length < 5:
            score -= 0.3
        
        # Has numbers (specificity bonus)
        if any(char.isdigit() for char in hook):
            score += 0.15
        
        # Not generic
        if not self._is_generic_content(hook):
            score += 0.15
        else:
            score -= 0.2  # Penalty for generic
        
        # Not navigation
        hook_lower = hook.lower().strip()
        nav_terms = {"home", "about", "contact", "welcome", "menu"}
        if hook_lower in nav_terms:
            score -= 0.4  # Heavy penalty
        
        # Has action words or benefits
        action_words = ["save", "get", "reduce", "increase", "improve", "faster", "better", "easier"]
        if any(word in hook_lower for word in action_words):
            score += 0.10
        
        return max(0.0, min(1.0, score))
    
    def _score_social_proof(self, result: Dict[str, Any]) -> float:
        """Score social proof quality (0.0-1.0)."""
        proof = result.get("social_proof_found")
        
        if not proof:
            # Not having proof is neutral (not bad, just not bonus)
            return 0.5
        
        score = 0.6  # Base score for having proof
        
        # Has numbers (critical for proof)
        if any(char.isdigit() for char in proof):
            score += 0.30  # Major bonus
            
            # Bonus for star ratings
            if "★" in proof or "star" in proof.lower():
                score += 0.05
            
            # Bonus for review counts
            if "review" in proof.lower():
                score += 0.05
        else:
            score -= 0.20  # Penalty for no numbers
        
        # Has specific claims
        specific_indicators = ["from", "by", "rated", "users", "customers", "companies"]
        if any(ind in proof.lower() for ind in specific_indicators):
            score += 0.10
        
        return max(0.0, min(1.0, score))
    
    def _score_benefit(self, result: Dict[str, Any]) -> float:
        """Score key benefit quality (0.0-1.0)."""
        benefit = result.get("key_benefit")
        
        if not benefit:
            # Not having benefit is OK (not all pages have clear benefit)
            return 0.5
        
        score = 0.5  # Base score
        
        # Length check
        if len(benefit) > 10:
            score += 0.15
        
        # Has numbers (quantified benefit)
        if any(char.isdigit() for char in benefit):
            score += 0.20
        
        # Not generic
        generic_benefits = ["easy to use", "powerful", "great", "simple", "fast"]
        if not any(gen in benefit.lower() for gen in generic_benefits):
            score += 0.15
        
        return max(0.0, min(1.0, score))
    
    def _score_completeness(self, result: Dict[str, Any]) -> float:
        """Score completeness of extraction (0.0-1.0)."""
        score = 0.0
        
        # Check key fields
        if result.get("the_hook"):
            score += 0.40  # Hook is critical
        
        if result.get("page_type"):
            score += 0.20
        
        if result.get("social_proof_found"):
            score += 0.15
        
        if result.get("key_benefit"):
            score += 0.10
        
        if result.get("detected_palette"):
            score += 0.10
        
        if result.get("analysis_confidence", 0.0) > 0.5:
            score += 0.05
        
        return min(1.0, score)
    
    def _score_consistency(self, result: Dict[str, Any]) -> float:
        """Score internal consistency (0.0-1.0)."""
        score = 1.0  # Start perfect, deduct for issues
        
        page_type = result.get("page_type", "").lower()
        is_profile = result.get("is_individual_profile", False)
        company_indicators = result.get("company_indicators", [])
        
        # Check profile consistency
        if page_type == "profile" and not is_profile:
            score -= 0.3
        
        if is_profile and len(company_indicators) > 2:
            score -= 0.4  # Major inconsistency
        
        if page_type not in ["profile", "personal"] and is_profile:
            score -= 0.3
        
        return max(0.0, score)
    
    def _score_specificity(self, result: Dict[str, Any]) -> float:
        """Score overall specificity (0.0-1.0)."""
        hook = result.get("the_hook", "")
        proof = result.get("social_proof_found", "") or ""
        benefit = result.get("key_benefit", "") or ""
        all_text = f"{hook} {proof} {benefit}"
        
        score = 0.0
        
        # Has numbers
        if any(char.isdigit() for char in all_text):
            score += 0.40
        
        # Has proper nouns (capitalized words, likely brands/names)
        words = all_text.split()
        proper_nouns = sum(1 for w in words if w and len(w) > 1 and w[0].isupper() and w[1:].islower())
        if proper_nouns >= 2:
            score += 0.30
        
        # Has percentages or units
        if "%" in all_text or any(unit in all_text.lower() for unit in ["hours", "days", "months", "dollars", "$", "€", "£"]):
            score += 0.20
        
        # Has comparatives (faster, better, more)
        if any(comp in all_text.lower() for comp in ["faster", "better", "more", "less", "than", "vs"]):
            score += 0.10
        
        return min(1.0, score)
    
    def _is_generic_content(self, text: str) -> bool:
        """Check if text is generic/vague."""
        text_lower = text.lower().strip()
        
        for generic in self._generic_phrases:
            if generic in text_lower:
                return True
        
        return False
    
    def _has_specific_claims(self, text: str) -> bool:
        """Check if text has specific, quantifiable claims."""
        # Has numbers
        if any(char.isdigit() for char in text):
            return True
        
        # Has specific named entities
        specific_indicators = [
            "google", "amazon", "microsoft", "apple", "stripe",
            "#1", "award", "certified", "rated"
        ]
        text_lower = text.lower()
        return any(ind in text_lower for ind in specific_indicators)
    
    def _check_contradictions(self, result: Dict[str, Any]) -> bool:
        """Check for logical contradictions in extraction."""
        page_type = result.get("page_type", "").lower()
        is_profile = result.get("is_individual_profile", False)
        company_indicators = result.get("company_indicators", [])
        
        # Contradiction: Profile with many company indicators
        if (page_type == "profile" or is_profile) and len(company_indicators) > 2:
            return True
        
        # Contradiction: Different signals
        if page_type == "profile" and not is_profile:
            return True
        
        if is_profile and page_type in ["company", "landing", "saas"]:
            return True
        
        return False
    
    def _build_generic_blacklist(self) -> List[str]:
        """Build list of generic phrases."""
        return [
            "welcome", "about us", "contact us",
            "our services", "what we do", "who we are",
            "learn more", "get started", "sign up",
            "easy to use", "powerful features", "great support",
            "reliable", "innovative", "leading provider"
        ]
    
    def _build_positive_indicators(self) -> List[str]:
        """Build list of positive quality indicators."""
        return [
            # Quantifiable claims
            "save", "reduce", "increase", "improve", "faster",
            # Specific metrics
            "hours", "days", "months", "%", "x", "times",
            # Social proof
            "rated", "reviews", "users", "customers", "companies",
            # Trust signals
            "certified", "award", "ranked", "#1", "trusted"
        ]


def score_extraction_quality(result: Dict[str, Any]) -> QualityBreakdown:
    """
    Convenience function to score extraction quality.
    
    Args:
        result: AI extraction result dictionary
        
    Returns:
        QualityBreakdown with scores and grade
    """
    scorer = ExtractionQualityScorer()
    return scorer.score_extraction(result)
