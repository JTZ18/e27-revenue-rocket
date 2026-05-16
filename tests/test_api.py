"""Test FastAPI service."""
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from intel_engine.api import app
from intel_engine.schemas.gap import Gap, GapResolution, GapStatus
from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter
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


@pytest.mark.asyncio
async def test_create_gap_endpoint(monkeypatch, tmp_path):
    monkeypatch.setenv("GAP_LOG_ROOT", str(tmp_path))

    payload = {
        "source_event_id": "evt_xyz",
        "customer_question": "Are Boldr watches MRI-safe?",
        "missing_info": ["MRI compatibility unknown"],
        "themes_detected": ["materials_safety"],
        "persona_hints": [],
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        r = await ac.post("/gap", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "open"
    assert body["gap_id"].startswith("gap_")


@pytest.mark.asyncio
async def test_draft_kb_entry_endpoint(monkeypatch, tmp_path, fixtures_dir):
    monkeypatch.setenv("GAP_LOG_ROOT", str(tmp_path))
    monkeypatch.setenv("KB_ROOT", str(fixtures_dir / "sample_kb"))

    # Pre-write a resolved gap
    from intel_engine.gap.logger import write_gap

    gap = Gap(
        gap_id="gap_resolve",
        source_event_id="evt_a",
        customer_question="Are Boldr watches MRI-safe?",
        missing_info=["MRI"],
        themes_detected=["materials_safety"],
        status=GapStatus.resolved,
        resolution=GapResolution(
            resolved_by="sarah@b.com",
            resolution_text="Titanium is non-magnetic; watches are MRI-safe.",
            resolved_at=datetime(2026, 5, 16, tzinfo=UTC),
        ),
    )
    write_gap(gap)

    mock_entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="mri-safe",
            title="MRI-safe?",
            domain=KBDomain.spec,
            themes=["materials_safety"],
            sources=["gap_resolve"],
            last_verified=date(2026, 5, 16),
        ),
        body="Yes. Titanium is non-magnetic.",
    )
    with patch(
        "intel_engine.api.draft_kb_entry",
        new=AsyncMock(return_value=mock_entry),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            r = await ac.post("/draft-kb-entry", json={"gap_id": "gap_resolve"})

    assert r.status_code == 200
    body = r.json()
    assert body["frontmatter"]["slug"] == "mri-safe"
    assert body["frontmatter"]["domain"] == "spec"


@pytest.mark.asyncio
async def test_stage_and_load_draft(monkeypatch, tmp_path):
    # Cheat: monkeypatch the global path
    import intel_engine.api as api_mod
    monkeypatch.setattr(api_mod, "DRAFT_STAGE_DIR", tmp_path)

    entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="t", title="T", domain=KBDomain.faq, themes=[], sources=[],
            last_verified=date(2026, 5, 16),
        ),
        body="b",
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        r = await ac.post(
            "/draft/stage",
            json={"gap_id": "g1", "entry": entry.model_dump(mode="json")},
        )
        assert r.status_code == 200
        r2 = await ac.get("/draft/staged/g1")
        assert r2.status_code == 200
        assert r2.json()["frontmatter"]["slug"] == "t"
