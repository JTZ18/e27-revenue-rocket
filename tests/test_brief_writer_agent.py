"""Test brief writer."""
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from intel_engine.agents.brief_writer import write_brief
from intel_engine.schemas.brief import BriefTarget
from intel_engine.schemas.persona import PersonaAxis, PersonaDefinition
from intel_engine.schemas.theme import Theme, ThemeReport


@pytest.mark.asyncio
async def test_write_brief_returns_marketing_brief(monkeypatch, tmp_path: Path):
    (tmp_path / "kb" / "_workflows").mkdir(parents=True)
    (tmp_path / "kb" / "_workflows" / "brief-writer-agent.md").write_text("PROMPT")
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))
    from intel_engine import settings
    settings.kb_root.cache_clear()

    weekly = [
        ThemeReport(
            week_start="2026-05-01",
            week_end="2026-05-07",
            ticket_count=10,
            themes=[
                Theme(
                    slug="sustainability",
                    label="Sustainability",
                    frequency=4,
                    example_ticket_ids=["T1", "T2"],
                    summary="Vegan + carbon-neutral.",
                )
            ],
        )
    ]
    personas = [
        PersonaDefinition(
            axis=PersonaAxis.interest,
            slug="sustainability_buyer",
            label="Sustainability buyer",
            description="d",
            signals=["vegan"],
        )
    ]
    mock = {
        "headline": "May: sustainability dominates.",
        "insights": [
            {
                "theme": "sustainability",
                "ticket_count": 4,
                "persona_segments": ["sustainability_buyer"],
                "observation": "Cluster on vegan straps.",
            }
        ],
        "recommendations": [
            {
                "target": "product_page",
                "action": "Add vegan-strap explainer to Expedition PDP.",
                "expected_impact": "Reduce CS load by 15%.",
                "evidence_themes": ["sustainability"],
            }
        ],
    }
    with patch(
        "intel_engine.agents.brief_writer.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ) as mock_complete:
        brief = await write_brief(
            month="2026-05",
            theme_reports=weekly,
            personas=personas,
            kb_summary="(50 entries)",
        )

    assert brief.month == "2026-05"
    assert "sustainability" in brief.headline.lower()
    assert brief.recommendations[0].target == BriefTarget.product_page

    _, kwargs = mock_complete.call_args
    assert "PROMPT" in kwargs["system"]
    assert "2026-05" in kwargs["user"]
    assert "Sustainability" in kwargs["user"]
    assert "sustainability_buyer" in kwargs["user"]
