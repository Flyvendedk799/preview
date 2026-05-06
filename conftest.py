"""Repo-root pytest config.

Pin import paths so pytest's autodiscovery does not put ``backend/`` onto
``sys.path``; otherwise the local ``backend/queue`` package shadows the
stdlib ``queue`` module and breaks ``concurrent.futures.ThreadPoolExecutor``.
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))

# Drop any path entry that would expose backend/queue as the global queue.
_to_remove = (
    os.path.join(REPO_ROOT, "backend"),
    os.path.join(REPO_ROOT, "backend") + os.sep,
)
sys.path[:] = [p for p in sys.path if p not in _to_remove]

# Ensure the repo root is importable so ``import backend.services...`` works.
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Force-reimport stdlib queue so any earlier shadowing is undone.
if "queue" in sys.modules and getattr(sys.modules["queue"], "__file__", "") and \
        "backend/queue" in sys.modules["queue"].__file__.replace("\\", "/"):
    del sys.modules["queue"]
import queue  # noqa: E402,F401  — import after path cleanup
