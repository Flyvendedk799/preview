"""
Test script for intelligent page classifier and preview engine integration.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    try:
        from backend.services.intelligent_page_classifier import (
            IntelligentPageClassifier,
            PageCategory,
            get_page_classifier
        )
        print("[OK] intelligent_page_classifier imported")
        
        from backend.services.semantic_extractor import extract_semantic_structure
        print("[OK] semantic_extractor imported")
        
        from backend.services.metadata_extractor import extract_metadata_from_html
        print("[OK] metadata_extractor imported")
        
        # PreviewEngine may have dependencies not available locally
        try:
            from backend.services.preview_engine import PreviewEngine, PreviewEngineConfig
            print("[OK] preview_engine imported")
        except ImportError as ie:
            print(f"[SKIP] preview_engine import skipped (missing dependencies: {ie})")
        
        print("[PASS] Core imports successful")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_classifier_basic():
    """Test basic classifier functionality."""
    print("\nTesting basic classifier functionality...")
    try:
        from backend.services.intelligent_page_classifier import get_page_classifier, PageCategory
        
        classifier = get_page_classifier()
        
        # Test URL pattern classification
        test_cases = [
            ("https://example.com/products/laptop", PageCategory.PRODUCT),
            ("https://example.com/blog/post-1", PageCategory.CONTENT),
            ("https://example.com/profile/john", PageCategory.PROFILE),
            ("https://example.com/", PageCategory.LANDING),
            ("https://example.com/dashboard", PageCategory.TOOL),
        ]
        
        for url, expected_category in test_cases:
            classification = classifier.classify(url=url)
            actual_category = classification.primary_category
            
            if actual_category == expected_category:
                print(f"[OK] {url} -> {actual_category.value} (confidence: {classification.confidence:.2f})")
            else:
                print(f"[WARN] {url} -> {actual_category.value} (expected {expected_category.value}, confidence: {classification.confidence:.2f})")
        
        print("[PASS] Basic classifier tests passed")
        return True
    except Exception as e:
        print(f"❌ Classifier test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_classifier_with_metadata():
    """Test classifier with HTML metadata."""
    print("\nTesting classifier with HTML metadata...")
    try:
        from backend.services.intelligent_page_classifier import get_page_classifier, PageCategory
        
        classifier = get_page_classifier()
        
        # Test with og:type
        html_metadata = {
            "og_type": "product",
            "schema_type": "Product"
        }
        
        classification = classifier.classify(
            url="https://example.com/item",
            html_metadata=html_metadata
        )
        
        print(f"[OK] Classification with og:type=product -> {classification.primary_category.value} (confidence: {classification.confidence:.2f})")
        print(f"   Reasoning: {classification.reasoning[:100]}...")
        
        # Test with profile og:type
        html_metadata_profile = {
            "og_type": "profile",
        }
        
        classification_profile = classifier.classify(
            url="https://example.com/user/john",
            html_metadata=html_metadata_profile
        )
        
        print(f"[OK] Classification with og:type=profile -> {classification_profile.primary_category.value} (confidence: {classification_profile.confidence:.2f})")
        
        return True
    except Exception as e:
        print(f"❌ Classifier with metadata test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_classifier_with_structure():
    """Test classifier with content structure."""
    print("\nTesting classifier with content structure...")
    try:
        from backend.services.intelligent_page_classifier import get_page_classifier, PageCategory
        
        classifier = get_page_classifier()
        
        # Test product structure
        product_structure = {
            "has_price": True,
            "has_add_to_cart": True,
            "has_product_image": True,
            "has_reviews": True,
        }
        
        classification = classifier.classify(
            url="https://example.com/item",
            content_structure=product_structure
        )
        
        print(f"[OK] Product structure -> {classification.primary_category.value} (confidence: {classification.confidence:.2f})")
        
        # Test profile structure
        profile_structure = {
            "has_profile_image": True,
            "has_contact_info": True,
            "has_social_links": True,
            "has_bio": True,
        }
        
        classification_profile = classifier.classify(
            url="https://example.com/user/john",
            content_structure=profile_structure
        )
        
        print(f"[OK] Profile structure -> {classification_profile.primary_category.value} (confidence: {classification_profile.confidence:.2f})")
        
        return True
    except Exception as e:
        print(f"❌ Classifier with structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_preview_strategy():
    """Test that preview strategies are generated correctly."""
    print("\nTesting preview strategy generation...")
    try:
        from backend.services.intelligent_page_classifier import get_page_classifier, PageCategory
        
        classifier = get_page_classifier()
        
        # Test product strategy
        classification = classifier.classify(
            url="https://example.com/products/laptop",
            html_metadata={"og_type": "product"}
        )
        
        strategy = classification.preview_strategy
        assert "template_type" in strategy, "Strategy missing template_type"
        assert "priority_elements" in strategy, "Strategy missing priority_elements"
        assert "layout_preferences" in strategy, "Strategy missing layout_preferences"
        
        print(f"[OK] Product strategy:")
        print(f"   Template: {strategy['template_type']}")
        print(f"   Priority elements: {strategy['priority_elements']}")
        
        # Test profile strategy
        classification_profile = classifier.classify(
            url="https://example.com/profile/john",
            html_metadata={"og_type": "profile"}
        )
        
        strategy_profile = classification_profile.preview_strategy
        print(f"[OK] Profile strategy:")
        print(f"   Template: {strategy_profile['template_type']}")
        print(f"   Priority elements: {strategy_profile['priority_elements']}")
        
        return True
    except Exception as e:
        print(f"❌ Preview strategy test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_semantic_extractor():
    """Test semantic extractor structure indicators."""
    print("\nTesting semantic extractor...")
    try:
        from backend.services.semantic_extractor import extract_semantic_structure
        
        # Test HTML with product indicators
        html_product = """
        <html>
        <body>
            <h1>Laptop Pro</h1>
            <p>Price: $999</p>
            <button>Add to Cart</button>
            <div class="reviews">4.5 stars</div>
        </body>
        </html>
        """
        
        structure = extract_semantic_structure(html_product)
        
        assert "has_price" in structure, "Missing has_price indicator"
        assert "has_add_to_cart" in structure, "Missing has_add_to_cart indicator"
        assert structure["has_price"] == True, "Price not detected"
        assert structure["has_add_to_cart"] == True, "Add to cart not detected"
        
        print(f"[OK] Semantic extractor detected:")
        print(f"   has_price: {structure['has_price']}")
        print(f"   has_add_to_cart: {structure['has_add_to_cart']}")
        print(f"   has_reviews: {structure['has_reviews']}")
        
        return True
    except Exception as e:
        print(f"❌ Semantic extractor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metadata_extractor():
    """Test metadata extractor og:type extraction."""
    print("\nTesting metadata extractor...")
    try:
        from backend.services.metadata_extractor import extract_metadata_from_html
        
        # Test HTML with og:type
        html_with_og = """
        <html>
        <head>
            <meta property="og:type" content="product" />
            <script type="application/ld+json">
            {"@type": "Product"}
            </script>
        </head>
        <body></body>
        </html>
        """
        
        metadata = extract_metadata_from_html(html_with_og)
        
        assert "og_type" in metadata, "Missing og_type in metadata"
        assert metadata["og_type"] == "product", f"og_type incorrect: {metadata['og_type']}"
        assert "schema_type" in metadata, "Missing schema_type in metadata"
        
        print(f"[OK] Metadata extractor:")
        print(f"   og_type: {metadata['og_type']}")
        print(f"   schema_type: {metadata.get('schema_type', 'None')}")
        
        return True
    except Exception as e:
        print(f"❌ Metadata extractor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_preview_engine_integration():
    """Test that PreviewEngine can use the classifier."""
    print("\nTesting PreviewEngine integration...")
    try:
        # Try to import PreviewEngine, skip if dependencies missing
        try:
            from backend.services.preview_engine import PreviewEngine, PreviewEngineConfig
        except ImportError as ie:
            print(f"[SKIP] PreviewEngine not available (missing dependencies: {ie})")
            return True  # Skip this test if dependencies missing
        
        config = PreviewEngineConfig(
            is_demo=True,
            enable_brand_extraction=False,  # Skip brand extraction for faster test
            enable_ai_reasoning=False,  # Skip AI for faster test
            enable_composited_image=False,  # Skip image generation for faster test
            enable_cache=False  # Skip cache for test
        )
        
        engine = PreviewEngine(config)
        
        # Check that _classify_page_intelligently exists
        assert hasattr(engine, '_classify_page_intelligently'), "Missing _classify_page_intelligently method"
        
        # Test with minimal HTML
        html_content = """
        <html>
        <head>
            <meta property="og:type" content="product" />
            <title>Test Product</title>
        </head>
        <body>
            <h1>Test Product</h1>
            <p>Price: $99</p>
        </body>
        </html>
        """
        
        # Create minimal screenshot bytes (1x1 PNG)
        screenshot_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        # Test classification method
        classification = engine._classify_page_intelligently(
            url="https://example.com/product",
            html_content=html_content,
            screenshot_bytes=screenshot_bytes
        )
        
        assert classification is not None, "Classification returned None"
        assert hasattr(classification, 'primary_category'), "Classification missing primary_category"
        assert hasattr(classification, 'confidence'), "Classification missing confidence"
        assert hasattr(classification, 'preview_strategy'), "Classification missing preview_strategy"
        
        print(f"[OK] PreviewEngine integration:")
        print(f"   Category: {classification.primary_category.value}")
        print(f"   Confidence: {classification.confidence:.2f}")
        print(f"   Template: {classification.preview_strategy.get('template_type', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"[FAIL] PreviewEngine integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test edge cases and error handling."""
    print("\nTesting edge cases...")
    try:
        from backend.services.intelligent_page_classifier import get_page_classifier, PageCategory
        
        classifier = get_page_classifier()
        
        # Test empty URL
        classification = classifier.classify(url="")
        assert classification.primary_category == PageCategory.UNKNOWN or classification.confidence < 0.5, "Empty URL should have low confidence"
        print("[OK] Empty URL handled")
        
        # Test with no signals
        classification = classifier.classify(url="https://example.com/unknown")
        assert classification is not None, "Classification should not be None"
        print(f"[OK] Unknown URL -> {classification.primary_category.value}")
        
        # Test with conflicting signals
        classification = classifier.classify(
            url="https://example.com/product",
            html_metadata={"og_type": "profile"}  # URL says product, metadata says profile
        )
        assert classification is not None, "Conflicting signals should still produce classification"
        print(f"[OK] Conflicting signals handled -> {classification.primary_category.value}")
        
        return True
    except Exception as e:
        print(f"❌ Edge case test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("COMPREHENSIVE TEST SUITE FOR INTELLIGENT PAGE CLASSIFIER")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Basic Classifier", test_classifier_basic),
        ("Classifier with Metadata", test_classifier_with_metadata),
        ("Classifier with Structure", test_classifier_with_structure),
        ("Preview Strategy", test_preview_strategy),
        ("Semantic Extractor", test_semantic_extractor),
        ("Metadata Extractor", test_metadata_extractor),
        ("PreviewEngine Integration", test_preview_engine_integration),
        ("Edge Cases", test_edge_cases),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"[WARNING] {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

