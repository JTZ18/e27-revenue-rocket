"""Test theme clusterer."""
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from intel_engine.agents.theme_clusterer import cluster_themes


@pytest.mark.asyncio
async def test_cluster_themes_returns_report(monkeypatch, tmp_path: Path):
    (tmp_path / "kb" / "_workflows").mkdir(parents=True)
    (tmp_path / "kb" / "_workflows" / "theme-clusterer-agent.md").write_text("PROMPT")
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))
    from intel_engine import settings
    settings.kb_root.cache_clear()

    tickets = [
        {"ticket_id": f"T{i}", "message_body": f"msg {i}"} for i in range(1, 6)
    ]
    mock = {
        "themes": [
            {
                "slug": "bpa_safety",
                "label": "BPA safety",
                "frequency": 3,
                "example_ticket_ids": ["T1", "T2", "T3"],
                "summary": "BPA-free strap questions.",
            },
            {
                "slug": "servicing",
                "label": "Servicing",
                "frequency": 2,
                "example_ticket_ids": ["T4", "T5"],
                "summary": "Servicing-related queries.",
            },
        ]
    }
    with (
        patch(
            "intel_engine.llm.client.llm_config",
            return_value={
                "base_url": "http://test",
                "api_key": "test-key",
                "model": "test-model",
            },
        ),
        patch(
            "intel_engine.agents.theme_clusterer.LLMClient.complete_json",
            new=AsyncMock(return_value=mock),
        ) as mock_complete,
    ):
        report = await cluster_themes(
            tickets=tickets,
            week_start="2026-05-11",
            week_end="2026-05-17",
        )

    assert report.ticket_count == 5
    assert len(report.themes) == 2
    assert report.top_slug() == "bpa_safety"

    # Verify prompt loading and LLM call arguments
    call_kwargs = mock_complete.call_args.kwargs
    assert "PROMPT" in call_kwargs["system"]
    assert "2026-05-11" in call_kwargs["user"]
    assert "2026-05-17" in call_kwargs["user"]
    assert "[T1] msg 1" in call_kwargs["user"]
    assert "[T5] msg 5" in call_kwargs["user"]
