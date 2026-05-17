"""Test sentiment comparator agent."""
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from intel_engine.agents.sentiment_comparator import compare_sentiment
from intel_engine.schemas.sentiment import (
    ExternalSentimentReport,
    SentimentVerdict,
)
from intel_engine.schemas.theme import Theme


@pytest.mark.asyncio
async def test_comparator_returns_comparison(monkeypatch, tmp_path: Path):
    (tmp_path / "kb" / "_workflows").mkdir(parents=True)
    (tmp_path / "kb" / "_workflows" / "sentiment-comparator-agent.md").write_text("PROMPT")
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))
    monkeypatch.setenv("LLM_OPENROUTER_BASE_URL", "http://mock")
    monkeypatch.setenv("LLM_OPENROUTER_API_KEY", "k")
    monkeypatch.setenv("LLM_OPENROUTER_MODEL", "m")
    from intel_engine import settings
    settings.kb_root.cache_clear()
    settings.llm_config.cache_clear()

    theme = Theme(
        slug="vegan_straps",
        label="Vegan straps",
        frequency=8,
        example_ticket_ids=["T1", "T2"],
        summary="Customers ask for vegan-certified alternatives.",
    )
    report = ExternalSentimentReport(
        theme_slug="vegan_straps",
        ran_at="2026-05-17T10:00:00+08:00",
        topic="Vegan watch straps",
        external_mentions=42,
        top_sources=["reddit.com/r/vegan", "ig"],
        snippets=["Vegan leather alternatives are trending."],
        raw_emit={},
    )

    mock_out = {
        "verdict": "market_wide",
        "reasoning": "42 external vs 8 internal — broad market signal.",
        "suggested_action": "Add a vegan-strap explainer to the Expedition PDP.",
    }

    with patch(
        "intel_engine.agents.sentiment_comparator.LLMClient.complete_json",
        new=AsyncMock(return_value=mock_out),
    ) as mock_complete:
        cmp = await compare_sentiment(theme=theme, external=report)

    assert cmp.verdict == SentimentVerdict.market_wide
    assert cmp.internal_frequency == 8
    assert cmp.external_mentions == 42
    assert cmp.reasoning == "42 external vs 8 internal — broad market signal."
    assert "Expedition" in cmp.suggested_action

    _, kwargs = mock_complete.call_args
    assert "PROMPT" in kwargs["system"]
    assert "vegan_straps" in kwargs["user"]
    assert "42" in kwargs["user"]


@pytest.mark.asyncio
async def test_comparator_slug_mismatch(monkeypatch, tmp_path: Path):
    (tmp_path / "kb" / "_workflows").mkdir(parents=True)
    (tmp_path / "kb" / "_workflows" / "sentiment-comparator-agent.md").write_text("PROMPT")
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))
    monkeypatch.setenv("LLM_OPENROUTER_BASE_URL", "http://mock")
    monkeypatch.setenv("LLM_OPENROUTER_API_KEY", "k")
    monkeypatch.setenv("LLM_OPENROUTER_MODEL", "m")
    from intel_engine import settings
    settings.kb_root.cache_clear()
    settings.llm_config.cache_clear()

    theme = Theme(
        slug="vegan_straps",
        label="Vegan straps",
        frequency=8,
        example_ticket_ids=["T1"],
        summary="Customers ask for vegan-certified alternatives.",
    )
    report = ExternalSentimentReport(
        theme_slug="mesh_strap",
        ran_at="2026-05-17T10:00:00+08:00",
        topic="Mesh straps",
        external_mentions=5,
        top_sources=["reddit"],
        snippets=["Mesh straps are popular."],
        raw_emit={},
    )

    with pytest.raises(ValueError, match="slug mismatch"):
        await compare_sentiment(theme=theme, external=report)


@pytest.mark.asyncio
async def test_comparator_fallback_defaults(monkeypatch, tmp_path: Path):
    (tmp_path / "kb" / "_workflows").mkdir(parents=True)
    (tmp_path / "kb" / "_workflows" / "sentiment-comparator-agent.md").write_text("PROMPT")
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))
    monkeypatch.setenv("LLM_OPENROUTER_BASE_URL", "http://mock")
    monkeypatch.setenv("LLM_OPENROUTER_API_KEY", "k")
    monkeypatch.setenv("LLM_OPENROUTER_MODEL", "m")
    from intel_engine import settings
    settings.kb_root.cache_clear()
    settings.llm_config.cache_clear()

    theme = Theme(
        slug="vegan_straps",
        label="Vegan straps",
        frequency=8,
        example_ticket_ids=["T1"],
        summary="Customers ask for vegan-certified alternatives.",
    )
    report = ExternalSentimentReport(
        theme_slug="vegan_straps",
        ran_at="2026-05-17T10:00:00+08:00",
        topic="Vegan watch straps",
        external_mentions=42,
        top_sources=["reddit.com/r/vegan", "ig"],
        snippets=["Vegan leather alternatives are trending."],
        raw_emit={},
    )

    with patch(
        "intel_engine.agents.sentiment_comparator.LLMClient.complete_json",
        new=AsyncMock(return_value={}),
    ):
        cmp = await compare_sentiment(theme=theme, external=report)

    assert cmp.verdict == SentimentVerdict.insufficient_data
    assert cmp.reasoning == "No reasoning provided."
    assert cmp.suggested_action == "No action suggested."


@pytest.mark.asyncio
async def test_comparator_invalid_verdict_defaults(monkeypatch, tmp_path: Path):
    (tmp_path / "kb" / "_workflows").mkdir(parents=True)
    (tmp_path / "kb" / "_workflows" / "sentiment-comparator-agent.md").write_text("PROMPT")
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))
    monkeypatch.setenv("LLM_OPENROUTER_BASE_URL", "http://mock")
    monkeypatch.setenv("LLM_OPENROUTER_API_KEY", "k")
    monkeypatch.setenv("LLM_OPENROUTER_MODEL", "m")
    from intel_engine import settings
    settings.kb_root.cache_clear()
    settings.llm_config.cache_clear()

    theme = Theme(
        slug="vegan_straps",
        label="Vegan straps",
        frequency=8,
        example_ticket_ids=["T1"],
        summary="Customers ask for vegan-certified alternatives.",
    )
    report = ExternalSentimentReport(
        theme_slug="vegan_straps",
        ran_at="2026-05-17T10:00:00+08:00",
        topic="Vegan watch straps",
        external_mentions=42,
        top_sources=["reddit.com/r/vegan", "ig"],
        snippets=["Vegan leather alternatives are trending."],
        raw_emit={},
    )

    with patch(
        "intel_engine.agents.sentiment_comparator.LLMClient.complete_json",
        new=AsyncMock(
            return_value={
                "verdict": "nonsense",
                "reasoning": "Some reasoning here.",
                "suggested_action": "Do something.",
            }
        ),
    ):
        cmp = await compare_sentiment(theme=theme, external=report)

    assert cmp.verdict == SentimentVerdict.insufficient_data
    assert cmp.reasoning == "Some reasoning here."
    assert cmp.suggested_action == "Do something."
