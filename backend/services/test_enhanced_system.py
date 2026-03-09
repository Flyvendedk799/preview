"""
Quick validation test for the 7-layer enhancement system.

Run this to verify all modules import correctly and basic functionality works.
"""

import sys
from io import BytesIO
from PIL import Image

def test_imports():
    """Test that all modules import successfully."""
    print("🧪 Testing imports...")
    
    try:
        from backend.services.visual_hierarchy_engine import VisualHierarchyEngine
        print("  ✅ visual_hierarchy_engine")
    except Exception as e:
        print(f"  ❌ visual_hierarchy_engine: {e}")
        return False
    
    try:
        from backend.services.depth_engine import DepthEngine, ElevationLevel
        print("  ✅ depth_engine")
    except Exception as e:
        print(f"  ❌ depth_engine: {e}")
        return False
    
    try:
        from backend.services.premium_typography_engine import PremiumTypographyEngine
        print("  ✅ premium_typography_engine")
    except Exception as e:
        print(f"  ❌ premium_typography_engine: {e}")
        return False
    
    try:
        from backend.services.texture_engine import TextureEngine, TextureType
        print("  ✅ texture_engine")
    except Exception as e:
        print(f"  ❌ texture_engine: {e}")
        return False
    
    try:
        from backend.services.composition_engine import CompositionEngine, GridType
        print("  ✅ composition_engine")
    except Exception as e:
        print(f"  ❌ composition_engine: {e}")
        return False
    
    try:
        from backend.services.context_intelligence import ContextIntelligenceEngine
        print("  ✅ context_intelligence")
    except Exception as e:
        print(f"  ❌ context_intelligence: {e}")
        return False
    
    try:
        from backend.services.quality_assurance_engine import QualityAssuranceEngine
        print("  ✅ quality_assurance_engine")
    except Exception as e:
        print(f"  ❌ quality_assurance_engine: {e}")
        return False
    
    try:
        from backend.services.enhanced_preview_orchestrator import (
            EnhancedPreviewOrchestrator,
            generate_exceptional_preview
        )
        print("  ✅ enhanced_preview_orchestrator")
    except Exception as e:
        print(f"  ❌ enhanced_preview_orchestrator: {e}")
        return False
    
    print("✅ All imports successful!\n")
    return True


