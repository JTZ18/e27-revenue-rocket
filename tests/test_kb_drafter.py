"""Test KB drafter agent."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from intel_engine.agents.kb_drafter import draft_kb_entry
from intel_engine.schemas.gap import Gap, GapResolution, GapStatus
from intel_engine.schemas.kb import KBDomain, KBEntry


@pytest.fixture
def sample_gap() -> Gap:
    return Gap(
        gap_id="gap_2026-05-16_mri",
        source_event_id="evt_xyz",
        customer_question="Are Boldr watches MRI-safe?",
        missing_info=["MRI compatibility not in KB"],
        themes_detected=["materials_safety"],
        status=GapStatus.resolved,
        resolution=GapResolution(
            resolved_by="sarah@boldr.sg",
            resolution_text=(
                "Boldr Grade 5 titanium watches are MRI-safe. "
                "Titanium is non-magnetic. Customers should remove leather "
                "and FKM rubber straps with metal clasps before MRI."
            ),
            resolved_at=datetime(2026, 5, 16, tzinfo=UTC),
            source_note="confirmed with manufacturer",
        ),
    )


@pytest.fixture
def sample_kb_root(monkeypatch, fixtures_dir):
    from intel_engine.settings import kb_root
    kb_root.cache_clear()
    monkeypatch.setenv("KB_ROOT", str(fixtures_dir / "sample_kb"))


@pytest.mark.asyncio
async def test_draft_kb_entry_returns_valid_entry(sample_gap, sample_kb_root):
    mock_response = {
        "frontmatter": {
            "slug": "are-boldr-watches-mri-safe",
            "title": "Are Boldr watches MRI-safe?",
            "domain": "spec",
            "themes": ["materials_safety"],
            "sources": ["gap_2026-05-16_mri"],
            "last_verified": "2026-05-16",
            "supersedes": [],
        },
        "body": (
            "Yes. Boldr Grade 5 titanium watches are MRI-safe. "
            "Titanium is non-magnetic. We recommend removing leather or FKM straps "
            "with metal clasps before an MRI procedure."
        ),
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
            "intel_engine.agents.kb_drafter.LLMClient.complete_json",
            new=AsyncMock(return_value=mock_response),
        ),
    ):
        entry = await draft_kb_entry(sample_gap)

    assert isinstance(entry, KBEntry)
    assert entry.frontmatter.slug == "are-boldr-watches-mri-safe"
    assert entry.frontmatter.domain == KBDomain.spec
    assert "titanium" in entry.body.lower()


@pytest.mark.asyncio
async def test_draft_kb_entry_raises_if_no_resolution(sample_kb_root):
    from intel_engine.schemas.gap import Gap
    gap = Gap(
        gap_id="gap_test",
        source_event_id="evt_test",
        customer_question="Q?",
        missing_info=["unknown"],
    )
    with pytest.raises(ValueError, match="resolution"):
        await draft_kb_entry(gap)
