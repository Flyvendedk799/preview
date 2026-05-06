"""Phase 0 — Golden URL corpus and baseline metrics."""
from backend.services.preview.corpus.golden_corpus import (
    GoldenURL,
    GoldenCorpusCategory,
    GOLDEN_CORPUS,
    SHADOW_CORPUS,
    get_corpus,
    get_corpus_by_category,
)

__all__ = [
    "GoldenURL",
    "GoldenCorpusCategory",
    "GOLDEN_CORPUS",
    "SHADOW_CORPUS",
    "get_corpus",
    "get_corpus_by_category",
]
