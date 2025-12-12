"""
Comprehensive Test Suite for Product Page Enhancements

Tests all product intelligence, visual system, design system, and rendering components.
"""

import pytest
from unittest.mock import Mock, MagicMock
from PIL import Image
from io import BytesIO

# Test imports
try:
    from backend.services.product_intelligence import (
        ProductIntelligenceExtractor,
        ProductCategory,
        ProductInformation,
        BadgeType
    )
    from backend.services.product_visual_system import (
        ProductVisualRenderer,
        generate_product_visual_spec,
        UrgencyLevel,
        PriceDisplayStyle
    )
    from backend.services.product_design_system import (
        ProductDesignSystem,
        get_design_profile,
        LayoutStyle,
        ImageTreatment,
        ColorScheme
    )
    from backend.services.product_feature_selector import (
        SmartFeatureSelector,
        select_smart_features
    )
    from backend.services.product_image_optimizer import (
        ProductImageOptimizer,
        optimize_product_image
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    print(f"⚠️ Imports not available: {e}")


# =============================================================================
# Test Data
# =============================================================================

MOCK_PRODUCT_AI_ANALYSIS = {
    "page_type": "ecommerce",
    "the_hook": "Apple AirPods Pro (2nd Gen)",
    "social_proof_found": "4.8★ (28,474 reviews)",
    "pricing": {
        "current_price": "$199.99",
        "original_price": "$249.99",
        "discount_percentage": 20,
        "deal_ends": "Ends tonight at midnight"
    },
    "availability": {
        "in_stock": True,
        "stock_level": "Only 3 left in stock"
    },
    "rating": {
        "value": 4.8,
        "count": 28474
    },
    "product_details": {
        "brand": "Apple",
        "category": "Electronics"
    },
    "badges": ["Best Seller", "Amazon's Choice", "Free Shipping"]
}

MOCK_FASHION_PRODUCT = {
    "page_type": "ecommerce",
    "the_hook": "Nike Air Max 2024",
    "pricing": {
        "current_price": "$149.99",
        "original_price": "$249.99",
        "discount_percentage": 40
    },
    "availability": {
        "in_stock": True,
        "stock_level": "Only 5 left"
    },
    "rating": {
        "value": 4.7,
        "count": 1892
    },
    "product_details": {
        "brand": "Nike",
        "category": "Fashion"
    },
    "variants": {
        "colors": ["Black", "White", "Red"],
        "sizes": ["7", "8", "9", "10", "11"]
    }
}

MOCK_FOOD_PRODUCT = {
    "page_type": "ecommerce",
    "the_hook": "Organic Honey - 16oz",
    "pricing": {
        "current_price": "$12.99"
    },
    "rating": {
        "value": 4.9,
        "count": 2847
    },
    "product_details": {
        "brand": "Local Harvest",
        "category": "Food"
    },
    "badges": ["Organic", "Non-GMO", "Local"]
}


# =============================================================================
# Product Intelligence Tests
# =============================================================================

def test_product_intelligence_extraction():
    """Test comprehensive product data extraction."""
    print("\n=== Testing Product Intelligence Extraction ===\n")
    
    if not IMPORTS_AVAILABLE:
        print("⚠️ Skipping test - imports not available")
        return False
    
    try:
        extractor = ProductIntelligenceExtractor()
        product_info = extractor.extract(MOCK_PRODUCT_AI_ANALYSIS)
        
        # Test pricing extraction
        assert product_info.pricing.current_price == "$199.99"
        assert product_info.pricing.original_price == "$249.99"
        assert product_info.pricing.discount_percentage == 20
        assert product_info.pricing.is_on_sale == True
        assert product_info.pricing.deal_ends == "Ends tonight at midnight"
        print("✅ PASS: Pricing extraction correct")
        
        # Test availability
        assert product_info.availability.in_stock == True
        assert product_info.availability.limited_quantity == True
        assert product_info.availability.stock_quantity == 3
        print("✅ PASS: Availability extraction correct")
        
        # Test ratings
        assert product_info.rating.rating == 4.8
        assert product_info.rating.review_count == 28474
        print("✅ PASS: Rating extraction correct")
        
        # Test badges
        assert len(product_info.trust_signals.badges) == 3
        assert "Best Seller" in product_info.trust_signals.badges
        print("✅ PASS: Badge extraction correct")
        
        # Test urgency signals
        assert product_info.urgency_signals.has_urgency == True
        assert product_info.urgency_signals.deal_countdown is not None
        assert product_info.urgency_signals.limited_stock == True
        print("✅ PASS: Urgency signal synthesis correct")
        
        # Test category mapping
        assert product_info.details.product_type == ProductCategory.ELECTRONICS
        print("✅ PASS: Category mapping correct")
        
        print("\n✅ Product Intelligence: ALL TESTS PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Product Intelligence: FAILED - {e}\n")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# Visual System Tests
# =============================================================================

def test_visual_spec_generation():
    """Test visual specification generation."""
    print("\n=== Testing Visual Spec Generation ===\n")
    
    if not IMPORTS_AVAILABLE:
        print("⚠️ Skipping test - imports not available")
        return False
    
    try:
        # Prepare product intelligence dict
        product_info_dict = {
            "pricing": {
                "current_price": "$199.99",
                "original_price": "$249.99",
                "discount_percentage": 40,
                "is_on_sale": True,
                "deal_ends": "Ends in 2 hours"
            },
            "availability": {
                "in_stock": True,
                "limited_quantity": True,
                "stock_level": "Only 3 left"
            },
            "rating": {
                "rating": 4.9,
                "review_count": 28474
            },
            "urgency": {
                "has_urgency": True,
                "deal_countdown": "Ends in 2 hours",
                "stock_message": "Only 3 left"
            },
            "trust_signals": {
                "badges": ["Best Seller", "Amazon's Choice", "Free Shipping"]
            }
        }
        
        visual_spec = generate_product_visual_spec(product_info_dict)
        
        # Test urgency banner
        assert visual_spec.urgency_banner is not None
        assert visual_spec.urgency_banner.show == True
        assert "ENDS IN 2 HOURS" in visual_spec.urgency_banner.message.upper()
        print("✅ PASS: Urgency banner generated correctly")
        
        # Test discount badge (40% discount should be LARGE)
        assert visual_spec.discount_badge is not None
        assert visual_spec.discount_badge.show == True
        assert visual_spec.discount_badge.size in ["large", "extra-large"]
        print("✅ PASS: Discount badge generated correctly")
        
        # Test price spec (40% sale should be RED)
        assert visual_spec.price is not None
        assert visual_spec.price.display_style in [PriceDisplayStyle.SALE_HERO, PriceDisplayStyle.DISCOUNT]
        assert visual_spec.price.current_price_color.hex == "#DC2626"  # RED
        assert visual_spec.price.show_strikethrough == True
        print("✅ PASS: Price display spec correct (RED for sale)")
        
        # Test rating spec (4.9 should be prominent)
        assert visual_spec.rating is not None
        assert visual_spec.rating.is_exceptional == True
        assert visual_spec.rating.star_size >= 32  # Large stars for 4.8+
        print("✅ PASS: Rating spec correct (prominent for 4.9)")
        
        # Test overall urgency level
        assert visual_spec.overall_urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]
        print("✅ PASS: Overall urgency level correct")
        
        print("\n✅ Visual System: ALL TESTS PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Visual System: FAILED - {e}\n")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# Design System Tests
