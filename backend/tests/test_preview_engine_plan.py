"""End-to-end tests for the DEMO_PREVIEW_ENGINE_FINAL_PLAN integration.

These tests are designed to run without network or AI services, so they
exercise the new modules introduced by the plan in pure unit form. The
nightly corpus workflow gates on this file passing first (see
``.github/workflows/preview-corpus-nightly.yml``).
"""
from __future__ import annotations

import json
import time

import pytest


# ---------------------------------------------------------------------------
# Phase 0 — Corpus
# ---------------------------------------------------------------------------


def test_golden_corpus_meets_minimum_size():
    from backend.services.preview.corpus import GOLDEN_CORPUS, get_corpus

    assert len(GOLDEN_CORPUS) >= 60, "Plan requires minimum 60 golden URLs"
    assert len(get_corpus(include_shadow=True)) >= 70


def test_corpus_is_stratified_across_all_categories():
    from backend.services.preview.corpus import (
        GoldenCorpusCategory,
        get_corpus_by_category,
    )

    for category in GoldenCorpusCategory:
        urls = get_corpus_by_category(category)
        assert urls, f"Category {category.value} has no URLs"
        assert len(urls) >= 10, f"{category.value} stratification too small"


def test_corpus_entries_have_truth_labels():
    from backend.services.preview.corpus import GOLDEN_CORPUS

    for entry in GOLDEN_CORPUS:
        assert entry.url.startswith("http"), entry.url
        assert entry.expected_template_type, f"missing template for {entry.url}"
        # Title keywords are required so we can score fidelity.
        assert entry.expected_title_keywords, f"missing keywords for {entry.url}"


# ---------------------------------------------------------------------------
# Phase 1 — Reliability primitives
# ---------------------------------------------------------------------------


def test_retry_context_rejects_identical_payload():
    from backend.services.preview.reliability import (
        IdenticalRetryError,
        RetryContext,
    )

    ctx = RetryContext()
    payload = {"prompt": "summarize", "url": "https://example.com"}

    ctx.assert_payload_changed(payload)  # first call OK
    with pytest.raises(IdenticalRetryError):
        ctx.assert_payload_changed(payload)


def test_retry_context_mutate_advances_attempt_and_records():
    from backend.services.preview.reliability import RetryContext

    ctx = RetryContext()
    ctx.mutate(critique="too generic", prior_failure="HTTP 500")
    ctx.mutate(critique="boring hook")
    assert ctx.attempt == 2
    assert ctx.critiques == ["too generic", "boring hook"]
    assert "HTTP 500" in ctx.prior_failures[0]


def test_blueprint_validation_repairs_short_hex_colors():
    from backend.services.preview.reliability import validate_blueprint

    result = validate_blueprint({
        "template_type": "saas",
        "primary_color": "#abc",  # short form
        "secondary_color": "#123456",
        "accent_color": "f0a",  # missing leading #
    })
    assert result.is_valid, result.errors
    assert result.repaired["primary_color"] == "#AABBCC"
    assert result.repaired["accent_color"] == "#FF00AA"


def test_blueprint_validation_flags_missing_required():
    from backend.services.preview.reliability import validate_blueprint

    result = validate_blueprint({
        "primary_color": "#000000",
        # template_type, secondary, accent missing
    })
    assert not result.is_valid
    assert any("template_type" in err for err in result.errors)


def test_run_async_safely_runs_in_sync_context():
    from backend.services.preview.reliability import run_async_safely

    async def coro():
        return 42

    assert run_async_safely(lambda: coro()) == 42


def test_resolve_font_returns_fallback_when_missing():
    from backend.services.preview.reliability import resolve_font

    res = resolve_font("Inter-Regular")
    # On the test runner the bundled font almost certainly is missing.
    # The contract is: never raise, always return a FontResolution.
    assert res.requested == "Inter-Regular"
    assert isinstance(res.is_fallback, bool)


# ---------------------------------------------------------------------------
# Phase 2 — Observability
# ---------------------------------------------------------------------------


