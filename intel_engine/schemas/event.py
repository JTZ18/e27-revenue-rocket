"""Common Event Schema — all channel adapters normalise into this."""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Channel(str, Enum):
    google_sheet = "google_sheet"
    gmail = "gmail"
    instagram_dm = "instagram_dm"
    whatsapp = "whatsapp"


class Customer(BaseModel):
    id: str
    name: str


class CommonEvent(BaseModel):
    """Normalised inbound customer event from any channel."""

    event_id: str
    source: Channel
    channel_meta: dict[str, Any] = Field(default_factory=dict)
    customer: Customer
    subject: str | None = None
    body: str = Field(min_length=1)
    ts: datetime
    attachments: list[str] = Field(default_factory=list)
