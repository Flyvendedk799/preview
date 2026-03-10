# Model Selection — MyMetaView 10x Quality

**Reference:** `agents/founding-engineer/TECHNICAL_ARCHITECTURE_MYMETAVIEW_3.5.md` §1

## Code Alignment (AIL-112)

| Component | Model | Constant | Location |
|-----------|-------|----------|----------|
| Layout + reasoning (Stage 1–6) | `gpt-4o` | `MODEL_LAYOUT_REASONING` | `prompts/loader.py` |
| Brand extraction (logo detection) | `gpt-4o` | `MODEL_BRAND_EXTRACTION` | `prompts/loader.py` |
| Quality critic | `gpt-4o` | `MODEL_QUALITY_CRITIC` | `prompts/loader.py` |

**Do not downgrade** layout, reasoning, or brand extraction to gpt-4o-mini. Quality-critical paths use gpt-4o.

Value prop extractor remains gpt-4o-mini (cost-sensitive, non-critical).
