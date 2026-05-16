"""Persona schemas."""
from enum import Enum

from pydantic import BaseModel, Field


class PersonaAxis(str, Enum):
    lifecycle = "lifecycle"
    interest = "interest"
    behaviour = "behaviour"


class PersonaStatus(str, Enum):
    active = "active"
    stale = "stale"
    draft = "draft"


class PersonaDefinition(BaseModel):
    axis: PersonaAxis
    slug: str
    label: str
    description: str
    signals: list[str] = Field(min_length=1)
    status: PersonaStatus = PersonaStatus.active


class PersonaProposal(BaseModel):
    """A drift-detector or cold-start agent's proposal for a new persona."""

    axis: PersonaAxis
    slug: str
    label: str
    description: str
    signals: list[str] = Field(min_length=1)
    example_ticket_ids: list[str] = Field(default_factory=list)
    rationale: str


class PersonaDriftReport(BaseModel):
    window_start: str
    window_end: str
    unmatched_tickets: int
    threshold: int = 3
    proposals: list[PersonaProposal] = Field(default_factory=list)
    stale_candidates: list[str] = Field(
        default_factory=list,
        description="Slugs of existing personas that no longer match incoming tickets.",
    )
