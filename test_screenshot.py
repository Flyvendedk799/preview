import json
from backend.services.playwright_screenshot import capture_screenshot_and_html

try:
    print("Capturing example.com...")
    screen, html, dom = capture_screenshot_and_html('https://example.com')
    print(f'DOM extraction success: keys={list(dom.keys())}')
    print(f'Top texts found: {len(dom.get("raw_top_texts", []))}')
    print(f'CTAs found: {len(dom.get("raw_ctas", []))}')
    if dom.get("raw_top_texts"):
        print(f'Sample Top Text: {dom["raw_top_texts"][0]}')
except Exception as e:
    print(f'Error: {e}')
