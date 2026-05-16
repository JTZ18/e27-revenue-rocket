"""Test conflict detector."""
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from intel_engine.agents.conflict_detector import detect_conflicts


@pytest.mark.asyncio
async def test_detect_conflicts_returns_digest(monkeypatch, tmp_path: Path):
    (tmp_path / "kb" / "_workflows").mkdir(parents=True)
    (tmp_path / "kb" / "_workflows" / "conflict-detector-agent.md").write_text("PROMPT")
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))
    from intel_engine import settings
    settings.kb_root.cache_clear()

    kb_summary = [
        {"path": "kb/faqs/engraving-old.md", "domain": "faq", "title": "Engraving",
         "excerpt": "SGD 40"},
        {"path": "kb/rate-cards/engraving.md", "domain": "pricing", "title": "Engraving",
         "excerpt": "SGD 30"},
    ]
    mock = {
        "conflicts": [
            {
                "domain": "pricing",
                "fact_topic": "engraving service price",
                "entries": ["kb/faqs/engraving-old.md", "kb/rate-cards/engraving.md"],
                "canonical_proposal": "kb/rate-cards/engraving.md",
                "reasoning": "Rate card is canonical for prices per kb/_schema.md.",
            }
        ]
    }
    with patch(
        "intel_engine.agents.conflict_detector.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ) as mock_complete:
        digest = await detect_conflicts(
            kb_entries=kb_summary,
            week_end="2026-05-17",
        )

    assert digest.count == 1
    assert digest.conflicts[0].canonical_proposal.endswith("rate-cards/engraving.md")

    _, kwargs = mock_complete.call_args
    assert "PROMPT" in kwargs["system"]
    assert "2026-05-17" in kwargs["user"]
    assert "kb/faqs/engraving-old.md" in kwargs["user"]
