"""Test sentiment planner agent."""
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from intel_engine.agents.sentiment_planner import plan_query_for_theme
from intel_engine.schemas.theme import Theme


@pytest.mark.asyncio
async def test_planner_returns_query_plan(monkeypatch, tmp_path: Path):
    (tmp_path / "kb" / "_workflows").mkdir(parents=True)
    (tmp_path / "kb" / "_workflows" / "sentiment-planner-agent.md").write_text("PROMPT")
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))
    monkeypatch.setenv("LLM_MINIMAX_BASE_URL", "http://mock")
    monkeypatch.setenv("LLM_MINIMAX_API_KEY", "k")
    monkeypatch.setenv("LLM_MINIMAX_MODEL", "m")
    from intel_engine import settings

    settings.kb_root.cache_clear()
    settings.llm_config.cache_clear()

    theme = Theme(
        slug="bpa_free",
        label="BPA-free straps",
        frequency=4,
        example_ticket_ids=["T1", "T2"],
        summary="Customers ask whether FKM/silicone straps are BPA-free.",
    )

    mock_out = {
        "topic": "BPA-free titanium watch straps",
        "search_terms": ["BPA-free silicone", "FKM rubber safe", "BPA strap"],
        "subreddits": ["watches", "AskScience"],
        "related_handles": [],
        "notes": "Reddit + science subs are where material safety debates happen.",
    }

    with patch(
        "intel_engine.agents.sentiment_planner.LLMClient.complete_json",
        new=AsyncMock(return_value=mock_out),
    ) as mock_complete:
        plan = await plan_query_for_theme(theme=theme, kb_excerpt="BPA-free FAQ excerpt.")

    assert plan.topic == "BPA-free titanium watch straps"
    assert "BPA-free silicone" in plan.search_terms
    assert "watches" in plan.subreddits

    _, kwargs = mock_complete.call_args
    assert "PROMPT" in kwargs["system"]
    assert "BPA-free straps" in kwargs["user"]
    assert "T1" in kwargs["user"]