def test_basic_functionality():
    """Test basic functionality of each layer."""
    print("🧪 Testing basic functionality...\n")
    
    # Layer 1: Visual Hierarchy
    print("1️⃣ Testing Visual Hierarchy Engine...")
    try:
        from backend.services.visual_hierarchy_engine import VisualHierarchyEngine
        
        engine = VisualHierarchyEngine()
        test_elements = [
            {"id": "title", "content_type": "headline", "content": "Test", "priority_score": 1.0, "purpose": "hook"},
            {"id": "desc", "content_type": "description", "content": "Description", "priority_score": 0.5, "purpose": "benefit"}
        ]
        hierarchy = engine.calculate_hierarchy(test_elements, "balanced")
        assert len(hierarchy) == 2
        print(f"  ✅ Calculated hierarchy for {len(hierarchy)} elements")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # Layer 2: Depth & Shadows
    print("\n2️⃣ Testing Depth Engine...")
    try:
        from backend.services.depth_engine import DepthEngine, ElevationLevel
        
        depth_engine = DepthEngine(light_mode=True)
        shadow = depth_engine.get_shadow_composition(ElevationLevel.RAISED, "modern")
        css = shadow.to_css()
        assert "rgba" in css
        print(f"  ✅ Generated shadow composition")
        print(f"     Preview: {css[:80]}...")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # Layer 3: Premium Typography
    print("\n3️⃣ Testing Premium Typography Engine...")
    try:
        from backend.services.premium_typography_engine import PremiumTypographyEngine
        
        typo_engine = PremiumTypographyEngine()
        pairing = typo_engine.select_font_pairing("authoritative", "fintech")
        scale = typo_engine.get_type_scale(16, "golden_ratio")
        assert len(scale) > 5
        print(f"  ✅ Selected font pairing: {pairing.name}")
        print(f"     Headline: {pairing.headline_fonts[0]}")
        print(f"     Type scale: {list(scale.keys())[:5]}...")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # Layer 4: Textures
    print("\n4️⃣ Testing Texture Engine...")
    try:
        from backend.services.texture_engine import (
            TextureEngine, TextureType, TextureConfig
        )
        
        texture_engine = TextureEngine()
        config = TextureConfig(
            texture_type=TextureType.FILM_GRAIN,
            intensity=0.05,
            scale=1.0,
            opacity=30,
            blend_mode="overlay"
        )
        texture = texture_engine.generate_texture(100, 100, config)
        assert texture.size == (100, 100)
        print(f"  ✅ Generated {config.texture_type.value} texture: {texture.size}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # Layer 5: Composition
    print("\n5️⃣ Testing Composition Engine...")
    try:
        from backend.services.composition_engine import CompositionEngine, GridType
        
        comp_engine = CompositionEngine()
        test_elements = [
            {"id": "title", "content_type": "headline", "content": "Test", "priority_score": 1.0},
            {"id": "desc", "content_type": "description", "content": "Description", "priority_score": 0.5}
        ]
        zones = comp_engine.calculate_layout(test_elements, GridType.SWISS, "balanced")
        assert len(zones) > 0
        print(f"  ✅ Created {len(zones)} layout zones")
        for zone in zones[:2]:
            print(f"     {zone.purpose}: ({zone.x}, {zone.y}) {zone.width}x{zone.height}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # Layer 6: Context Intelligence
    print("\n6️⃣ Testing Context Intelligence Engine...")
    try:
        from backend.services.context_intelligence import ContextIntelligenceEngine
        
        context_engine = ContextIntelligenceEngine()
        recommendation = context_engine.get_design_recommendation(
            url="https://stripe.com",
            content_keywords=["payment", "api"]
        )
        print(f"  ✅ Industry classification: {recommendation.industry.value}")
        print(f"     Audience: {recommendation.audience.value}")
        print(f"     Typography: {recommendation.typography}")
        print(f"     Confidence: {recommendation.confidence:.2f}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # Layer 7: Quality Assurance
    print("\n7️⃣ Testing Quality Assurance Engine...")
    try:
        from backend.services.quality_assurance_engine import QualityAssuranceEngine
        
        qa_engine = QualityAssuranceEngine()
        test_image = Image.new('RGB', (1200, 630), (255, 255, 255))
        test_design = {
            "colors": {"text": (0, 0, 0), "background": (255, 255, 255)},
            "fonts": {"headline_size": 72, "body_size": 16, "line_height": 1.5},
            "line_length": 65
        }
        quality = qa_engine.assess_quality(test_image, test_design)
        print(f"  ✅ Quality assessment: {quality.grade} ({quality.overall:.2f})")
        print(f"     Accessibility: {quality.accessibility:.2f}")
        print(f"     Visual Balance: {quality.visual_balance:.2f}")
        print(f"     Typography: {quality.typography:.2f}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    print("\n✅ All basic functionality tests passed!\n")
    return True


def test_orchestrator():
    """Test the orchestrator integration."""
    print("🎭 Testing Enhanced Preview Orchestrator...\n")
    
    try:
        from backend.services.enhanced_preview_orchestrator import (
            EnhancedPreviewOrchestrator,
            EnhancedPreviewConfig
        )
        
        # Create test screenshot
        test_screenshot = Image.new('RGB', (1200, 800), (240, 240, 245))
        screenshot_buffer = BytesIO()
        test_screenshot.save(screenshot_buffer, format='PNG')
        screenshot_bytes = screenshot_buffer.getvalue()
        
        # Initialize orchestrator
        config = EnhancedPreviewConfig(
            enable_ab_testing=False  # Disable for quick test
        )
        orchestrator = EnhancedPreviewOrchestrator(config)
        
        print("  ✅ Orchestrator initialized")
        print(f"     Layers enabled: {sum([config.enable_hierarchy, config.enable_depth, config.enable_premium_typography, config.enable_textures, config.enable_composition, config.enable_context, config.enable_qa])}/7")
        
        # Note: Full generation test requires the existing preview_image_generator
        # which may have dependencies. Test initialization only.
        
        print("\n✅ Orchestrator test passed!\n")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("\n" + "="*60)
    print("🚀 7-Layer Enhancement System Validation")
    print("="*60 + "\n")
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed!")
        return False
    
    # Test basic functionality
    if not test_basic_functionality():
        print("\n❌ Functionality tests failed!")
        return False
    
    # Test orchestrator
    if not test_orchestrator():
        print("\n❌ Orchestrator test failed!")
        return False
    
    # Success!
    print("="*60)
    print("✅ ALL VALIDATION TESTS PASSED!")
    print("="*60)
    print("\n🎉 The 7-layer enhancement system is ready for use!")
    print("\nNext steps:")
    print("  1. Review ENHANCEMENT_LAYERS_INTEGRATION_GUIDE.md")
    print("  2. Review IMPLEMENTATION_SUMMARY.md")
    print("  3. Integrate into your demo endpoint")
    print("  4. Generate sample previews for comparison")
    print("\n")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
