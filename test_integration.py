"""
Integration test to verify the complete flow works correctly.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_complete_flow():
    """Test the complete classification and strategy flow."""
    print("Testing complete integration flow...")
    
    try:
        from backend.services.intelligent_page_classifier import get_page_classifier, PageCategory
        from backend.services.semantic_extractor import extract_semantic_structure
        from backend.services.metadata_extractor import extract_metadata_from_html
        
        classifier = get_page_classifier()
        
        # Test 1: Product page with all signals
        print("\n[TEST 1] Product page with all signals")
        html_product = """
        <html>
        <head>
            <meta property="og:type" content="product" />
            <script type="application/ld+json">{"@type": "Product"}</script>
        </head>
        <body>
            <h1>Laptop Pro</h1>
            <p>Price: $999</p>
            <button>Add to Cart</button>
            <div class="reviews">4.5 stars</div>
        </body>
        </html>
        """
        
        metadata = extract_metadata_from_html(html_product)
        structure = extract_semantic_structure(html_product)
        
        classification = classifier.classify(
            url="https://example.com/products/laptop",
            html_metadata=metadata,
            content_structure=structure
        )
        
        assert classification.primary_category == PageCategory.PRODUCT, f"Expected PRODUCT, got {classification.primary_category}"
        assert classification.confidence > 0.7, f"Confidence too low: {classification.confidence}"
        assert classification.preview_strategy["template_type"] == "product", "Wrong template type"
        assert "product_image" in classification.preview_strategy["priority_elements"], "Missing product_image in priority"
        
        print(f"  [PASS] Category: {classification.primary_category.value}")
        print(f"  [PASS] Confidence: {classification.confidence:.2f}")
        print(f"  [PASS] Template: {classification.preview_strategy['template_type']}")
        print(f"  [PASS] Priority elements: {classification.preview_strategy['priority_elements']}")
        
        # Test 2: Profile page
        print("\n[TEST 2] Profile page")
        html_profile = """
        <html>
        <head>
            <meta property="og:type" content="profile" />
        </head>
        <body>
            <img class="avatar" src="profile.jpg" />
            <h1>John Doe</h1>
            <p>Bio: Software engineer</p>
            <a href="mailto:john@example.com">Contact</a>
        </body>
        </html>
        """
        
        metadata_profile = extract_metadata_from_html(html_profile)
        structure_profile = extract_semantic_structure(html_profile)
        
        classification_profile = classifier.classify(
            url="https://example.com/profile/john",
            html_metadata=metadata_profile,
            content_structure=structure_profile
        )
        
        assert classification_profile.primary_category == PageCategory.PROFILE, f"Expected PROFILE, got {classification_profile.primary_category}"
        assert classification_profile.preview_strategy["template_type"] == "profile", "Wrong template type"
        assert "avatar" in classification_profile.preview_strategy["priority_elements"], "Missing avatar in priority"
        
        print(f"  [PASS] Category: {classification_profile.primary_category.value}")
        print(f"  [PASS] Template: {classification_profile.preview_strategy['template_type']}")
        
        # Test 3: Landing page (homepage)
        print("\n[TEST 3] Landing page")
        html_landing = """
        <html>
        <head>
            <meta property="og:type" content="website" />
        </head>
        <body>
            <section class="hero">
                <h1>Welcome to Our Platform</h1>
                <button>Get Started</button>
            </section>
            <section class="features">Features</section>
        </body>
        </html>
        """
        
        metadata_landing = extract_metadata_from_html(html_landing)
        structure_landing = extract_semantic_structure(html_landing)
        
        classification_landing = classifier.classify(
            url="https://example.com/",
            html_metadata=metadata_landing,
            content_structure=structure_landing
        )
        
        assert classification_landing.primary_category == PageCategory.LANDING, f"Expected LANDING, got {classification_landing.primary_category}"
        assert classification_landing.preview_strategy["template_type"] == "landing", "Wrong template type"
        
        print(f"  [PASS] Category: {classification_landing.primary_category.value}")
        print(f"  [PASS] Template: {classification_landing.preview_strategy['template_type']}")
        
        # Test 4: Edge case - conflicting signals
        print("\n[TEST 4] Conflicting signals (URL says product, metadata says profile)")
        classification_conflict = classifier.classify(
            url="https://example.com/products/item",
            html_metadata={"og_type": "profile"}
        )
        
        # Should still produce a valid classification (preferring stronger signal)
        assert classification_conflict is not None, "Should produce classification"
        assert classification_conflict.primary_category in [PageCategory.PRODUCT, PageCategory.PROFILE], "Should be PRODUCT or PROFILE"
        
        print(f"  [PASS] Handled conflict -> {classification_conflict.primary_category.value}")
        print(f"  [PASS] Confidence: {classification_conflict.confidence:.2f}")
        
        # Test 5: Unknown page
        print("\n[TEST 5] Unknown page with no signals")
        classification_unknown = classifier.classify(
            url="https://example.com/random/page"
        )
        
        assert classification_unknown is not None, "Should produce classification"
        assert classification_unknown.preview_strategy["template_type"] == "landing", "Should default to landing template"
        
        print(f"  [PASS] Unknown page -> {classification_unknown.primary_category.value}")
        print(f"  [PASS] Default template: {classification_unknown.preview_strategy['template_type']}")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] All integration tests passed!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_flow()
    sys.exit(0 if success else 1)

