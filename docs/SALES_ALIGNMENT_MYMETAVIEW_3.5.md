# MyMetaView 3.5 — Technical Fact Sheet for Sales & Customer Success

**Purpose:** Align sales and customer success messaging with engineering reality. Use these facts when positioning 3.5 improvements.

**Reference:** AIL-106, [QUALITY_PROFILE_SPEC.md](./QUALITY_PROFILE_SPEC.md), [VISIBLE_IMPROVEMENTS_SUMMARY.md](../VISIBLE_IMPROVEMENTS_SUMMARY.md)

---

## 1. 10x Generation Quality

### Quality Profiles
- **fast** (~2–4s): Simple pages, landing, about, blogs — good quality, low cost
- **balanced** (~4–8s): Product/feature pages — better quality, multi-agent + UI extraction
- **ultra** (~8–15s): Pricing, enterprise, docs, complex layouts — best quality, strict thresholds
- **auto**: System picks the right profile based on URL complexity (no user config needed)

### Technical Basis
- Multi-modal fusion: HTML + semantic analysis + AI vision with confidence scoring
- Quality thresholds: 0.78 (fast) → 0.82 (balanced) → 0.88 (ultra)
- Target quality enforcement on ultra: min 0.85 overall, 0.75 visual, 0.72 fidelity
- Uses best source per field (HTML when available, vision when needed) — faster and more accurate

### Sales Angle
- "10x better generations" = quality profiles + multi-modal fusion + confidence-based selection
- "Right quality for the page" = auto mode picks fast/balanced/ultra by URL
- "Enterprise-ready quality" = ultra profile for pricing, docs, complex pages

---

## 2. UX Improvements

### Latency
- fast: ~2–4s
- balanced: ~4–8s
- ultra: ~8–15s
- HTML-first extraction when metadata exists → instant for many sites

### User-Facing
- Auto mode: no configuration; system adapts to page type
- Progressive enhancement: starts with fast sources, adds vision only when needed
- Visible improvements: more accurate previews, more complete fields, consistent output

### Sales Angle
- "Faster when it matters" = HTML-first, quality profiles tuned for speed
- "Zero-config quality" = auto mode
- "Better UX" = accurate previews that match the page, fewer empty/mismatched fields

---

## 3. Reliability

### Caching
- Cache key: `demo:preview:v3:{mode}:{url_hash}`
- TTL: 24 hours (configurable)
- Invalidation: URL change or admin toggle

### Fallbacks
- Multiple extraction sources (HTML → semantic → vision)
- Confidence scoring picks best source per field
- Soft pass allowed on fast/balanced for edge cases; ultra enforces strict quality

### Sales Angle
- "Reliable previews" = multi-source fallbacks, deterministic caching
- "Works for more sites" = handles perfect metadata, missing metadata, poor HTML, dynamic content
- "Production-ready" = caching, invalidation, quality enforcement

---

## Quick Reference Table

| Pillar      | Technical Reality                          | Sales Message                          |
|-------------|--------------------------------------------|----------------------------------------|
| 10x quality | Quality profiles + multi-modal fusion      | 10x better generations, right quality per page |
| UX          | Auto mode, 2–15s latency, HTML-first        | Faster, zero-config, accurate previews  |
| Reliability | Caching, fallbacks, confidence scoring      | Reliable, works for more sites          |

---

## Do Not Overclaim

- Avoid specific percentage claims (e.g. "40% faster") unless backed by measured benchmarks
- "10x" refers to generation quality improvement, not raw speed
- Latency ranges are approximate; actual times depend on page complexity and infrastructure
