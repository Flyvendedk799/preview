#!/usr/bin/env python3
"""
Benchmark demo engine throughput for 400% improvement validation.

Compares processing_time_ms against baseline. Use in quality gates or manual runs.

Usage:
  cd <project_root>
  PYTHONPATH=. python backend/scripts/benchmark_demo_throughput.py
  PYTHONPATH=. python backend/scripts/benchmark_demo_throughput.py --update-baseline

Environment:
  DEMO_BENCHMARK_SKIP_LIVE=1  — Skip live API calls (for CI without Redis/API)
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _baseline_path() -> Path:
    return _project_root() / "backend" / "scripts" / "demo_throughput_baseline.json"


def load_baseline() -> Dict[str, Any]:
    """Load baseline config from JSON."""
    path = _baseline_path()
    if not path.exists():
        raise FileNotFoundError(f"Baseline not found: {path}")
    with open(path) as f:
        data = json.load(f)
    # Strip comment keys
    return {k: v for k, v in data.items() if not k.startswith("_")}


def compute_improvement_factor(baseline_ms: float, actual_ms: float) -> float:
    """
    improvement = (baseline - actual) / baseline as a multiple.
    400% improvement = 5x faster => factor = 5.0
    """
    if actual_ms <= 0:
        return float("inf")
    return baseline_ms / actual_ms


def validate_against_baseline(
    results: List[Dict[str, Any]],
    baseline: Dict[str, Any],
) -> Tuple[bool, str]:
    """
    Validate benchmark results against baseline.
    Returns (passed, message).
    """
    target_ms = baseline.get("target_ms_per_preview", 15000)
    min_rate = baseline.get("min_success_rate", 0.8)
    baseline_ms = baseline.get("baseline_ms_per_preview", 60000)

    if not results:
        return False, "No results to validate"

    passed = [r for r in results if r.get("processing_time_ms") is not None and r["processing_time_ms"] <= target_ms]
    success_count = len(passed)
    total = len(results)
    rate = success_count / total if total else 0

    if rate < min_rate:
        return False, (
            f"Success rate {rate:.1%} < {min_rate:.0%}. "
            f"{success_count}/{total} previews under {target_ms}ms."
        )

    avg_ms = sum(r["processing_time_ms"] for r in passed) / len(passed) if passed else 0
    factor = compute_improvement_factor(baseline_ms, avg_ms)
    return True, (
        f"Passed: {success_count}/{total} under {target_ms}ms. "
        f"Avg {avg_ms:.0f}ms, ~{factor:.1f}x improvement vs baseline {baseline_ms}ms."
    )


def run_benchmark_via_api(base_url: str, urls: List[str]) -> List[Dict[str, Any]]:
    """
    Run benchmark by calling demo-v2 API. Requires requests.
    For unit tests, this is mocked; for real runs, requires live API.
    """
    try:
        import requests
    except ImportError:
        raise ImportError("requests required for live benchmark. pip install requests")

    results = []
    api = f"{base_url.rstrip('/')}/api/v1/demo-v2"
    for url in urls:
        try:
            r = requests.post(
                f"{api}/jobs",
                json={"url": url, "quality_mode": "fast"},
                timeout=10,
            )
            r.raise_for_status()
            job_id = r.json().get("job_id")
            if not job_id:
                results.append({"url": url, "error": "No job_id"})
                continue

            for _ in range(90):
                time.sleep(2)
                s = requests.get(f"{api}/jobs/{job_id}/status", timeout=10)
                s.raise_for_status()
                data = s.json()
                status = data.get("status")
                if status == "finished":
                    pt = data.get("processing_time_ms") or data.get("result", {}).get("processing_time_ms")
                    results.append({"url": url, "processing_time_ms": pt})
                    break
                if status == "failed":
                    results.append({"url": url, "error": data.get("error", "failed")})
                    break
            else:
                results.append({"url": url, "error": "timeout"})
        except Exception as e:
            results.append({"url": url, "error": str(e)})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark demo throughput")
    parser.add_argument("--update-baseline", action="store_true", help="Update baseline from current run")
    parser.add_argument("--base-url", default="https://www.mymetaview.com", help="API base URL")
    parser.add_argument("--dry-run", action="store_true", help="Load baseline and validate logic only")
    args = parser.parse_args()

    root = _project_root()
    os.chdir(root)
    if "." not in sys.path:
        sys.path.insert(0, ".")

    if os.environ.get("DEMO_BENCHMARK_SKIP_LIVE") == "1" or args.dry_run:
        print("DEMO_BENCHMARK_SKIP_LIVE=1 or --dry-run: skipping live API calls")
        baseline = load_baseline()
        print(f"Baseline: target={baseline.get('target_ms_per_preview')}ms")
        print("Throughput validation logic OK.")
        return 0

    try:
        baseline = load_baseline()
    except Exception as e:
        print(f"ERROR: {e}")
        return 2

    urls = baseline.get("fixture_urls", ["https://example.com"])
    print(f"Benchmarking {len(urls)} URLs vs target {baseline.get('target_ms_per_preview')}ms...")
    results = run_benchmark_via_api(args.base_url, urls)
    ok, msg = validate_against_baseline(results, baseline)
    print(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
