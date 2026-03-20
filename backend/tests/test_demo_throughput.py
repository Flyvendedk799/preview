"""
Regression tests for demo throughput and 400% improvement validation.

Covers:
- Throughput baseline validation logic
- Improvement factor calculation
- Batch job processing_time_ms in response
- Parallel batch job (6.0: test_demo_batch_job_parallel)
"""
import pytest
from unittest.mock import patch, MagicMock


def _load_module():
    from backend.scripts import benchmark_demo_throughput as bm
    return bm


class TestThroughputValidation:
    """Validate throughput baseline and improvement factor logic."""

    def test_compute_improvement_factor_5x(self):
        """5x faster => factor 5.0."""
        bm = _load_module()
        assert bm.compute_improvement_factor(60000, 12000) == pytest.approx(5.0)
        assert bm.compute_improvement_factor(60000, 15000) == pytest.approx(4.0)

    def test_compute_improvement_factor_slower(self):
        """Slower than baseline => factor < 1."""
        bm = _load_module()
        assert bm.compute_improvement_factor(60000, 90000) == pytest.approx(0.667, rel=0.01)

    def test_validate_against_baseline_pass(self):
        """All results under target => pass."""
        bm = _load_module()
        baseline = {"target_ms_per_preview": 15000, "min_success_rate": 0.8, "baseline_ms_per_preview": 60000}
        results = [
            {"url": "https://a.com", "processing_time_ms": 8000},
            {"url": "https://b.com", "processing_time_ms": 12000},
        ]
        ok, msg = bm.validate_against_baseline(results, baseline)
        assert ok is True
        assert "Passed" in msg
        assert "2/2" in msg or "2/" in msg

    def test_validate_against_baseline_fail_low_rate(self):
        """Low success rate => fail."""
        bm = _load_module()
        baseline = {"target_ms_per_preview": 15000, "min_success_rate": 0.8, "baseline_ms_per_preview": 60000}
        results = [
            {"url": "https://a.com", "processing_time_ms": 8000},
            {"url": "https://b.com", "processing_time_ms": 25000},
            {"url": "https://c.com", "processing_time_ms": 30000},
        ]
        ok, msg = bm.validate_against_baseline(results, baseline)
        assert ok is False
        assert "rate" in msg.lower() or "1/3" in msg or "2/3" in msg

    def test_validate_against_baseline_empty(self):
        """Empty results => fail."""
        bm = _load_module()
        baseline = {"target_ms_per_preview": 15000}
        ok, msg = bm.validate_against_baseline([], baseline)
        assert ok is False
        assert "No results" in msg


class TestBatchJobCompletes:
    """Batch job must complete and return aggregated counts."""

    def test_batch_job_returns_completed_count(self):
        """Batch job aggregates completed/failed counts for throughput tracking."""
        from backend.jobs.demo_batch_job import generate_demo_batch_job

        mock_result = MagicMock()
        mock_result.url = "https://example.com"
        mock_result.title = "Test"
        mock_result.composited_preview_image_url = "https://r2.example.com/img.png"
        mock_result.screenshot_url = None

        with patch("backend.jobs.demo_batch_job.PreviewEngine") as MockEngine:
            MockEngine.return_value.generate.return_value = mock_result
            with patch("backend.jobs.demo_batch_job.get_redis_client") as mock_redis:
                mock_redis.return_value.setex = MagicMock()
                mock_redis.return_value.get = MagicMock(return_value=None)
                with patch("backend.jobs.demo_batch_job.is_demo_cache_disabled", return_value=True):
                    out = generate_demo_batch_job("bench-1", ["https://example.com"], quality_mode="fast")

        assert out["completed"] == 1
        assert out["failed"] == 0
        assert out["status"] == "completed"


class TestDemoPreviewJobProcessingTime:
    """Single demo preview job must include processing_time_ms."""

    def test_demo_preview_job_returns_processing_time(self):
        """generate_demo_preview_job response must include processing_time_ms."""
        from backend.jobs.demo_preview_job import generate_demo_preview_job

        mock_result = MagicMock()
        mock_result.url = "https://example.com"
        mock_result.title = "Test"
        mock_result.subtitle = None
        mock_result.description = None
        mock_result.tags = []
        mock_result.context_items = []
        mock_result.credibility_items = []
        mock_result.cta_text = None
        mock_result.primary_image_base64 = None
        mock_result.screenshot_url = None
        mock_result.composited_preview_image_url = None
        mock_result.brand = {}
        mock_result.blueprint = {"template_type": "article", "overall_quality": "good"}
        mock_result.reasoning_confidence = 0.88
        mock_result.processing_time_ms = 9500
        mock_result.quality_scores = {}
        mock_result.message = "OK"
        mock_result.warnings = []
        mock_result.design_dna = None

        with patch("backend.jobs.demo_preview_job.PreviewEngine") as MockEngine:
            MockEngine.return_value.generate.return_value = mock_result
            with patch("backend.jobs.demo_preview_job.get_redis_client", return_value=None):
                with patch("backend.jobs.demo_preview_job.is_demo_cache_disabled", return_value=True):
                    with patch("backend.jobs.demo_preview_job.SessionLocal") as mock_db:
                        mock_db.return_value.close = MagicMock()
                        with patch("backend.jobs.demo_preview_job.get_current_job", return_value=MagicMock(id="test")):
                            with patch("backend.jobs.demo_preview_job.log_activity"):
                                result = generate_demo_preview_job("https://example.com", "fast")

        assert "processing_time_ms" in result
        assert result["processing_time_ms"] == 9500


class TestDemoBatchJobParallel:
    """Parallel batch job: N URLs complete in ~1/N time with N workers."""

    def test_demo_batch_job_parallel(self):
        """
        With mocked engine (sleep 0.2s per URL), 4 URLs in parallel
        complete in ~0.2s total vs ~0.8s sequential.
        """
        import time as time_module

        def slow_generate(url, cache_key_prefix=None):
            time_module.sleep(0.2)  # Simulate ~200ms per URL
            mock_result = MagicMock()
            mock_result.url = url
            mock_result.title = "Test"
            mock_result.composited_preview_image_url = "https://example.com/preview.png"
            mock_result.screenshot_url = "https://example.com/shot.png"
            return mock_result

        urls = [
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/3",
            "https://example.com/4",
        ]

        from backend.jobs.demo_batch_job import generate_demo_batch_job

        with patch("backend.jobs.demo_batch_job.PreviewEngine") as MockEngine:
            MockEngine.return_value.generate.side_effect = slow_generate
            with patch("backend.jobs.demo_batch_job.get_redis_client") as mock_redis:
                mock_redis.return_value.setex = MagicMock()
                mock_redis.return_value.get = MagicMock(return_value=None)
                with patch("backend.jobs.demo_batch_job.is_demo_cache_disabled", return_value=True):
                    t0 = time_module.perf_counter()
                    out = generate_demo_batch_job(
                        "parallel-test", urls, quality_mode="fast"
                    )
                    elapsed = time_module.perf_counter() - t0

        assert out["completed"] == 4
        assert out["failed"] == 0
        assert out["status"] == "completed"
        assert len(out["results"]) == 4
        # Results must preserve URL order
        assert [r["url"] for r in out["results"]] == urls
        # Parallel: 4 URLs at 0.2s each with 4 workers => ~0.2-0.4s total
        # Sequential would be ~0.8s
        assert elapsed < 0.6, f"Expected parallel speedup, got {elapsed:.2f}s (seq would be ~0.8s)"
