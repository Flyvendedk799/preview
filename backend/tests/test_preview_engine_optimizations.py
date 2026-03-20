"""Tests for preview_engine 400% optimization: parallelization, caching, early exits."""

import pytest
from backend.services.preview_engine import PreviewEngine, PreviewEngineConfig


class TestHasRichOgMetadata:
    """Tests for OG-rich early exit detection."""

    def test_detects_rich_og_metadata(self):
        """Pages with og:title, og:description, og:image trigger fast path."""
        config = PreviewEngineConfig(is_demo=True)
        engine = PreviewEngine(config)
        html = """
        <html><head>
        <meta property="og:title" content="My Great Product - Best in Class">
        <meta property="og:description" content="This is a comprehensive description that has at least forty characters in it for the threshold.">
        <meta property="og:image" content="https://example.com/image.png">
        </head></html>
        """
        assert engine._has_rich_og_metadata(html) is True

    def test_rejects_short_title(self):
        """Short og:title does not qualify."""
        config = PreviewEngineConfig(is_demo=True)
        engine = PreviewEngine(config)
        html = """
        <html><head>
        <meta property="og:title" content="Short">
        <meta property="og:description" content="This is a comprehensive description that has at least forty characters in it for the threshold.">
        <meta property="og:image" content="https://example.com/image.png">
        </head></html>
        """
        assert engine._has_rich_og_metadata(html) is False

    def test_rejects_short_description(self):
        """Short og:description does not qualify."""
        config = PreviewEngineConfig(is_demo=True)
        engine = PreviewEngine(config)
        html = """
        <html><head>
        <meta property="og:title" content="My Great Product - Best in Class">
        <meta property="og:description" content="Too short">
        <meta property="og:image" content="https://example.com/image.png">
        </head></html>
        """
        assert engine._has_rich_og_metadata(html) is False

    def test_rejects_missing_image(self):
        """Missing og:image does not qualify."""
        config = PreviewEngineConfig(is_demo=True)
        engine = PreviewEngine(config)
        html = """
        <html><head>
        <meta property="og:title" content="My Great Product - Best in Class">
        <meta property="og:description" content="This is a comprehensive description that has at least forty characters in it for the threshold.">
        </head></html>
        """
        assert engine._has_rich_og_metadata(html) is False

    def test_handles_content_before_property_order(self):
        """Alternate meta order content=... property=... is supported."""
        config = PreviewEngineConfig(is_demo=True)
        engine = PreviewEngine(config)
        html = """
        <html><head>
        <meta content="My Great Product - Best in Class" property="og:title">
        <meta content="This is a comprehensive description that has at least forty characters in it for the threshold." property="og:description">
        <meta content="https://example.com/image.png" property="og:image">
        </head></html>
        """
        assert engine._has_rich_og_metadata(html) is True

    def test_empty_html_returns_false(self):
        """Empty or minimal HTML returns False."""
        config = PreviewEngineConfig(is_demo=True)
        engine = PreviewEngine(config)
        assert engine._has_rich_og_metadata("") is False
        assert engine._has_rich_og_metadata("<html></html>") is False
