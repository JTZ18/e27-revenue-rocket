"""Test schemas validate correctly."""
from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from intel_engine.schemas.event import Channel, CommonEvent, Customer
from intel_engine.schemas.gap import Gap, GapStatus
from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter, KBStatus
from intel_engine.schemas.traversal import Confidence, TraversalResult


def test_common_event_minimal_fields():
    event = CommonEvent(
        event_id="evt_123",
        source=Channel.google_sheet,
        customer=Customer(id="anon_c042", name="Sarah K."),
        body="Are your watches MRI-safe?",
        ts=datetime(2026, 5, 16, 14, 23, 11, tzinfo=UTC),
    )
    assert event.subject is None
    assert event.attachments == []
    assert event.channel_meta == {}


def test_common_event_rejects_empty_body():
    with pytest.raises(ValidationError):
        CommonEvent(
            event_id="evt_123",
            source=Channel.gmail,
            customer=Customer(id="anon_c042", name="Sarah K."),
            body="",
            ts=datetime.now(UTC),
        )


def test_common_event_channels_enum():
    assert Channel.google_sheet.value == "google_sheet"
    assert Channel.gmail.value == "gmail"
    assert Channel.instagram_dm.value == "instagram_dm"
    assert Channel.whatsapp.value == "whatsapp"


def test_kb_frontmatter_required_fields():
    fm = KBFrontmatter(
        slug="bpa-free-straps",
        title="Are Boldr FKM rubber straps BPA-free?",
        domain=KBDomain.spec,
        themes=["materials_safety", "sustainability"],
        sources=["faq_v3"],
        last_verified=date(2026, 5, 16),
    )
    assert fm.status == KBStatus.active
    assert fm.supersedes == []


def test_kb_entry_serialises_to_markdown():
    entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="bpa-free-straps",
            title="Are Boldr FKM rubber straps BPA-free?",
            domain=KBDomain.spec,
            themes=["materials_safety"],
            sources=["faq_v3"],
            last_verified=date(2026, 5, 16),
        ),
        body="Yes. All Boldr FKM rubber and silicone straps are 100% BPA-free.",
    )
    md = entry.to_markdown()
    assert md.startswith("---\n")
    assert "slug: bpa-free-straps" in md
    assert "Yes. All Boldr FKM rubber" in md


def test_traversal_result_can_answer():
    result = TraversalResult(
        pages_read=["kb/faqs/bpa-straps.md"],
        can_answer_fully=True,
        missing_info=[],
        draft_reply="Hi Sarah, thanks for reaching out...",
        themes_detected=["materials_safety"],
        persona_hints=["health_conscious"],
        confidence=Confidence.high,
    )
    assert result.can_answer_fully is True


def test_traversal_result_cannot_answer_requires_missing_info():
    result = TraversalResult(
        pages_read=["kb/faqs/bpa-straps.md"],
        can_answer_fully=False,
        missing_info=["MRI compatibility unknown"],
        draft_reply=None,
        themes_detected=["materials_safety"],
        persona_hints=[],
        confidence=Confidence.low,
    )
    assert result.can_answer_fully is False
    assert result.draft_reply is None


def test_kb_entry_round_trip():
    entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="bpa-free-straps",
            title="Are Boldr FKM rubber straps BPA-free?",
            domain=KBDomain.spec,
            themes=["materials_safety"],
            sources=["faq_v3"],
            last_verified=date(2026, 5, 16),
        ),
        body="Yes. All Boldr FKM rubber and silicone straps are 100% BPA-free.",
    )
    md = entry.to_markdown()
    restored = KBEntry.from_markdown(md)
    assert restored == entry


def test_traversal_result_validator_can_answer_fully_requires_draft_reply():
    with pytest.raises(ValidationError):
        TraversalResult(
            pages_read=["kb/faqs/bpa-straps.md"],
            can_answer_fully=True,
            missing_info=[],
            draft_reply=None,
            themes_detected=["materials_safety"],
            persona_hints=[],
            confidence=Confidence.high,
        )


def test_traversal_result_validator_cannot_answer_fully_rejects_draft_reply():
    with pytest.raises(ValidationError):
        TraversalResult(
            pages_read=["kb/faqs/bpa-straps.md"],
            can_answer_fully=False,
            missing_info=["MRI compatibility unknown"],
            draft_reply="some text",
            themes_detected=["materials_safety"],
            persona_hints=[],
            confidence=Confidence.low,
        )


def test_gap_default_status_is_open():
    gap = Gap(
        gap_id="gap_2026-05-16_abc",
        source_event_id="evt_123",
        customer_question="Are Boldr watches MRI-safe?",
        missing_info=["MRI compatibility unknown"],
        themes_detected=["materials_safety"],
    )
    assert gap.status == GapStatus.open
    assert gap.resolution is None
