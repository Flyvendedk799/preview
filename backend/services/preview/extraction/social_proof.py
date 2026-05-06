"""Social-proof extraction pass (Phase 4.4).

Run a regex + DOM pass for numeric proof signals **before** falling back to
AI. The plan's exit gate is:
  - "Social-proof numeric extraction precision ≥ 80% when numbers are present."
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from typing import List, Optional


@dataclass
class NumericProof:
    raw: str
    value: str  # canonical form ("5,000+ teams")
    label: str  # what the number describes ("teams")
    source: str  # 'dom' | 'regex'


# ----- Regex passes ---------------------------------------------------------

_PROOF_PATTERNS = [
    # "Trusted by 5,000+ teams"
    (r"(?:trusted|loved|used|chosen)\s+by\s+([0-9][0-9,]{2,}\+?)\s+([a-z][a-z\s]{1,40})",
     "regex"),
    # "10,000 customers can't be wrong"
    (r"\b([0-9][0-9,]{2,}\+?)\s+(customers|users|teams|companies|developers|"
     r"businesses|fans|subscribers|followers|downloads|installs|members|sites)\b",
     "regex"),
    # "Rated 4.8 by 10,000 reviewers"
    (r"\b(?:rated|rating)\s+([0-9](?:\.[0-9])?)\s*(?:/\s*5)?\s+(?:by|from)?\s*"
     r"([0-9][0-9,]{1,}\+?)?\s*(reviewers|reviews|customers)?",
     "regex"),
    # "★ 4.7"
    (r"(?:★|⭐)\s*([0-9]\.[0-9])",
     "regex"),
    # "Featured in TechCrunch"
    (r"\bfeatured\s+in\s+([A-Z][A-Za-z0-9 &]{2,40})",
     "regex"),
    # "100M downloads"
    (r"\b([0-9]+(?:\.[0-9]+)?[KMB]\+?)\s+(downloads|users|customers|installs|signups|"
     r"members|teams|companies|reviewers|reviews)\b",
     "regex"),
]


def _normalize_proof(value: str, label: str) -> str:
    value = value.strip().rstrip(",.;")
    label = label.strip().rstrip(",.;")
    if not label:
        return value
    return f"{value} {label}".strip()


def extract_social_proof(html: str) -> List[NumericProof]:
    """Return numeric proofs found in the HTML. Order: DOM first, regex second."""
    if not html:
        return []
    text = unescape(_strip_tags(html))
    proofs: List[NumericProof] = []
    seen: set = set()

    # DOM pass: schema.org AggregateRating
    dom_matches = re.findall(
        r'"aggregateRating".{0,400}?"ratingValue"\s*:\s*"?([0-9]\.[0-9])"?'
        r'(?:.{0,400}?"reviewCount"\s*:\s*"?([0-9][0-9,]+)"?)?',
        html, re.IGNORECASE | re.DOTALL,
    )
    for rating, review_count in dom_matches:
        normalized = f"{rating} ★"
        if review_count:
            normalized += f" ({review_count} reviews)"
        if normalized in seen:
            continue
        seen.add(normalized)
        proofs.append(NumericProof(
            raw=f"AggregateRating={rating} reviews={review_count}",
            value=normalized,
            label="rating",
            source="dom",
        ))

    # Regex pass over visible text
    for pattern, source in _PROOF_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            groups = [g for g in match.groups() if g]
            if not groups:
                continue
            value = groups[0]
            label = groups[1] if len(groups) > 1 else ""
            canonical = _normalize_proof(value, label)
            # Star ratings come through with no label; preserve the ★ glyph
            # so the canonical form stays meaningful.
            if "★" in match.group(0) and "★" not in canonical:
                canonical = f"{canonical} ★"
                label = label or "rating"
            if canonical in seen or len(canonical) < 3:
                continue
            seen.add(canonical)
            proofs.append(NumericProof(
                raw=match.group(0),
                value=canonical,
                label=label or "metric",
                source=source,
            ))

    return proofs


def first_numeric_proof(html: str) -> Optional[NumericProof]:
    proofs = extract_social_proof(html)
    return proofs[0] if proofs else None


def _strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)
