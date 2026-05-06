#!/usr/bin/env python3
"""Reproducible runner for the demo preview engine corpus.

This is the script the plan calls "reproducible run command/script". It
walks the golden corpus, calls the engine, and writes per-URL outputs into
``artifacts/baseline/<date>/``. The same script is invoked from the nightly
CI workflow (Phase 7) to drive the regression dashboard.

Usage:
    python -m backend.scripts.preview_engine.run_corpus \\
        --output-dir artifacts/baseline \\
        --max-urls 5  # smoke run
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("corpus_runner")


def _import_engine():
    """Import lazily so unit tests can run without the full backend stack."""
    from backend.services.preview_engine import (
        PreviewEngine,
        PreviewEngineConfig,
    )
    return PreviewEngine, PreviewEngineConfig


def _import_corpus():
    from backend.services.preview.corpus import (
        get_corpus,
        get_corpus_by_category,
        GoldenCorpusCategory,
        GoldenURL,
    )
    return get_corpus, get_corpus_by_category, GoldenCorpusCategory, GoldenURL


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the golden corpus")
    parser.add_argument("--output-dir", default="artifacts/baseline",
                        help="Where to write per-URL artifacts")
    parser.add_argument("--max-urls", type=int, default=0,
                        help="Optional cap; 0 = whole corpus")
    parser.add_argument("--include-shadow", action="store_true",
                        help="Include the rotating shadow corpus")
    parser.add_argument("--category", default=None,
                        help="Restrict to a single category")
    parser.add_argument("--quality-mode", default="balanced",
                        choices=["fast", "balanced", "ultra"])
    parser.add_argument("--workers", type=int, default=2,
                        help="Concurrent jobs (default 2)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Just print the corpus and exit")
    return parser.parse_args(argv)


def make_run_dir(base: str) -> Path:
    today = datetime.utcnow().strftime("%Y-%m-%d-%H%M%S")
    path = Path(base) / today
    path.mkdir(parents=True, exist_ok=True)
    return path


def select_corpus(args: argparse.Namespace):
    get_corpus, get_corpus_by_category, GoldenCorpusCategory, GoldenURL = _import_corpus()
    if args.category:
        category = GoldenCorpusCategory(args.category)
        urls = get_corpus_by_category(category, include_shadow=args.include_shadow)
    else:
        urls = get_corpus(include_shadow=args.include_shadow)
    if args.max_urls and args.max_urls > 0:
        urls = urls[: args.max_urls]
    return urls


def run_single(
    *,
    entry,
    output_dir: Path,
    quality_mode: str,
) -> Dict[str, Any]:
    PreviewEngine, PreviewEngineConfig = _import_engine()
    started = time.time()
    record: Dict[str, Any] = {
        "url": entry.url,
        "category": entry.category.value,
        "expected_template_type": entry.expected_template_type,
        "expected_title_keywords": list(entry.expected_title_keywords),
        "started_at": datetime.utcnow().isoformat(),
    }

    try:
        config = PreviewEngineConfig(
            is_demo=True,
            enable_brand_extraction=True,
            enable_ai_reasoning=True,
            enable_composited_image=True,
            enable_cache=False,
        )
        engine = PreviewEngine(config)
        result = engine.generate(entry.url, cache_key_prefix=f"corpus:{quality_mode}:")
        record.update({
            "status": "ok",
            "title": result.title,
            "description": result.description,
            "template_type": (result.blueprint or {}).get("template_type"),
            "processing_time_ms": result.processing_time_ms,
            "trace_url": result.trace_url,
            "warnings": result.warnings or [],
            "quality_scores": result.quality_scores or {},
            "title_match": entry.matches_title(result.title or ""),
            "default_palette_used": _has_default_palette(result.blueprint or {}),
            "primary_image_url": result.composited_preview_image_url,
        })
    except Exception as exc:  # noqa: BLE001
        logger.exception("Corpus run failed for %s", entry.url)
        record.update({
            "status": "fail",
            "error": str(exc),
            "title_match": False,
        })

    record["elapsed_seconds"] = round(time.time() - started, 2)
    record["finished_at"] = datetime.utcnow().isoformat()

    safe_name = entry.url.replace("https://", "").replace("/", "_")[:120]
    (output_dir / f"{safe_name}.json").write_text(json.dumps(record, indent=2))
    return record


def _has_default_palette(blueprint: Dict[str, Any]) -> bool:
    """Heuristic for "default" palette = the engine's hard-coded blue."""
    primary = (blueprint.get("primary_color") or "").lower()
    return primary in {"#2563eb", "#3b82f6", "#1e40af"}


def aggregate(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not records:
        return {}

    total = len(records)
    successes = [r for r in records if r.get("status") == "ok"]
    fails = [r for r in records if r.get("status") != "ok"]

    title_matches = sum(1 for r in successes if r.get("title_match"))
    default_palette_count = sum(1 for r in successes if r.get("default_palette_used"))

    durations_ms = [r.get("processing_time_ms") for r in successes
                    if isinstance(r.get("processing_time_ms"), (int, float))]
    durations_ms.sort()

    def _percentile(values: List[float], pct: float) -> Optional[float]:
        if not values:
            return None
        k = max(0, min(len(values) - 1, int(round((pct / 100) * (len(values) - 1)))))
        return values[k]

    aggregate_record: Dict[str, Any] = {
        "total": total,
        "successful": len(successes),
        "failed": len(fails),
        "success_rate": round(len(successes) / total, 3),
        "title_fidelity": round(title_matches / max(1, len(successes)), 3),
        "default_palette_incidence": round(default_palette_count / max(1, len(successes)), 3),
        "p50_ms": _percentile(durations_ms, 50),
        "p95_ms": _percentile(durations_ms, 95),
        "fails_by_url": [r.get("url") for r in fails],
    }
    return aggregate_record


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    urls = select_corpus(args)
    if args.dry_run:
        for entry in urls:
            print(f"{entry.category.value}: {entry.url}")
        print(f"total={len(urls)}")
        return 0

    run_dir = make_run_dir(args.output_dir)
    logger.info("Writing artifacts to %s", run_dir)

    records: List[Dict[str, Any]] = []
    if args.workers <= 1:
        for entry in urls:
            records.append(run_single(entry=entry, output_dir=run_dir,
                                       quality_mode=args.quality_mode))
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {
                ex.submit(run_single, entry=entry, output_dir=run_dir,
                          quality_mode=args.quality_mode): entry
                for entry in urls
            }
            for fut in as_completed(futures):
                records.append(fut.result())

    summary = aggregate(records)
    summary_path = run_dir / "SUMMARY.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    logger.info("Run complete: %s", summary)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