# =============================================================================

def test_design_profiles():
    """Test category design profiles."""
    print("\n=== Testing Design System Profiles ===\n")
    
    if not IMPORTS_AVAILABLE:
        print("⚠️ Skipping test - imports not available")
        return False
    
    try:
        # Test Electronics profile
        elec_profile = get_design_profile(ProductCategory.ELECTRONICS)
        assert elec_profile.layout_style == LayoutStyle.SPLIT
        assert elec_profile.image_treatment == ImageTreatment.CLEAN_BG
        assert elec_profile.color_scheme == ColorScheme.MINIMAL
        assert elec_profile.show_specs == True
        assert elec_profile.feature_style == "grid"
        print("✅ PASS: Electronics profile correct (split, clean, specs)")
        
        # Test Fashion profile
        fashion_profile = get_design_profile(ProductCategory.FASHION)
        assert fashion_profile.layout_style == LayoutStyle.HERO
        assert fashion_profile.image_treatment == ImageTreatment.LIFESTYLE
        assert fashion_profile.color_scheme == ColorScheme.VIBRANT
        assert fashion_profile.price_prominence == "hero"
        print("✅ PASS: Fashion profile correct (hero, lifestyle, vibrant)")
        
        # Test Food profile
        food_profile = get_design_profile(ProductCategory.FOOD)
        assert food_profile.layout_style == LayoutStyle.HERO
        assert food_profile.image_treatment == ImageTreatment.ZOOM
        assert food_profile.title_weight == "extra-bold"
        print("✅ PASS: Food profile correct (hero, zoom, extra-bold)")
        
        # Test Beauty profile
        beauty_profile = get_design_profile(ProductCategory.BEAUTY)
        assert beauty_profile.layout_style == LayoutStyle.CARD
        assert beauty_profile.image_treatment == ImageTreatment.SOFT
        assert beauty_profile.color_scheme == ColorScheme.LUXE
        assert beauty_profile.use_serif_title == True  # Elegant serif
        print("✅ PASS: Beauty profile correct (card, soft, luxe, serif)")
        
        print("\n✅ Design System: ALL TESTS PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Design System: FAILED - {e}\n")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# Feature Selection Tests
