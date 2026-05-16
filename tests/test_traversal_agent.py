"""Test wiki-traversal agent."""
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from intel_engine.agents.traversal import traverse
from intel_engine.schemas.event import Channel, CommonEvent, Customer
from intel_engine.schemas.traversal import Confidence, TraversalResult


@pytest.fixture
def sample_event() -> CommonEvent:
    return CommonEvent(
        event_id="evt_test",
        source=Channel.google_sheet,
        customer=Customer(id="anon_x", name="Sarah"),
        body="Are your straps BPA-free?",
        ts=datetime(2026, 5, 16, tzinfo=UTC),
    )


@pytest.fixture
def sample_kb_root(monkeypatch, fixtures_dir) -> Path:
    monkeypatch.setenv("KB_ROOT", str(fixtures_dir / "sample_kb"))
    return fixtures_dir / "sample_kb"


@pytest.mark.asyncio
async def test_traverse_returns_validated_result(sample_event, sample_kb_root):
    mock_response = {
        "pages_read": ["kb/faqs/bpa.md"],
        "can_answer_fully": True,
        "missing_info": [],
        "draft_reply": (
            "Hi Sarah, thanks for reaching out — Yes, all Boldr FKM straps are 100% BPA-free."
        ),
        "themes_detected": ["materials_safety"],
        "persona_hints": ["health_conscious"],
        "confidence": "high",
    }
    mock_client_cls = patch(
        "intel_engine.agents.traversal.LLMClient",
    ).start()
    mock_instance = mock_client_cls.return_value
    mock_instance.complete_json = AsyncMock(return_value=mock_response)

    result = await traverse(sample_event)

    patch.stopall()
    assert isinstance(result, TraversalResult)
    assert result.can_answer_fully is True
    assert result.draft_reply is not None
    assert "BPA-free" in result.draft_reply
    assert result.confidence == Confidence.high


@pytest.mark.asyncio
async def test_traverse_handles_gap(sample_event, sample_kb_root):
    mock_response = {
        "pages_read": ["kb/faqs/bpa.md"],
        "can_answer_fully": False,
        "missing_info": ["MRI safety not in KB"],
        "draft_reply": None,
        "themes_detected": ["materials_safety"],
        "persona_hints": [],
        "confidence": "low",
    }
    mock_client_cls = patch(
        "intel_engine.agents.traversal.LLMClient",
    ).start()
    mock_instance = mock_client_cls.return_value
    mock_instance.complete_json = AsyncMock(return_value=mock_response)

    result = await traverse(sample_event)

    patch.stopall()
    assert result.can_answer_fully is False
    assert result.draft_reply is None
    assert "MRI" in result.missing_info[0]
