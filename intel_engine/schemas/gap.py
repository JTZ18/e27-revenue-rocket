"""Knowledge-gap schemas."""
from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class GapStatus(str, Enum):
    open = "open"
    resolved = "resolved"
    superseded = "superseded"


class GapResolution(BaseModel):
    resolved_by: str          # human identifier (Slack user ID, email, etc.)
    resolution_text: str
    resolved_at: datetime
    source_note: str | None = None  # "vendor email", "internal team", etc.


class Gap(BaseModel):
    gap_id: str
    source_event_id: str
    customer_question: str
    missing_info: list[str]
    themes_detected: list[str] = Field(default_factory=list)
    persona_hints: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: GapStatus = GapStatus.open
    resolution: GapResolution | None = None
    drafted_kb_slug: str | None = None