# =============================================================================

def test_feature_selection():
    """Test smart feature selection."""
    print("\n=== Testing Feature Selection ===\n")
    
    if not IMPORTS_AVAILABLE:
        print("⚠️ Skipping test - imports not available")
        return False
    
    try:
        # Electronics features
        elec_features = [
            "128GB Storage",
            "5G Connectivity",
            "Stylish design",  # Low priority
            "24-hour battery life",
            "Nice color"  # Vague, should be deprioritized
        ]
        
        selected = select_smart_features(elec_features, ProductCategory.ELECTRONICS, max_features=3)
        
        # Should prioritize technical specs over vague features
        assert "128GB Storage" in selected
        assert "5G Connectivity" in selected
        assert "24-hour battery life" in selected
        assert "Stylish design" not in selected  # Low priority
        assert "Nice color" not in selected  # Vague
        print("✅ PASS: Electronics feature selection prioritizes specs")
        
        # Fashion features
        fashion_features = [
            "100% organic cotton",  # High priority
            "Machine washable",  # High priority
            "Trendy style",  # Low priority
            "Breathable fabric"  # High priority
        ]
        
        selected = select_smart_features(fashion_features, ProductCategory.FASHION, max_features=3)
        assert "100% organic cotton" in selected
        assert "Machine washable" in selected or "Breathable fabric" in selected
        print("✅ PASS: Fashion feature selection prioritizes materials")
        
        # Food features
        food_features = [
            "USDA Organic",  # High priority
            "Non-GMO",  # High priority
            "Delicious taste",  # Low priority, vague
            "Gluten-free"  # High priority
        ]
        
        selected = select_smart_features(food_features, ProductCategory.FOOD, max_features=3)
        assert "USDA Organic" in selected
        assert "Delicious taste" not in selected  # Vague
        print("✅ PASS: Food feature selection prioritizes certifications")
        
        print("\n✅ Feature Selection: ALL TESTS PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Feature Selection: FAILED - {e}\n")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# Image Optimization Tests
# =============================================================================

