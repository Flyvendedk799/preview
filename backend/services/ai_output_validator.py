"""
AI Output Validation Module

Validates AI extraction results for quality, sensibility, and correctness.
This module prevents nonsense results from reaching production.

VALIDATION CATEGORIES:
1. Hook/Title validation (not navigation, appropriate length, meaningful)
2. Social proof validation (has numbers, specific claims)
3. Person name validation (looks like real names, not job titles)
4. Page type consistency (all signals agree)
5. Company vs individual detection
6. Content sensibility (not generic, not filler)

DESIGN PRINCIPLES:
- Fail fast on obvious errors
- Provide actionable feedback
- Enable self-correction
- No silent failures
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity level of validation issues."""
    CRITICAL = "critical"    # Must fix (blocks usage)
    WARNING = "warning"      # Should fix (reduces quality)
    INFO = "info"           # Nice to fix (minor improvement)


@dataclass
class ValidationIssue:
    """A single validation issue."""
    severity: ValidationSeverity
    category: str  # e.g., "hook", "social_proof", "name"
    message: str
    field: str  # Which field has the issue
    current_value: Any
    suggested_fix: Optional[str] = None


@dataclass
class ValidationResult:
    """Complete validation result."""
    is_valid: bool
    quality_score: float  # 0.0-1.0
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    def get_critical_issues(self) -> List[ValidationIssue]:
        """Get only critical issues that must be fixed."""
        return [i for i in self.issues if i.severity == ValidationSeverity.CRITICAL]
    
    def get_warnings(self) -> List[ValidationIssue]:
        """Get warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]


class AIOutputValidator:
    """
    Comprehensive validator for AI extraction results.
    
    Validates:
    - Hook/title quality
    - Social proof authenticity
    - Person name validity (for profiles)
    - Page type consistency
    - Content sensibility
    - Field completeness
    """
    
    def __init__(self):
        self._generic_phrases = self._build_generic_phrase_blacklist()
        self._navigation_terms = self._build_navigation_blacklist()
        self._job_title_keywords = self._build_job_title_keywords()
        self._company_keywords = self._build_company_keywords()
    
    def validate_extraction(self, result: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete AI extraction result.
        
        Args:
            result: AI extraction result dict
            
        Returns:
            ValidationResult with issues and quality score
        """
        issues: List[ValidationIssue] = []
        
        # 1. Validate hook/title
        hook_issues = self._validate_hook(result)
        issues.extend(hook_issues)
        
        # 2. Validate social proof
        proof_issues = self._validate_social_proof(result)
        issues.extend(proof_issues)
        
        # 3. Validate person name (if profile)
        name_issues = self._validate_person_name(result)
        issues.extend(name_issues)
        
        # 4. Validate page type consistency
        consistency_issues = self._validate_page_type_consistency(result)
        issues.extend(consistency_issues)
        
        # 5. Validate benefit/description
        benefit_issues = self._validate_benefit(result)
        issues.extend(benefit_issues)
        
        # 6. Validate completeness
        completeness_issues = self._validate_completeness(result)
        issues.extend(completeness_issues)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(result, issues)
        
        # Determine if valid (no critical issues)
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        is_valid = len(critical_issues) == 0
        
        # Generate warnings and suggestions
        warnings = [i.message for i in issues if i.severity == ValidationSeverity.WARNING]
        suggestions = [i.suggested_fix for i in issues if i.suggested_fix]
        
        validation_result = ValidationResult(
            is_valid=is_valid,
            quality_score=quality_score,
            issues=issues,
            warnings=warnings,
            suggestions=suggestions
        )
        
        # Log validation summary
        if not is_valid:
            logger.warning(
                f"❌ Validation FAILED: {len(critical_issues)} critical issues, "
                f"quality score: {quality_score:.2f}"
            )
        elif warnings:
            logger.info(
                f"⚠️  Validation passed with {len(warnings)} warnings, "
                f"quality score: {quality_score:.2f}"
            )
        else:
            logger.info(f"✅ Validation passed, quality score: {quality_score:.2f}")
        
        return validation_result
    
    def _validate_hook(self, result: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate hook/title quality."""
        issues = []
        hook = result.get("the_hook", "")
        
        if not hook:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="hook",
                message="Hook is missing",
                field="the_hook",
                current_value=hook,
                suggested_fix="Extract compelling headline or main value proposition"
            ))
            return issues
        
        hook_stripped = hook.strip()
        hook_lower = hook_stripped.lower()
        
        # Check: Too short
        if len(hook_stripped) < 3:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="hook",
                message=f"Hook too short: '{hook_stripped}' ({len(hook_stripped)} chars)",
                field="the_hook",
                current_value=hook,
                suggested_fix="Extract a more substantial headline (at least 3 characters)"
            ))
        
        # Check: Too long
        if len(hook_stripped) > 150:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="hook",
                message=f"Hook too long: {len(hook_stripped)} chars (should be < 150)",
                field="the_hook",
                current_value=hook[:50] + "...",
                suggested_fix="Truncate to first sentence or key phrase"
            ))
        
        # Check: Is navigation text
        if hook_lower in self._navigation_terms:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="hook",
                message=f"Hook is navigation text: '{hook_stripped}'",
                field="the_hook",
                current_value=hook,
                suggested_fix="Extract actual content headline, not navigation menu text"
            ))
        
        # Check: Is generic phrase
        for generic in self._generic_phrases:
            if generic in hook_lower:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="hook",
                    message=f"Hook contains generic phrase: '{hook_stripped}'",
                    field="the_hook",
                    current_value=hook,
                    suggested_fix="Find more specific, compelling headline"
                ))
                break
        
        # Check: Starts with common filler words
        filler_starters = ["welcome to", "this is", "here is", "check out", "click here"]
        for filler in filler_starters:
            if hook_lower.startswith(filler):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="hook",
                    message=f"Hook starts with filler: '{hook_stripped}'",
                    field="the_hook",
                    current_value=hook,
                    suggested_fix="Extract headline without filler intro"
                ))
                break
        
        return issues
    
    def _validate_social_proof(self, result: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate social proof has numbers and specifics."""
        issues = []
        proof = result.get("social_proof_found")
        
        if not proof:
            # Having no social proof is OK (not all pages have it)
            return issues
        
        proof_stripped = proof.strip()
        
        # Check: Has numbers
        has_numbers = any(char.isdigit() for char in proof_stripped)
        if not has_numbers:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="social_proof",
                message=f"Social proof lacks numbers: '{proof_stripped}'",
                field="social_proof_found",
                current_value=proof,
                suggested_fix="Include specific numbers (ratings, counts, stats)"
            ))
        
        # Check: Generic claims
        generic_proof = ["great reviews", "highly rated", "popular", "trusted", "best"]
        for generic in generic_proof:
            if generic in proof_stripped.lower() and not has_numbers:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="social_proof",
                    message=f"Social proof is generic without numbers: '{proof_stripped}'",
                    field="social_proof_found",
                    current_value=proof,
                    suggested_fix="Replace with specific metrics (e.g., '4.9★ from 2,847 reviews')"
                ))
                break
        
        return issues
    
    def _validate_person_name(self, result: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate person name for profile pages."""
        issues = []
        
        page_type = result.get("page_type", "").lower()
        is_profile = result.get("is_individual_profile", False)
        
        # Only validate names for profile pages
        if page_type != "profile" and not is_profile:
            return issues
        
        # Check detected_person_name field
        detected_name = result.get("detected_person_name")
        hook = result.get("the_hook", "")
        
        # For profiles, hook should be the person's name
        name_to_check = detected_name or hook
        
        if not name_to_check:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="person_name",
                message="Profile page missing person name",
                field="detected_person_name",
                current_value=None,
                suggested_fix="Extract person's full name (2-4 words, capitalized)"
            ))
            return issues
        
        # Validate name looks like a real person name
        name_validation = self._is_valid_person_name(name_to_check)
        
        if not name_validation["valid"]:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="person_name",
                message=f"Invalid person name for profile: '{name_to_check}' - {name_validation['reason']}",
                field="detected_person_name",
                current_value=name_to_check,
                suggested_fix=name_validation.get("suggestion", "Extract actual person name")
            ))
        
        return issues
    
    def _validate_page_type_consistency(self, result: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate page type is consistent with other signals."""
        issues = []
        
        page_type = result.get("page_type", "").lower()
        is_profile = result.get("is_individual_profile", False)
        company_indicators = result.get("company_indicators", [])
        
        # Check: Marked as profile but has company indicators
        if (page_type == "profile" or is_profile) and len(company_indicators) > 2:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="consistency",
                message=f"Marked as profile but has {len(company_indicators)} company indicators: {', '.join(company_indicators[:3])}",
                field="page_type",
                current_value=page_type,
                suggested_fix="Reclassify as company/landing page"
            ))
        
        # Check: Profile page type but is_individual_profile is false
        if page_type == "profile" and not is_profile:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="consistency",
                message="page_type='profile' but is_individual_profile=false (inconsistent)",
                field="page_type",
                current_value=page_type,
                suggested_fix="Ensure profile classification is consistent"
            ))
        
        # Check: is_individual_profile but page_type is not profile
        if is_profile and page_type not in ["profile", "personal"]:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="consistency",
                message=f"is_individual_profile=true but page_type='{page_type}' (inconsistent)",
                field="is_individual_profile",
                current_value=is_profile,
                suggested_fix="Update page_type to 'profile' or set is_individual_profile=false"
            ))
        
        return issues
    
    def _validate_benefit(self, result: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate key benefit is specific, not generic."""
        issues = []
        benefit = result.get("key_benefit")
        
        if not benefit:
            # Not having a benefit is OK (informational)
            return issues
        
        benefit_lower = benefit.strip().lower()
        
        # Check for generic benefits
        generic_benefits = [
            "easy to use",
            "powerful features",
            "great support",
            "simple and intuitive",
            "user-friendly",
            "reliable",
            "fast",
            "secure",
        ]
        
        for generic in generic_benefits:
            if benefit_lower == generic or benefit_lower == generic + ".":
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="benefit",
                    message=f"Benefit is too generic: '{benefit.strip()}'",
                    field="key_benefit",
                    current_value=benefit,
                    suggested_fix="Find specific, quantifiable benefit (e.g., 'Save 10 hours/week')"
                ))
                break
        
        return issues
    
    def _validate_completeness(self, result: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate extraction has reasonable completeness."""
        issues = []
        
        # Check basic fields exist
        if not result.get("the_hook"):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="completeness",
                message="Missing hook/title",
                field="the_hook",
                current_value=None
            ))
        
        if not result.get("page_type"):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="completeness",
                message="Missing page_type classification",
                field="page_type",
                current_value=None
            ))
        
        # Check confidence
        confidence = result.get("confidence", 0.0)
        if confidence < 0.3:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="completeness",
                message=f"Very low extraction confidence: {confidence:.2f}",
                field="confidence",
                current_value=confidence,
                suggested_fix="Consider retry or fallback extraction method"
            ))
        
        return issues
    
    def _is_valid_person_name(self, name: str) -> Dict[str, Any]:
        """
        Check if string looks like a real person name.
        
        Returns dict with:
        - valid: bool
        - reason: str (if invalid)
        - suggestion: str (if invalid)
        """
        if not name or len(name.strip()) < 3:
            return {
                "valid": False,
                "reason": "Name too short (< 3 chars)",
                "suggestion": "Extract full person name"
            }
        
        name_stripped = name.strip()
        words = name_stripped.split()
        
        # Names are typically 2-4 words
        if len(words) < 2:
            return {
                "valid": False,
                "reason": "Name has only 1 word (needs first + last)",
                "suggestion": "Extract full name (e.g., 'John Doe', not just 'John')"
            }
        
        if len(words) > 5:
            return {
                "valid": False,
                "reason": f"Name has too many words ({len(words)})",
                "suggestion": "Extract just the person's name, not their bio"
            }
        
        # Names are typically < 60 characters total
        if len(name_stripped) > 60:
            return {
                "valid": False,
                "reason": f"Name too long ({len(name_stripped)} chars) - likely a bio",
                "suggestion": "Extract just the name (2-4 words), not the description"
            }
        
        # Most words should be capitalized (proper nouns)
        capitalized_words = sum(1 for w in words if w and w[0].isupper())
        if capitalized_words < len(words) * 0.65:  # At least 65% capitalized
            return {
                "valid": False,
                "reason": "Name lacks proper capitalization",
                "suggestion": "Look for properly capitalized name (e.g., 'Sarah Chen')"
            }
        
        # Check for job title keywords (names shouldn't have these)
        for keyword in self._job_title_keywords:
            if keyword in name_stripped.lower():
                return {
                    "valid": False,
                    "reason": f"Contains job title keyword '{keyword}' - this is a title, not a name",
                    "suggestion": "Extract person's name only, exclude job title"
                }
        
        # Check for company name indicators
        for keyword in self._company_keywords:
            if keyword in name_stripped.lower():
                return {
                    "valid": False,
                    "reason": f"Contains company keyword '{keyword}' - this is a company, not a person",
                    "suggestion": "Verify this is an individual profile, not a company page"
                }
        
        # Passed all checks
        return {"valid": True}
    
    def _calculate_quality_score(
        self,
        result: Dict[str, Any],
        issues: List[ValidationIssue]
    ) -> float:
        """
        Calculate overall quality score (0.0-1.0).
        
        Factors:
        - Has compelling hook (not generic)
        - Has social proof with numbers
        - Has specific benefit
        - Page type confidence high
        - No validation issues
        """
        score = 1.0  # Start with perfect score
        
        # Penalty for validation issues
        for issue in issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                score -= 0.25  # -25% per critical issue
            elif issue.severity == ValidationSeverity.WARNING:
                score -= 0.10  # -10% per warning
            else:  # INFO
                score -= 0.02  # -2% per info
        
        # Bonus for good elements
        hook = result.get("the_hook", "")
        if hook and len(hook) > 5:
            # Bonus for having numbers in hook (specific)
            if any(char.isdigit() for char in hook):
                score += 0.05
        
        # Bonus for social proof with numbers
        proof = result.get("social_proof_found")
        if proof and any(char.isdigit() for char in proof):
            score += 0.10
        
        # Bonus for specific benefit
        benefit = result.get("key_benefit")
        if benefit and len(benefit) > 10:
            # Bonus if benefit has numbers
            if any(char.isdigit() for char in benefit):
                score += 0.05
        
        # Bonus for high confidence
        confidence = result.get("confidence", 0.5)
        if confidence > 0.8:
            score += 0.05
        
        # Clamp to 0.0-1.0
        return max(0.0, min(1.0, score))
    
    def _build_generic_phrase_blacklist(self) -> List[str]:
        """Build list of generic phrases that should not be hooks."""
        return [
            "welcome",
            "welcome to",
            "about us",
            "our story",
            "get started",
            "learn more",
            "click here",
            "sign up",
            "join us",
            "contact us",
            "our services",
            "what we do",
            "who we are",
        ]
    
    def _build_navigation_blacklist(self) -> set:
        """Build set of navigation terms that should never be hooks."""
        return {
            "home",
            "about",
            "contact",
            "services",
            "products",
            "portfolio",
            "blog",
            "news",
            "careers",
            "login",
            "sign up",
            "signup",
            "sign in",
            "signin",
            "register",
            "menu",
            "navigation",
            "search",
        }
    
    def _build_job_title_keywords(self) -> List[str]:
        """Build list of job title keywords (not person names)."""
        return [
            # Seniority
            "senior", "junior", "lead", "principal", "staff",
            "head of", "chief", "director", "manager", "coordinator",
            # Roles
            "developer", "engineer", "designer", "architect",
            "analyst", "consultant", "specialist", "expert",
            "administrator", "officer", "executive",
            # Domains
            "software", "frontend", "backend", "full stack", "fullstack",
            "data", "product", "marketing", "sales", "operations",
            # Modifiers
            "certified", "experienced", "professional",
        ]
    
    def _build_company_keywords(self) -> List[str]:
        """Build list of company name keywords."""
        return [
            # Legal entities
            "inc", "llc", "ltd", "corp", "corporation", "company", "co.",
            # Business types
            "agency", "studio", "group", "partners", "consulting",
            "solutions", "services", "tech", "technologies",
            "software", "systems", "media", "digital",
            # Other indicators
            "team", "collective", "creative", "design firm",
        ]


def validate_extraction_result(result: Dict[str, Any]) -> ValidationResult:
    """
    Convenience function to validate an extraction result.
    
    Args:
        result: AI extraction result dictionary
        
    Returns:
        ValidationResult with issues and quality score
    """
    validator = AIOutputValidator()
    return validator.validate_extraction(result)