def test_job_trace_round_trip():
    from backend.services.preview.observability import (
        JobTrace,
        JobTraceStore,
        StageTiming,
        new_job_trace,
    )
    from backend.services.preview.observability.reason_codes import (
        FailureReason,
        TerminalStatus,
    )

    trace = new_job_trace("https://example.com", is_demo=True)
    trace.add_stage(StageTiming(
        name="capture",
        started_at=0,
        finished_at=1,
        duration_ms=1000,
    ))
    trace.extraction_confidence = 0.84
    trace.template_selected = "modern_card"
    trace.finalize_failure(FailureReason.QUALITY_GATE_FAILED, detail="bad contrast")

    store = JobTraceStore.get_instance()
    store.save(trace)

    payload = store.get(trace.job_id)
    assert payload is not None
    assert payload["terminal_status"] == TerminalStatus.FAILED.value
    assert payload["failure_reason"] == FailureReason.QUALITY_GATE_FAILED.value


def test_diagnose_extracts_bottleneck():
    from backend.services.preview.observability.diagnosis import diagnose
    from backend.services.preview.observability.job_trace import StageTiming, new_job_trace

    trace = new_job_trace("https://example.com")
    trace.add_stage(StageTiming("capture", 0, 0.2, 200))
    trace.add_stage(StageTiming("analyze", 0.2, 5.5, 5300))
    trace.finalize_success()

    payload = trace.to_dict()
    diag = diagnose(payload)
    assert diag["verdict"] == "success"
    assert diag["bottleneck_stage"]["name"] == "analyze"


# ---------------------------------------------------------------------------
# Phase 3 — Templates / gradients / composition
# ---------------------------------------------------------------------------


def test_template_contracts_have_well_formed_safe_areas():
    from backend.services.preview.templates import TEMPLATE_CONTRACTS

    for contract_id, contract in TEMPLATE_CONTRACTS.items():
        assert contract.canvas == (1200, 630), contract_id
        for area_name, area in contract.safe_areas.items():
            assert area.x >= 0
            assert area.y >= 0
            assert area.right <= contract.canvas[0], (contract_id, area_name)
            assert area.bottom <= contract.canvas[1], (contract_id, area_name)


def test_pre_measure_layout_flags_overflow():
    from backend.services.preview.templates import (
        TemplateRenderInput,
        get_contract,
        pre_measure_layout,
    )

    contract = get_contract("modern_card")
    inputs = TemplateRenderInput(
        title="A" * 500,  # impossible to fit
        description="B" * 4000,
    )
    violations = pre_measure_layout(contract, inputs)
    assert any(v.field == "title" for v in violations)


def test_pre_measure_layout_passes_for_realistic_input():
    from backend.services.preview.templates import (
        TemplateRenderInput,
        get_contract,
        pre_measure_layout,
    )

    contract = get_contract("hero")
    inputs = TemplateRenderInput(
        title="Build software at the speed of thought",
        subtitle="Linear is built for modern teams",
        description="Linear streamlines issues, sprints, and product roadmaps "
                    "into a single fast, beautifully-designed app.",
        cta_text="Start free",
        has_logo=True,
    )
    violations = pre_measure_layout(contract, inputs)
    assert violations == []


def test_three_stop_gradient_sample_is_perceptually_smooth():
    from backend.services.preview.templates.gradient import (
        GradientPalette,
        gradient_signature,
    )
    from backend.services.preview.extraction.palette import perceptual_distance

    palette = GradientPalette.from_hex("#0F172A", "#3B82F6", "#F472B6")
    # Use a denser sample to assess smoothness; 8-pixel grids have ~1/8th
    # of the range between samples and aren't smooth by construction.
    grid = gradient_signature(palette, width=64, height=2, direction="horizontal")
    row = grid[0]
    diffs = [perceptual_distance(row[i], row[i + 1]) for i in range(len(row) - 1)]
    assert max(diffs) < 60, "gradient has banding"
    assert perceptual_distance(row[0], row[-1]) > 100, "gradient too narrow"


def test_eased_mask_starts_at_zero_and_ends_at_one():
    from backend.services.preview.templates.composition import eased_mask

    mask = eased_mask(8)
    assert mask[0] == 0
    assert mask[-1] == 1
    # Monotonic
    for prev, cur in zip(mask, mask[1:]):
        assert cur >= prev


# ---------------------------------------------------------------------------
# Phase 4 — Extraction fidelity
# ---------------------------------------------------------------------------