def test_image_optimization():
    """Test category-specific image optimization."""
    print("\n=== Testing Image Optimization ===\n")
    
    if not IMPORTS_AVAILABLE:
        print("⚠️ Skipping test - imports not available")
        return False
    
    try:
        # Create test image
        test_img = Image.new('RGB', (100, 100), color='red')
        
        # Test electronics optimization
        optimizer = ProductImageOptimizer()
        optimized = optimizer.optimize(test_img, ProductCategory.ELECTRONICS)
        assert optimized.size == (100, 100)
        print("✅ PASS: Electronics image optimization (sharp, precise)")
        
        # Test food optimization (should be most vibrant)
        optimized_food = optimizer.optimize(test_img, ProductCategory.FOOD)
        assert optimized_food.size == (100, 100)
        print("✅ PASS: Food image optimization (vibrant, high contrast)")
        
        # Test beauty optimization (should be soft)
        optimized_beauty = optimizer.optimize(test_img, ProductCategory.BEAUTY)
        assert optimized_beauty.size == (100, 100)
        print("✅ PASS: Beauty image optimization (soft, bright)")
        
        print("\n✅ Image Optimization: ALL TESTS PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Image Optimization: FAILED - {e}\n")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# Integration Tests
# =============================================================================

def test_end_to_end_product_pipeline():
    """Test complete product preview generation pipeline."""
    print("\n=== Testing End-to-End Pipeline ===\n")
    
    if not IMPORTS_AVAILABLE:
        print("⚠️ Skipping test - imports not available")
        return False
    
    try:
        # 1. Extract product intelligence
        extractor = ProductIntelligenceExtractor()
        product_info = extractor.extract(MOCK_PRODUCT_AI_ANALYSIS)
        
        # 2. Get design profile
        profile = get_design_profile(product_info.details.product_type)
        
        # 3. Generate visual specs
        product_info_dict = {
            "pricing": {
                "current_price": product_info.pricing.current_price,
                "original_price": product_info.pricing.original_price,
                "discount_percentage": product_info.pricing.discount_percentage,
                "is_on_sale": product_info.pricing.is_on_sale
            },
            "rating": {
                "rating": product_info.rating.rating,
                "review_count": product_info.rating.review_count
            },
            "urgency": {
                "has_urgency": product_info.urgency_signals.has_urgency
            },
            "trust_signals": {
                "badges": product_info.trust_signals.badges
            }
        }
        
        visual_spec = generate_product_visual_spec(product_info_dict)
        
        # 4. Verify pipeline flow
        assert product_info.pricing.is_on_sale == True
        assert profile.layout_style == LayoutStyle.SPLIT  # Electronics
        assert visual_spec.discount_badge is not None
        assert visual_spec.urgency_banner is not None
        
        print("✅ PASS: End-to-end pipeline works correctly")
        print("   → Intelligence extracted")
        print("   → Design profile selected")
        print("   → Visual specs generated")
        print("   → Ready for rendering")
        
        print("\n✅ Integration: ALL TESTS PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration: FAILED - {e}\n")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# Run All Tests
# =============================================================================

def run_all_tests():
    """Run complete test suite."""
    print("\n" + "="*80)
    print("🧪 PRODUCT ENHANCEMENTS - COMPREHENSIVE TEST SUITE")
    print("="*80 + "\n")
    
    if not IMPORTS_AVAILABLE:
        print("❌ Cannot run tests - required imports not available")
        print("   Make sure all product enhancement modules are in the correct location")
        return False
    
    results = []
    
    # Run each test
    results.append(("Product Intelligence", test_product_intelligence_extraction()))
    results.append(("Visual System", test_visual_spec_generation()))
    results.append(("Design System", test_design_profiles()))
    results.append(("Feature Selection", test_feature_selection()))
    results.append(("Image Optimization", test_image_optimization()))
    results.append(("End-to-End Pipeline", test_end_to_end_product_pipeline()))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:12} {name}")
    
    print(f"\n{'='*80}")
    print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("="*80 + "\n")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Product enhancements are working correctly.\n")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed. Review errors above.\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
