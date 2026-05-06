"""Phase 3.1 — Template contract tests.

These exist as a separate file so the nightly CI can gate on them
specifically (the plan exit gate is "clipping/overlap < 2% on corpus").
"""
from __future__ import annotations

import pytest

from backend.services.preview.templates import (
    HERO_CONTRACT_V1,
    MODERN_CARD_CONTRACT_V1,
    PROFILE_CONTRACT_V1,
    TEMPLATE_CONTRACTS,
    TemplateRenderInput,
    pre_measure_layout,
)


@pytest.mark.parametrize(
    "contract,inputs",
    [
        (
            HERO_CONTRACT_V1,
            TemplateRenderInput(
                title="Build software at the speed of thought",
                subtitle="Linear is built for modern teams",
                description=(
                    "Linear streamlines issues, sprints, and product roadmaps "
                    "into a single fast, beautifully-designed app."
                ),
                cta_text="Start free",
                has_logo=True,
            ),
        ),
        (
            MODERN_CARD_CONTRACT_V1,
            TemplateRenderInput(
                title="Notes that turn into outcomes",
                subtitle=None,
                description=(
                    "Capture ideas, sync with your team, and ship faster "
                    "with the workspace that scales."
                ),
                cta_text="Get started",
                has_logo=True,
            ),
        ),
        (
            PROFILE_CONTRACT_V1,
            TemplateRenderInput(
                title="Dan Abramov",
                subtitle="React core, Vercel",
                description=(
                    "Lead engineer behind Redux and React Server Components. "
                    "Writes about UI architecture and developer experience."
                ),
                tags=["React", "Redux", "DX", "JavaScript"],
                has_logo=False,
            ),
        ),
    ],
)
def test_realistic_inputs_fit_safely(contract, inputs):
    violations = pre_measure_layout(contract, inputs)
    assert violations == [], (
        f"{contract.id}: unexpected violations {[v.detail for v in violations]}"
    )


def test_overflowing_input_is_caught_for_all_contracts():
    inputs = TemplateRenderInput(
        title="Very" * 200,
        description="Word " * 4000,
    )
    for contract in [HERO_CONTRACT_V1, MODERN_CARD_CONTRACT_V1, PROFILE_CONTRACT_V1]:
        violations = pre_measure_layout(contract, inputs)
        assert violations, f"{contract.id} did not catch overflow"


def test_contract_id_resolution():
    assert TEMPLATE_CONTRACTS["hero@v1"].name == "hero"
    assert TEMPLATE_CONTRACTS["hero"].version == "v1"
