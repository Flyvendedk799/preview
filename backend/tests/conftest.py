"""Shared test fixtures for backend tests."""
import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO
from PIL import Image


@pytest.fixture
def sample_screenshot_bytes():
    """Generate a minimal valid PNG screenshot for testing."""
    img = Image.new('RGB', (1200, 630), color=(255, 255, 255))
    # Add some colored regions to simulate page content
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    # Header area
    draw.rectangle([(0, 0), (1200, 80)], fill=(30, 30, 50))
    # Logo area
    draw.rectangle([(20, 15), (120, 65)], fill=(59, 130, 246))
    # Main heading area
    draw.rectangle([(100, 150), (800, 220)], fill=(20, 20, 30))
    # CTA button
    draw.rectangle([(100, 300), (300, 350)], fill=(249, 115, 22))

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


@pytest.fixture
def sample_html():
    """Sample HTML content for testing brand/hero extraction."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Acme Corp - Build Better Software</title>
        <meta property="og:title" content="Acme Corp - Build Better Software" />
        <meta property="og:description" content="Ship 10x faster with AI-powered development tools" />
        <meta property="og:image" content="https://acme.com/og-image.jpg" />
        <meta name="twitter:image" content="https://acme.com/twitter-card.jpg" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png" />
        <link rel="icon" href="/favicon.ico" />
    </head>
    <body>
        <header>
            <nav>
                <a href="/" class="logo">
                    <img src="/logo.svg" alt="Acme Logo" width="120" height="40" />
                </a>
            </nav>
        </header>
        <section class="hero">
            <h1>Build Better Software</h1>
            <p>Ship 10x faster with AI-powered development tools</p>
            <p>Trusted by 50,000+ developers worldwide</p>
            <img src="/hero-image.jpg" alt="Product screenshot" width="800" height="400" />
            <a href="/signup" class="cta">Start Free Trial</a>
        </section>
        <section class="social-proof">
            <p>4.9★ (2,847 reviews)</p>
        </section>
    </body>
    </html>
    """


@pytest.fixture
def sample_stage_1_2_3_response():
    """Sample GPT-4o response for Stage 1-2-3."""
    return {
        "reasoning_chain": {
            "page_type_decision": "SaaS company homepage with clear value proposition",
            "individual_vs_company": "company - product features and 'we' language",
            "headline_selection": "Main hero headline describes core value",
            "validation": "All signals consistent with SaaS landing page"
        },
        "page_type": "saas",
        "primary_headline": "Build Better Software",
        "credibility_signals": "Trusted by 50,000+ developers worldwide",
        "value_statement": "Ship 10x faster with AI-powered development tools",
        "detected_person_name": None,
        "is_individual_profile": False,
        "company_indicators": ["product features", "pricing", "we language"],
        "regions": [
            {
                "id": "r1",
                "content_type": "headline",
                "raw_content": "Build Better Software",
                "bbox": {"x": 0.08, "y": 0.24, "width": 0.58, "height": 0.11},
                "purpose": "headline",
                "marketing_value": "high",
                "why_it_matters": "Primary value proposition",
                "visual_weight": "hero",
                "priority_score": 0.95,
                "is_logo": False
            },
            {
                "id": "r2",
                "content_type": "logo",
                "raw_content": "Acme",
                "bbox": {"x": 0.02, "y": 0.02, "width": 0.08, "height": 0.08},
                "purpose": "identity",
                "marketing_value": "medium",
                "why_it_matters": "Brand recognition",
                "visual_weight": "secondary",
                "priority_score": 0.7,
                "is_logo": True
            }
        ],
        "detected_palette": {
            "primary": "#3B82F6",
            "secondary": "#1E293B",
            "accent": "#F97316"
        },
        "detected_logo": {
            "region_id": "r2",
            "confidence": 0.9
        },
        "design_dna": {
            "style": "minimalist",
            "mood": "balanced",
            "formality": 0.7,
            "typography_personality": "authoritative",
            "color_emotion": "trust",
            "spacing_feel": "spacious",
            "brand_adjectives": ["modern", "professional", "clean"],
            "design_reasoning": "Clean design with blue tones builds trust"
        },
        "analysis_confidence": 0.92
    }


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client that returns predictable responses."""
    with patch('backend.services.preview_reasoning.OpenAI') as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        yield mock_client
