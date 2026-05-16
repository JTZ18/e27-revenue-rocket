"""Test cold-start persona discovery agent."""
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from intel_engine.agents.persona_discovery import discover_personas


@pytest.mark.asyncio
async def test_discover_personas_returns_proposals(monkeypatch, tmp_path: Path):
    # Point KB_ROOT at a sample kb with the prompt file present
    kb = tmp_path / "kb" / "_workflows"
    kb.mkdir(parents=True)
    (tmp_path / "kb" / "_workflows" / "persona-discovery-agent.md").write_text("PROMPT")
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))

    from intel_engine import settings
    settings.kb_root.cache_clear()

    tickets = [
        {"ticket_id": "TKT-1", "message_body": "Are straps BPA-free?"},
        {"ticket_id": "TKT-2", "message_body": "Are dyes safe on skin?"},
        {"ticket_id": "TKT-3", "message_body": "Do you service 2019 models?"},
    ]
    mock = {
        "proposals": [
            {
                "axis": "interest",
                "slug": "health_conscious",
                "label": "Health-conscious",
                "description": "Cares about safety.",
                "signals": ["BPA", "dye"],
                "example_ticket_ids": ["TKT-1", "TKT-2"],
                "rationale": "Two skin/safety tickets.",
            },
            {
                "axis": "lifecycle",
                "slug": "owner_aftercare",
                "label": "Owner aftercare",
                "description": "Existing owners servicing watches.",
                "signals": ["service", "repair"],
                "example_ticket_ids": ["TKT-3"],
                "rationale": "Servicing-only ticket.",
            },
        ]
    }
    with patch(
        "intel_engine.agents.persona_discovery.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ):
        proposals = await discover_personas(tickets)

    assert len(proposals) == 2
    assert proposals[0].axis.value == "interest"
    assert proposals[1].slug == "owner_aftercare"
