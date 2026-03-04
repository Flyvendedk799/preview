import sys
import os

# Ensure backend modules are loadable
sys.path.append(os.path.abspath("."))
from backend.services.preview_image_generator import _generate_hero_template

# Mock data to simulate Playwright return payload
screenshot_bytes = b"" # empty
title = "SuperAI 2026"
subtitle = "Build Better Apps Today"
description = "A new paradigm for scientific AI preview generation."

primary_color = (37, 99, 235)
secondary_color = (30, 64, 175)
accent_color = (245, 158, 11)

credibility_items = [{"type": "users", "value": "100k+ Users"}]
tags = ["AI", "Composition", "Science"]
primary_image_base64 = None

dom_data = {
    "raw_top_texts": [
        {"tag": "H1", "text": "SuperAI 2026: The Next Era of Video Preview", "bounds": {"width": 800, "height": 60}},
        {"tag": "P", "text": "Discover out-of-the-box compositing without hallucinations.", "bounds": {"width": 800, "height": 30}}
    ],
    "raw_ctas": [
        {"tag": "A", "text": "Start Free Trial", "bounds": {"width": 200, "height": 48}, "computed_styles": {"backgroundColor": "#f97316"}}
    ]
}

try:
    print("Testing Hero Template Generation...")
    img_bytes = _generate_hero_template(
        screenshot_bytes=screenshot_bytes,
        title=title,
        subtitle=subtitle,
        description=description,
        primary_color=primary_color,
        secondary_color=secondary_color,
        accent_color=accent_color,
        credibility_items=credibility_items,
        tags=tags,
        primary_image_base64=primary_image_base64,
        dom_data=dom_data
    )
    print(f"Success! Generated {len(img_bytes)} bytes image.")
    with open("test_hero_composited.png", "wb") as f:
        f.write(img_bytes)
        print("Saved to test_hero_composited.png")
except Exception as e:
    print(f"Hero layout failed: {e}")
