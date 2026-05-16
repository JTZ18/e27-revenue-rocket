"""Test FastAPI service."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from intel_engine.api import app
from intel_engine.schemas.traversal import Confidence, TraversalResult


@pytest.mark.asyncio
async def test_healthcheck():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        r = await ac.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_traverse_endpoint(fixtures_dir, monkeypatch):
    monkeypatch.setenv("KB_ROOT", str(fixtures_dir / "sample_kb"))

    mock_result = TraversalResult(
        pages_read=["kb/faqs/bpa.md"],
        can_answer_fully=True,
        missing_info=[],
        draft_reply="Yes, all our straps are BPA-free.",
        themes_detected=["materials_safety"],
        persona_hints=["health_conscious"],
        confidence=Confidence.high,
    )

    event_payload = {
        "event_id": "evt_test",
        "source": "google_sheet",
        "customer": {"id": "c1", "name": "Sarah"},
        "body": "BPA-free?",
        "ts": datetime(2026, 5, 16, tzinfo=UTC).isoformat(),
    }

    with patch(
        "intel_engine.api.traverse",
        new=AsyncMock(return_value=mock_result),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            r = await ac.post("/traverse", json=event_payload)

    assert r.status_code == 200
    body = r.json()
    assert body["can_answer_fully"] is True
    assert body["confidence"] == "high"
