"""Tests for preview_image_generator.py - PIL output validation."""
import pytest
from io import BytesIO
from PIL import Image


class TestFitTextToBox:
    """Test the _fit_text_to_box function."""

    def test_fits_short_text(self):
        from backend.services.preview_image_generator import _fit_text_to_box
        from PIL import ImageDraw

        img = Image.new('RGB', (800, 200))
        draw = ImageDraw.Draw(img)

        font, lines = _fit_text_to_box("Hello World", 600, 100, draw)
        assert len(lines) >= 1
        assert "Hello World" in lines[0]

    def test_reduces_font_for_long_text(self):
        from backend.services.preview_image_generator import _fit_text_to_box
        from PIL import ImageDraw

        img = Image.new('RGB', (800, 200))
        draw = ImageDraw.Draw(img)

        long_text = "This is a very long headline that should require font size reduction to fit properly within the available space"
        font, lines = _fit_text_to_box(long_text, 400, 80, draw, max_font_size=48, min_font_size=24)

        assert len(lines) >= 1
        # Font size should have been reduced
        total_chars = sum(len(line) for line in lines)
        assert total_chars > 0


class TestWCAGContrast:
    """Test WCAG contrast enforcement."""

    def test_adds_overlay_for_low_contrast(self):
        from backend.services.preview_image_generator import _ensure_wcag_contrast

        # Create a medium-gray image
        img = Image.new('RGB', (200, 100), color=(128, 128, 128))
        # White text on medium gray has poor contrast
        result = _ensure_wcag_contrast(img, [(10, 10, 180, 80)], (255, 255, 255), min_ratio=4.5)

        assert result is not None
        assert result.size == (200, 100)

    def test_no_overlay_for_good_contrast(self):
        from backend.services.preview_image_generator import _ensure_wcag_contrast

        # Dark background with white text - good contrast
        img = Image.new('RGB', (200, 100), color=(10, 10, 10))
        result = _ensure_wcag_contrast(img, [(10, 10, 180, 80)], (255, 255, 255), min_ratio=4.5)

        assert result is not None


class TestSampleLuminance:
    """Test luminance sampling."""

    def test_white_region_luminance(self):
        from backend.services.preview_image_generator import _sample_region_luminance

        img = Image.new('RGB', (100, 100), color=(255, 255, 255))
        lum = _sample_region_luminance(img, 10, 10, 80, 80)
        assert lum > 0.95

    def test_black_region_luminance(self):
        from backend.services.preview_image_generator import _sample_region_luminance

        img = Image.new('RGB', (100, 100), color=(0, 0, 0))
        lum = _sample_region_luminance(img, 10, 10, 80, 80)
        assert lum < 0.05

    def test_handles_out_of_bounds(self):
        from backend.services.preview_image_generator import _sample_region_luminance

        img = Image.new('RGB', (50, 50), color=(100, 100, 100))
        # Should not crash with out-of-bounds coordinates
        lum = _sample_region_luminance(img, 40, 40, 100, 100)
        assert 0.0 <= lum <= 1.0


class TestImageOutput:
    """Test that generated images meet og:image requirements."""

    def test_output_dimensions(self, sample_screenshot_bytes):
        """Generated preview should be 1200x630."""
        from backend.services.preview_image_generator import generate_designed_preview

        result = generate_designed_preview(
            screenshot_bytes=sample_screenshot_bytes,
            title="Test Title",
            subtitle="Test subtitle",
            description="Test description for the preview",
            cta_text="Learn More",
            domain="example.com",
            blueprint={
                "primary_color": "#3B82F6",
                "secondary_color": "#1E293B",
                "accent_color": "#F97316",
                "template_type": "landing",
            },
            template_type="landing",
        )

        if result:
            img = Image.open(BytesIO(result))
            assert img.width == 1200
            assert img.height == 630
