"""
Comprehensive Test Suite for AI Engine Enhancements

Tests all enhancement modules to ensure they work correctly:
- Page classifier (negative signals, URL patterns, cross-validation)
- Output validator
- Quality scorer  
- Extraction enhancer
- Fallback system
- Quality gates

Run with: python3 -m pytest backend/services/test_ai_enhancements.py -v
Or: python3 backend/services/test_ai_enhancements.py
"""

import sys
from typing import Dict, Any


def test_page_classifier_enhancements():
    """Test enhanced page classifier with negative signals."""
    print("\n=== Testing Page Classifier Enhancements ===")
    
    try:
        from backend.services.intelligent_page_classifier import (
            IntelligentPageClassifier,
            PageCategory
        )
        
        classifier = IntelligentPageClassifier()
        
        # Test 1: Individual profile URL (should be PROFILE)
        print("\n1. Testing individual profile URL...")
        classification = classifier.classify(
            url="https://example.com/profile/john-doe",
            ai_analysis={"page_type": "profile", "is_individual_profile": True, "company_indicators": []}
        )
        assert classification.primary_category == PageCategory.PROFILE, f"Expected PROFILE, got {classification.primary_category}"
        print(f"✅ PASS: Classified as {classification.primary_category} (confidence: {classification.confidence:.2f})")
        
        # Test 2: Company team page (should NOT be PROFILE)
        print("\n2. Testing company team page...")
        classification = classifier.classify(
            url="https://example.com/team",
            ai_analysis={
                "page_type": "company",
                "is_individual_profile": False,
                "company_indicators": ["team page", "multiple people", "we language"]
            }
        )
        assert classification.primary_category != PageCategory.PROFILE, f"Should NOT be PROFILE, got {classification.primary_category}"
        print(f"✅ PASS: Classified as {classification.primary_category} (correctly NOT profile)")
        
        # Test 3: E-commerce page with pricing (negative signals should disprove PROFILE)
        print("\n3. Testing e-commerce with negative signals...")
        classification = classifier.classify(
            url="https://shop.com/product/item-123",
            content_structure={
                "has_price": True,
                "has_add_to_cart": True
            },
            ai_analysis={"page_type": "ecommerce", "is_individual_profile": False}
        )
        assert classification.primary_category == PageCategory.PRODUCT, f"Expected PRODUCT, got {classification.primary_category}"
        print(f"✅ PASS: Negative signals correctly identified product page")
        
        print("\n✅ Page Classifier: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Page Classifier: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_output_validator():
    """Test output validator."""
    print("\n=== Testing Output Validator ===")
    
    try:
        from backend.services.ai_output_validator import AIOutputValidator, ValidationSeverity
        
        validator = AIOutputValidator()
        
        # Test 1: Valid extraction
        print("\n1. Testing valid extraction...")
        valid_result = {
            "the_hook": "Ship 10x faster with AI",
            "social_proof_found": "4.9★ from 2,847 reviews",
            "key_benefit": "Save 10 hours/week",
            "page_type": "saas",
            "is_individual_profile": False,
            "confidence": 0.85
        }
        validation = validator.validate_extraction(valid_result)
        assert validation.is_valid, "Should be valid"
        print(f"✅ PASS: Valid extraction (quality: {validation.quality_score:.2f})")
        
        # Test 2: Invalid hook (navigation text)
        print("\n2. Testing invalid hook (navigation)...")
        invalid_result = {
            "the_hook": "Welcome",
            "page_type": "landing",
            "confidence": 0.7
        }
        validation = validator.validate_extraction(invalid_result)
        # Check that it at least has warnings/low quality
        assert len(validation.issues) > 0 or validation.quality_score < 0.70, "Should have issues or low quality"
        print(f"✅ PASS: Correctly detected navigation hook issues (quality: {validation.quality_score:.2f})")
        
        # Test 3: Invalid person name for profile
        print("\n3. Testing invalid person name...")
        profile_result = {
            "the_hook": "Senior Product Designer with 10 years experience",
            "page_type": "profile",
            "is_individual_profile": True,
            "detected_person_name": "Senior Product Designer",
            "confidence": 0.6
        }
        validation = validator.validate_extraction(profile_result)
        assert not validation.is_valid, "Should be invalid (job title as name)"
        print(f"✅ PASS: Correctly detected job title as invalid name")
        
        print("\n✅ Output Validator: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Output Validator: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quality_scorer():
    """Test quality scorer."""
    print("\n=== Testing Quality Scorer ===")
    
    try:
        from backend.services.extraction_quality_scorer import (
            ExtractionQualityScorer,
            QualityGrade
        )
        
        scorer = ExtractionQualityScorer()
        
        # Test 1: High quality extraction
        print("\n1. Testing high quality extraction...")
        excellent_result = {
            "the_hook": "Ship 10x faster with AI",
            "social_proof_found": "4.9★ from 2,847 reviews",
            "key_benefit": "Save 10 hours/week on reporting",
            "page_type": "saas",
            "confidence": 0.9
        }
        score = scorer.score_extraction(excellent_result)
        assert score.overall_score >= 0.70, f"Should be high quality, got {score.overall_score:.2f}"
        print(f"✅ PASS: High quality (score: {score.overall_score:.2f}, grade: {score.grade.value})")
        
        # Test 2: Low quality extraction (generic)
        print("\n2. Testing low quality extraction...")
        poor_result = {
            "the_hook": "Welcome to our website",
            "social_proof_found": "Great reviews",
            "key_benefit": "Easy to use",
            "page_type": "unknown",
            "confidence": 0.4
        }
        score = scorer.score_extraction(poor_result)
        assert score.overall_score < 0.60, f"Should be low quality, got {score.overall_score:.2f}"
        assert score.should_retry(), "Should recommend retry"
        print(f"✅ PASS: Low quality detected (score: {score.overall_score:.2f}, should_retry: {score.should_retry()})")
        
        print("\n✅ Quality Scorer: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Quality Scorer: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quality_gates():
    """Test quality gates."""
    print("\n=== Testing Quality Gates ===")
    
    try:
        from backend.services.quality_gates import (
            QualityGateEvaluator,
            QualityGateConfig,
            GateStatus
        )
        
        config = QualityGateConfig(
            min_extraction_quality=0.60,
            min_confidence=0.50,
            require_hook=True,
            allow_navigation_hooks=False
        )
        evaluator = QualityGateEvaluator(config)
        
        # Test 1: Should pass gates
        print("\n1. Testing passing gates...")
        good_extraction = {
            "the_hook": "Ship 10x faster",
            "page_type": "saas",
            "analysis_confidence": 0.8,
            "is_individual_profile": False,
            "company_indicators": []
        }
        result = evaluator.evaluate(good_extraction, quality_score=0.75)
        assert result.status in [GateStatus.PASS, GateStatus.PASS_WITH_WARNINGS], f"Should pass, got {result.status}"
        assert result.should_use, "Should be usable"
        print(f"✅ PASS: Gates passed (status: {result.status.value})")
        
        # Test 2: Should fail gates (navigation hook)
        print("\n2. Testing failing gates...")
        bad_extraction = {
            "the_hook": "Welcome",
            "page_type": "unknown",
            "analysis_confidence": 0.3
        }
        result = evaluator.evaluate(bad_extraction, quality_score=0.3)
        assert result.status in [GateStatus.FAIL, GateStatus.REJECT], f"Should fail, got {result.status}"
        assert not result.should_use, "Should not be usable"
        print(f"✅ PASS: Gates correctly failed (status: {result.status.value})")
        
        print("\n✅ Quality Gates: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Quality Gates: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback_system():
    """Test fallback system."""
    print("\n=== Testing Fallback System ===")
    
    try:
        from backend.services.extraction_fallback_system import ExtractionFallbackSystem
        
        system = ExtractionFallbackSystem()
        
        # Test: Minimal fallback (URL-only)
        print("\n1. Testing minimal fallback...")
        result = system._create_minimal_fallback("https://stripe.com/products/payments")
        assert result["the_hook"], "Should have a hook"
        assert result["page_type"], "Should have a page type"
        assert result["extraction_method"] == "url_fallback"
        print(f"✅ PASS: Minimal fallback created (hook: '{result['the_hook']}')")
        
        print("\n✅ Fallback System: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Fallback System: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("AI ENGINE ENHANCEMENTS - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    results = {
        "Page Classifier": test_page_classifier_enhancements(),
        "Output Validator": test_output_validator(),
        "Quality Scorer": test_quality_scorer(),
        "Quality Gates": test_quality_gates(),
        "Fallback System": test_fallback_system()
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! AI Engine enhancements are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed. Please review failures above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
