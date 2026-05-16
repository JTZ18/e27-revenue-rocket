"""Test persona drift detector."""
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from intel_engine.agents.persona_drift import detect_drift
from intel_engine.schemas.persona import PersonaAxis, PersonaDefinition


@pytest.mark.asyncio
async def test_detect_drift_returns_report(monkeypatch, tmp_path: Path):
    (tmp_path / "kb" / "_workflows").mkdir(parents=True)
    (tmp_path / "kb" / "_workflows" / "persona-drift-agent.md").write_text("PROMPT")
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))

    from intel_engine import settings
    settings.kb_root.cache_clear()

    active = [
        PersonaDefinition(
            axis=PersonaAxis.interest,
            slug="health_conscious",
            label="Health-conscious",
            description="d",
            signals=["BPA", "dye"],
        )
    ]
    tickets = [
        {"ticket_id": "T1", "message_body": "Carbon-neutral shipping?", "received_at": "2026-05-01"},
        {"ticket_id": "T2", "message_body": "Is the strap vegan?", "received_at": "2026-05-03"},
        {"ticket_id": "T3", "message_body": "What's your sustainability policy?", "received_at": "2026-05-05"},
    ]

    mock = {
        "unmatched_tickets": 3,
        "stale_candidates": [],
        "proposals": [
            {
                "axis": "interest",
                "slug": "sustainability_buyer",
                "label": "Sustainability buyer",
                "description": "Cares about carbon-neutral + vegan.",
                "signals": ["carbon-neutral", "vegan", "sustainability"],
                "example_ticket_ids": ["T1", "T2", "T3"],
                "rationale": "3 unmatched tickets cluster on sustainability.",
            }
        ],
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
            "intel_engine.agents.persona_drift.LLMClient.complete_json",
            new=AsyncMock(return_value=mock),
        ),
    ):
        report = await detect_drift(
            active_personas=active,
            tickets=tickets,
            window_start="2026-04-01",
            window_end="2026-05-12",
        )

    assert report.unmatched_tickets == 3
    assert report.threshold == 3
    assert len(report.proposals) == 1
    assert report.proposals[0].slug == "sustainability_buyer"
