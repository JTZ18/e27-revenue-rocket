"""Test cold-start persona discovery agent."""
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from intel_engine.agents.persona_discovery import _format_tickets, discover_personas


@pytest.fixture
def setup_kb(monkeypatch, tmp_path: Path):
    """Point KB_ROOT at a sample kb with the prompt file present."""
    kb = tmp_path / "kb" / "_workflows"
    kb.mkdir(parents=True)
    (tmp_path / "kb" / "_workflows" / "persona-discovery-agent.md").write_text("PROMPT")
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))

    from intel_engine import settings
    settings.kb_root.cache_clear()
    return tmp_path


@pytest.fixture
def tickets():
    return [
        {"ticket_id": "TKT-1", "message_body": "Are straps BPA-free?"},
        {"ticket_id": "TKT-2", "message_body": "Are dyes safe on skin?"},
        {"ticket_id": "TKT-3", "message_body": "Do you service 2019 models?"},
    ]


@pytest.mark.asyncio
async def test_discover_personas_returns_proposals(setup_kb, tickets):
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
                "example_ticket_ids": ["TKT-2", "TKT-3"],
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


@pytest.mark.asyncio
async def test_discover_personas_prompt_and_tickets_passed_to_llm(setup_kb, tickets):
    """Verify correct prompt name and formatted tickets are sent to LLMClient."""
    mock_complete = AsyncMock(return_value={"proposals": []})
    with patch(
        "intel_engine.agents.persona_discovery.LLMClient.complete_json",
        new=mock_complete,
    ):
        await discover_personas(tickets)

    assert mock_complete.called
    call_kwargs = mock_complete.call_args.kwargs
    assert call_kwargs["system"] == "PROMPT"

    user_msg = call_kwargs["user"]
    assert "=== TICKET DUMP (3 tickets) ===" in user_msg
    assert "[TKT-1] Are straps BPA-free?" in user_msg
    assert "[TKT-2] Are dyes safe on skin?" in user_msg
    assert "[TKT-3] Do you service 2019 models?" in user_msg
    assert "Propose persona taxonomy now." in user_msg


@pytest.mark.asyncio
async def test_discover_personas_empty_proposals_returns_empty_list(setup_kb, tickets):
    """Missing or empty proposals key returns empty list gracefully."""
    with patch(
        "intel_engine.agents.persona_discovery.LLMClient.complete_json",
        new=AsyncMock(return_value={}),
    ):
        proposals = await discover_personas(tickets)
    assert proposals == []

    with patch(
        "intel_engine.agents.persona_discovery.LLMClient.complete_json",
        new=AsyncMock(return_value={"proposals": []}),
    ):
        proposals = await discover_personas(tickets)
    assert proposals == []


@pytest.mark.asyncio
async def test_discover_personas_malformed_proposal_raises_validation_error(
    setup_kb, tickets
):
    """Malformed LLM output (e.g. missing required fields) raises ValidationError."""
    mock = {
        "proposals": [
            {
                "axis": "interest",
                "slug": "bad_proposal",
                # missing label, description, signals, example_ticket_ids, rationale
            }
        ]
    }
    with patch(
        "intel_engine.agents.persona_discovery.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ), pytest.raises(ValidationError):
        await discover_personas(tickets)


@pytest.mark.asyncio
async def test_discover_personas_too_few_example_ticket_ids_raises_validation_error(
    setup_kb, tickets
):
    """Proposal with fewer than 2 example_ticket_ids violates schema and raises."""
    mock = {
        "proposals": [
            {
                "axis": "interest",
                "slug": "health_conscious",
                "label": "Health-conscious",
                "description": "Cares about safety.",
                "signals": ["BPA"],
                "example_ticket_ids": ["TKT-1"],
                "rationale": "Only one ticket.",
            }
        ]
    }
    with patch(
        "intel_engine.agents.persona_discovery.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ), pytest.raises(ValidationError):
        await discover_personas(tickets)


def test_format_tickets_truncates_and_joins():
    """_format_tickets produces expected string with truncation and newline joining."""
    tickets = [
        {"ticket_id": "A", "message_body": "Hello\nworld"},
        {"ticket_id": "B", "message_body": "x" * 300},
    ]
    result = _format_tickets(tickets)
    assert result == "[A] Hello world\n[B] " + "x" * 280
