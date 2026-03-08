"""Tests for cache quality policy and demo cache invalidation coverage."""
from backend.services.preview_engine import PreviewEngine, PreviewEngineConfig, PreviewEngineResult
from backend.services.preview_cache import invalidate_cache


def _make_engine(**config_overrides):
    """Build a PreviewEngine instance without running heavy __init__ logic."""
    engine = PreviewEngine.__new__(PreviewEngine)
    engine.config = PreviewEngineConfig(**config_overrides)
    return engine


def test_cache_policy_rejects_fallback_results():
    engine = _make_engine(enforce_target_quality=True)
    result = PreviewEngineResult(
        url="https://example.com",
        title="Example",
        quality_scores={"is_fallback": True, "overall": 0.95, "design_fidelity": 0.95, "visual": 0.95},
    )

    assert engine._is_cache_eligible_result(result) is False


def test_cache_policy_rejects_below_target_scores_in_strict_mode():
    engine = _make_engine(
        enforce_target_quality=True,
        quality_threshold=0.88,
        min_soft_pass_fidelity=0.72,
        min_soft_pass_visual=0.75,
    )
    result = PreviewEngineResult(
        url="https://example.com",
        title="Example",
        quality_scores={"overall": 0.81, "design_fidelity": 0.71, "visual": 0.70},
    )

    assert engine._is_cache_eligible_result(result) is False


def test_cache_policy_accepts_target_scores_in_strict_mode():
    engine = _make_engine(
        enforce_target_quality=True,
        quality_threshold=0.88,
        min_soft_pass_fidelity=0.72,
        min_soft_pass_visual=0.75,
    )
    result = PreviewEngineResult(
        url="https://example.com",
        title="Example",
        quality_scores={"overall": 0.92, "design_fidelity": 0.80, "visual": 0.84, "gate_status": "pass"},
    )

    assert engine._is_cache_eligible_result(result) is True


def test_invalidate_cache_includes_demo_v3_quality_mode_prefixes(monkeypatch):
    deleted_keys = []

    class DummyRedis:
        def delete(self, *keys):
            deleted_keys.extend(keys)
            return len(keys)

    from backend.services import preview_cache as cache_module
    monkeypatch.setattr(cache_module, "get_redis_client", lambda: DummyRedis())

    ok = invalidate_cache("https://example.com/demo")

    assert ok is True
    assert any(k.startswith("demo:preview:v3:fast:") for k in deleted_keys)
    assert any(k.startswith("demo:preview:v3:balanced:") for k in deleted_keys)
    assert any(k.startswith("demo:preview:v3:ultra:") for k in deleted_keys)
