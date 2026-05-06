#!/usr/bin/env python3
"""Developer-facing job diagnosis CLI (Phase 2 exit gate).

Usage:
    python -m backend.scripts.preview_engine.diagnose_job <job_id>
    python -m backend.scripts.preview_engine.diagnose_job --recent 10
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, List


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect preview JobTrace records")
    parser.add_argument("job_id", nargs="?", default=None,
                        help="Job ID to diagnose")
    parser.add_argument("--recent", type=int, default=0,
                        help="Print N most recent jobs and exit")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    from backend.services.preview.observability.diagnosis import diagnose_job
    from backend.services.preview.observability.job_trace import JobTraceStore

    store = JobTraceStore.get_instance()
    if args.recent:
        for entry in store.list_recent(args.recent):
            print(json.dumps({
                "job_id": entry.get("job_id"),
                "url": entry.get("url"),
                "terminal_status": entry.get("terminal_status"),
                "failure_reason": entry.get("failure_reason"),
                "total_ms": entry.get("total_ms"),
            }, indent=2))
        return 0

    if not args.job_id:
        print("Provide a job_id or use --recent N", file=sys.stderr)
        return 2

    diagnosis = diagnose_job(args.job_id)
    if diagnosis is None:
        print(f"job_id={args.job_id} not found in JobTraceStore", file=sys.stderr)
        return 1
    print(json.dumps(diagnosis, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