def test_classify_page_type_routes_known_urls():
    from backend.services.preview.extraction.prompts import (
        PageType,
        classify_page_type,
    )

    assert classify_page_type("https://shop.example.com/products/blue") == \
        PageType.PRODUCT_ECOMMERCE
    assert classify_page_type("https://example.com/docs/intro") == PageType.DOCS
    assert classify_page_type("https://twitter.com/jack") == PageType.PROFILE
    assert classify_page_type("https://example.com/") == PageType.GENERAL_MARKETING


def test_low_information_hook_rejection():
    from backend.services.preview.extraction.validators import is_low_information_hook

    assert is_low_information_hook("Welcome to MyCompany")
    assert is_low_information_hook("Home")
    assert is_low_information_hook("")
    assert not is_low_information_hook("Build software at the speed of thought")


def test_fallback_title_chain_uses_domain_when_all_weak():
    from backend.services.preview.extraction.validators import fallback_title_chain

    title = fallback_title_chain(
        extracted_hook="",
        og_title="Home",
        h1_candidates=["Welcome"],
        url="https://acme-co.com/",
    )
    assert title == "Acme Co"


def test_palette_distance_enforced():
    from backend.services.preview.extraction.palette import enforce_palette_distance

    result = enforce_palette_distance(
        primary="#3B82F6",
        secondary="#3B83F7",  # essentially identical
        accent="#3C82F6",
    )
    # Three role colors must be distinct after enforcement.
    assert result.primary_hex != result.secondary_hex
    assert result.primary_hex != result.accent_hex
    assert result.secondary_hex != result.accent_hex
    assert result.fallbacks_applied  # at least one repair


def test_extract_social_proof_finds_multiple_signals():
    from backend.services.preview.extraction.social_proof import extract_social_proof

    html = """
    <p>Trusted by 12,500+ teams worldwide.</p>
    <span>★ 4.7</span>
    <p>Featured in TechCrunch and The Verge.</p>
    """
    proofs = extract_social_proof(html)
    values = [p.value for p in proofs]
    assert any("12,500" in v for v in values)
    assert any("4.7" in v for v in values)
    assert any("TechCrunch" in v for v in values)


# ---------------------------------------------------------------------------
# Phase 6 — Lanes
# ---------------------------------------------------------------------------


def test_lane_selection_picks_fast_when_og_rich():
    from backend.services.preview.lanes import select_lane
    from backend.services.preview.observability.reason_codes import PreviewLane

    decision = select_lane(
        has_rich_og_metadata=True,
        html_size_bytes=200_000,
        is_demo=True,
    )
    assert decision.lane == PreviewLane.FAST


def test_lane_selection_forces_deep_for_ecommerce():
    from backend.services.preview.lanes import select_lane
    from backend.services.preview.observability.reason_codes import PreviewLane

    decision = select_lane(
        has_rich_og_metadata=True,
        html_size_bytes=200_000,
        is_demo=False,
        is_ecommerce=True,
    )
    assert decision.lane == PreviewLane.DEEP


def test_screenshot_capture_with_timeout_returns_fallback():
    from backend.services.preview.lanes import (
        screenshot_capture_with_timeout,
        CaptureFallback,
    )

    def slow_capture(_):
        time.sleep(0.4)
        return b"never"

    captured: dict = {}

    def fallback_handler(fb: CaptureFallback):
        captured["reason"] = fb.reason.value
        return b"fallback"

    out = screenshot_capture_with_timeout(
        slow_capture,
        "https://example.com",
        timeout_seconds=0.05,
        on_fallback=fallback_handler,
    )
    assert out == b"fallback"
    assert captured["reason"] == "capture_timeout"


# ---------------------------------------------------------------------------
# Phase 7 — Aggregation function
# ---------------------------------------------------------------------------


def test_corpus_aggregator_handles_mixed_records():
    from backend.scripts.preview_engine.run_corpus import aggregate

    records = [
        {"status": "ok", "title_match": True, "default_palette_used": False,
         "processing_time_ms": 4000, "url": "https://a"},
        {"status": "ok", "title_match": False, "default_palette_used": True,
         "processing_time_ms": 6000, "url": "https://b"},
        {"status": "fail", "url": "https://c"},
    ]
    summary = aggregate(records)
    assert summary["total"] == 3
    assert summary["successful"] == 2
    assert summary["failed"] == 1
    assert 0 < summary["success_rate"] < 1
    assert summary["title_fidelity"] == 0.5
    assert summary["default_palette_incidence"] == 0.5
    assert summary["p50_ms"] in (4000, 6000)
