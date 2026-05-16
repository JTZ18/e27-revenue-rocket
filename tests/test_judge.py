"""Test LLM-as-judge."""
from unittest.mock import AsyncMock, patch

import pytest

from eval.judge import judge_draft
from eval.schemas import RubricScore


@pytest.mark.asyncio
async def test_judge_returns_validated_score():
    mock = {
        "grounded": 5,
        "brand_voice": 4,
        "completeness": 5,
        "no_hallucination": 5,
        "tone_fit": 4,
        "notes": "Solid.",
    }
    with patch(
        "eval.judge.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ):
        score = await judge_draft(
            ticket_id="TKT-9001",
            customer_message="Are your straps BPA-free?",
            draft_reply="Yes. All Boldr FKM straps are BPA-free.",
            cited_excerpts=["kb/faqs/bpa.md: BPA-free FKM rubber"],
            brand_voice_contract="Open with Yes/No.",
        )

    assert isinstance(score, RubricScore)
    assert score.ticket_id == "TKT-9001"
    assert score.overall == 4.6


@pytest.mark.asyncio
async def test_judge_clamps_out_of_range():
    """Judge sometimes returns 0 or 6; we clamp to 1..5 before validation."""
    mock = {
        "grounded": 0,
        "brand_voice": 6,
        "completeness": 3,
        "no_hallucination": 3,
        "tone_fit": 3,
        "notes": "",
    }
    with patch(
        "eval.judge.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ):
        score = await judge_draft(
            ticket_id="TKT-X",
            customer_message="",
            draft_reply="",
            cited_excerpts=[],
            brand_voice_contract="",
        )
    assert score.grounded == 1
    assert score.brand_voice == 5
