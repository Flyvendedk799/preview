"""
Test script for the new LAB color space gradient generator.
Generates sample gradients to verify smoothness and check for banding.
"""
from backend.services.gradient_generator import generate_smooth_gradient
from PIL import Image
import sys

def test_gradients():
    """Test various gradient configurations."""
    print("Testing LAB color space gradient generator...")
    
    # Test 1: Diagonal gradient (most common case)
    print("\n1. Testing diagonal gradient (135deg)...")
    gradient1 = generate_smooth_gradient(
        1200, 630,
        (71, 85, 105),   # #475569 (slate-600)
        (51, 65, 85),    # #334155 (slate-700)
        angle=135,
        style="linear"
    )
    gradient1.save("test_gradient_diagonal.png")
    print("   [OK] Saved: test_gradient_diagonal.png")
    
    # Test 2: Vertical gradient
    print("\n2. Testing vertical gradient (90deg)...")
    gradient2 = generate_smooth_gradient(
        1200, 630,
        (71, 85, 105),
        (51, 65, 85),
        angle=90,
        style="linear"
    )
    gradient2.save("test_gradient_vertical.png")
    print("   [OK] Saved: test_gradient_vertical.png")
    
    # Test 3: Horizontal gradient
    print("\n3. Testing horizontal gradient (0deg)...")
    gradient3 = generate_smooth_gradient(
        1200, 630,
        (71, 85, 105),
        (51, 65, 85),
        angle=0,
        style="linear"
    )
    gradient3.save("test_gradient_horizontal.png")
    print("   [OK] Saved: test_gradient_horizontal.png")
    
    # Test 4: Radial gradient
    print("\n4. Testing radial gradient...")
    gradient4 = generate_smooth_gradient(
        1200, 630,
        (71, 85, 105),
        (51, 65, 85),
        angle=0,
        style="radial"
    )
    gradient4.save("test_gradient_radial.png")
    print("   [OK] Saved: test_gradient_radial.png")
    
    # Test 5: High contrast gradient (most likely to show banding)
    print("\n5. Testing high contrast gradient (most challenging)...")
    gradient5 = generate_smooth_gradient(
        1200, 630,
        (255, 255, 255),  # White
        (0, 0, 0),        # Black
        angle=135,
        style="linear"
    )
    gradient5.save("test_gradient_high_contrast.png")
    print("   [OK] Saved: test_gradient_high_contrast.png")
    
    # Test 6: Colorful gradient
    print("\n6. Testing colorful gradient...")
    gradient6 = generate_smooth_gradient(
        1200, 630,
        (249, 115, 22),   # Orange (#F97316)
        (71, 85, 105),    # Slate
        angle=135,
        style="linear"
    )
    gradient6.save("test_gradient_colorful.png")
    print("   [OK] Saved: test_gradient_colorful.png")
    
    print("\n[OK] All gradient tests completed!")
    print("\nCheck the generated PNG files for:")
    print("   - Smooth color transitions")
    print("   - No visible banding")
    print("   - Proper gradient direction")
    print("   - Clean appearance (no noise artifacts)")
    
    return True

if __name__ == "__main__":
    try:
        success = test_gradients()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

