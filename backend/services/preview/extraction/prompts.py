"""Specialized extraction prompts by page type (Phase 4.1).

Plan calls for splitting the monolithic extraction prompt into:
  - general/marketing
  - product/e-commerce
  - profile/personal brand

Each prompt asks for a tight, validated JSON schema. The classifier picks the
right prompt up front; ``validators`` then enforces low-information rejection
and the title fallback chain.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional, Tuple


class PageType(str, Enum):
    GENERAL_MARKETING = "general_marketing"
    PRODUCT_ECOMMERCE = "product_ecommerce"
    PROFILE = "profile"
    DOCS = "docs"


_ECOMMERCE_HINTS = (
    "/product", "/products/", "/shop/", "/p/", "/sku/", "/buy/", "checkout",
    "add-to-cart", "cart.json"
)
_PROFILE_HINTS = (
    "/about", "/me", "/team/", "/people/", "/profile", "/u/",
    "linkedin.com/in/", "twitter.com/", "x.com/", "github.com/",
)
_DOCS_HINTS = (
    "/docs", "/documentation", "/learn", "/guide", "/handbook",
    "/manual", "/reference",
)


_TITLE_NAME_RE = re.compile(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*[-|–—]")


def classify_page_type(url: str, html_snippet: Optional[str] = None) -> PageType:
    """Cheap rule-based classifier used to pick the prompt."""
    url_lower = (url or "").lower()
    if any(hint in url_lower for hint in _ECOMMERCE_HINTS):
        return PageType.PRODUCT_ECOMMERCE
    if any(hint in url_lower for hint in _DOCS_HINTS):
        return PageType.DOCS
    if any(hint in url_lower for hint in _PROFILE_HINTS):
        return PageType.PROFILE

    if html_snippet:
        html_lower = html_snippet.lower()
        if "schema.org/product" in html_lower or '"@type":"product"' in html_lower:
            return PageType.PRODUCT_ECOMMERCE
        if "schema.org/person" in html_lower or '"@type":"person"' in html_lower:
            return PageType.PROFILE
        title_match = re.search(r"<title>([^<]{1,180})</title>", html_lower)
        if title_match and _TITLE_NAME_RE.match(title_match.group(1)):
            return PageType.PROFILE

    return PageType.GENERAL_MARKETING


GENERAL_MARKETING_PROMPT = """You are a senior brand strategist. Read the page and return JSON ONLY.

REQUIRED schema:
{
  "title": string,            // The hook the brand actually leads with (max 80 chars).
                              // Reject navigation labels ("Home", "About"), domain names,
                              // and generic placeholders ("Welcome to ...").
  "subtitle": string|null,    // 1-line supporting line (max 100 chars). Null if missing.
  "description": string,      // 1-3 sentence value prop. Plain prose, no marketing fluff.
  "tags": string[],           // 3-6 lowercase noun phrases describing the offer.
  "cta_text": string|null,    // The actual primary CTA copy on the page (e.g. "Get started").
  "social_proof": string|null,// Numeric proof if present ("Trusted by 5,000 teams"); else null.
  "primary_color_hex": string,
  "secondary_color_hex": string,
  "accent_color_hex": string
}

Quality rules:
- Prefer hero / above-the-fold copy over footer or nav text.
- Strip emojis.
- If the source is mostly navigation, return title:"" and we will fall back.
"""

PRODUCT_ECOMMERCE_PROMPT = """You are a product copy specialist. Return JSON ONLY.

REQUIRED schema:
{
  "title": string,            // Product name (no price). Max 80 chars.
  "subtitle": string|null,    // Tagline / category. Max 100 chars.
  "description": string,      // 1-3 sentence summary of what the product is + key benefit.
  "tags": string[],           // 3-6 attributes (material, audience, occasion).
  "cta_text": string|null,    // "Add to bag", "Pre-order", etc.
  "price": string|null,       // Display string ("$129" / "Free"). Null if not listed.
  "social_proof": string|null,// Star rating, review count, "Editor's pick", etc.
  "primary_color_hex": string,
  "secondary_color_hex": string,
  "accent_color_hex": string
}

Quality rules:
- Title must be the product name, not the brand or category.
- Description must NOT be a list of bullet points; convert bullets to prose.
- If multiple variants, summarize ("available in 3 colors") instead of listing.
"""

PROFILE_PROMPT = """You are a personal-brand editor. Return JSON ONLY.

REQUIRED schema:
{
  "title": string,            // The person's name as it appears on the page. Max 60 chars.
  "subtitle": string|null,    // Their role + company ("Designer at Stripe"). Max 90 chars.
  "description": string,      // 1-3 sentence bio in their voice. Avoid third-person fluff.
  "tags": string[],           // 3-6 areas of focus (skills, topics).
  "cta_text": string|null,    // CTA ("Subscribe", "Hire me"); null if absent.
  "social_proof": string|null,// "10k followers", "Author of X", "Featured in Y".
  "primary_color_hex": string,
  "secondary_color_hex": string,
  "accent_color_hex": string
}

Quality rules:
- Reject "About me" / "Home" / generic page titles as the name; prefer the visible name.
- description must NOT just repeat the name.
"""

DOCS_PROMPT = """You are a docs editor. Return JSON ONLY.

REQUIRED schema:
{
  "title": string,            // The article / section title (max 80 chars).
  "subtitle": string|null,    // Section path or product label. Null if missing.
  "description": string,      // 1-3 sentence summary of what the page teaches.
  "tags": string[],           // 3-6 technical concepts covered.
  "cta_text": string|null,    // "Read more", "Get the SDK", etc.
  "social_proof": string|null,
  "primary_color_hex": string,
  "secondary_color_hex": string,
  "accent_color_hex": string
}

Quality rules:
- Treat code blocks as evidence, not as title material.
- description must read as prose; do not output bullet lists.
"""


_PROMPT_BY_TYPE = {
    PageType.GENERAL_MARKETING: GENERAL_MARKETING_PROMPT,
    PageType.PRODUCT_ECOMMERCE: PRODUCT_ECOMMERCE_PROMPT,
    PageType.PROFILE: PROFILE_PROMPT,
    PageType.DOCS: DOCS_PROMPT,
}


def get_extraction_prompt(
    page_type: PageType,
    *,
    retry_critique: Optional[str] = None,
) -> Tuple[str, PageType]:
    """Return ``(prompt, resolved_type)``.

    When a retry critique is supplied (Phase 1.2 contract), it is appended
    to the prompt so the next attempt produces a different output.
    """
    base = _PROMPT_BY_TYPE.get(page_type, GENERAL_MARKETING_PROMPT)
    if retry_critique:
        base = (
            base
            + "\n\nPrevious attempt was rejected. Apply this critique and "
              "produce a materially different output:\n"
            + retry_critique.strip()
        )
    return base, page_type
