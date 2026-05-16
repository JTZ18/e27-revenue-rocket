"""Test schemas validate correctly."""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from intel_engine.schemas.event import Channel, CommonEvent, Customer


def test_common_event_minimal_fields():
    event = CommonEvent(
        event_id="evt_123",
        source=Channel.google_sheet,
        customer=Customer(id="anon_c042", name="Sarah K."),
        body="Are your watches MRI-safe?",
        ts=datetime(2026, 5, 16, 14, 23, 11, tzinfo=timezone.utc),
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
            ts=datetime.now(timezone.utc),
        )


def test_common_event_channels_enum():
    assert Channel.google_sheet.value == "google_sheet"
    assert Channel.gmail.value == "gmail"
    assert Channel.instagram_dm.value == "instagram_dm"
    assert Channel.whatsapp.value == "whatsapp"
