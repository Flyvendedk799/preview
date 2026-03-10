"""
Centralized prompt library loader for MyMetaView 10x generation quality.

Loads prompts from backend/prompts/ with fallback to inline defaults.
Reference: TECHNICAL_ARCHITECTURE_MYMETAVIEW_3.5.md §2
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent


def _read_text(path: Path) -> Optional[str]:
    """Read text file, return None if not found."""
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception as e:
        logger.warning(f"Could not read prompt file {path}: {e}")
        return None


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    """Read JSON file, return None if not found or invalid."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Could not read JSON {path}: {e}")
        return None


def get_layout_stage1_prompt(few_shot_examples: Optional[str] = None) -> str:
    """Load Stage 1-3 layout reasoning prompt with optional few-shot examples."""
    path = _PROMPTS_DIR / "layout_reasoning" / "system_layout_stage1.txt"
    content = _read_text(path)
    if content is None:
        return ""
    if few_shot_examples is None:
        few_shot_examples = _format_few_shot_examples()
    return content.replace("{few_shot_examples}", few_shot_examples)


def _format_few_shot_examples() -> str:
    """Format few-shot examples from JSON for prompt injection."""
    path = _PROMPTS_DIR / "layout_reasoning" / "few_shot_examples.json"
    data = _read_json(path)
    if not data:
        return ""

    lines = []
    for layout_type, examples in data.items():
        if not isinstance(examples, list):
            continue
        for i, ex in enumerate(examples[:3], 1):  # Max 3 per type
            if isinstance(ex, dict):
                lines.append(f"EXAMPLE ({layout_type}):")
                lines.append(json.dumps(ex, indent=2))
                lines.append("")
    return "\n".join(lines).strip() if lines else ""


def get_layout_stage4_prompt(
    regions_json: str,
    page_type: str,
    primary: str,
    secondary: str,
    accent: str,
    design_dna_json: str,
) -> str:
    """Load Stage 4-6 layout reasoning prompt with template variables filled."""
    path = _PROMPTS_DIR / "layout_reasoning" / "system_layout_stage4.txt"
    content = _read_text(path)
    if content is None:
        return ""
    return content.format(
        regions_json=regions_json,
        page_type=page_type,
        primary=primary,
        secondary=secondary,
        accent=accent,
        design_dna_json=design_dna_json,
    )


def get_brand_extraction_prompt() -> str:
    """Load brand extraction (logo detection) system prompt."""
    path = _PROMPTS_DIR / "brand_extraction" / "system_brand.txt"
    content = _read_text(path)
    return content or ""


def get_quality_critic_prompt() -> str:
    """Load quality critic system prompt."""
    path = _PROMPTS_DIR / "quality_critic" / "system_critic.txt"
    content = _read_text(path)
    return content or ""


# Model selection constants (per TECHNICAL_ARCHITECTURE_MYMETAVIEW_3.5.md §1)
MODEL_LAYOUT_REASONING = "gpt-4o"
MODEL_BRAND_EXTRACTION = "gpt-4o"
MODEL_QUALITY_CRITIC = "gpt-4o"
