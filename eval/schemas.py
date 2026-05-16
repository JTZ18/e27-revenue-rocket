"""Schemas for the evaluation harness."""
from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class EvalLabel(BaseModel):
    """Held-out ground-truth label for one ticket."""

    ticket_id: str
    question_type: str
    buyer_persona: str
    answered_by_kb: bool
    requires_escalation: bool


class ReplayStep(BaseModel):
    """One row of the replay harness output — per-ticket provenance."""

    ticket_id: str
    ticket_index: int
    received_at: datetime
    pages_read: list[str] = Field(default_factory=list)
    can_answer_fully: bool
    themes_detected: list[str] = Field(default_factory=list)
    persona_hints: list[str] = Field(default_factory=list)
    confidence: str
    draft_reply: str | None = None
    gap_created: bool
    kb_entry_added_slug: str | None = None
    kb_commit_sha: str | None = None

    @model_validator(mode="after")
    def _consistency(self) -> "ReplayStep":
        if self.gap_created and self.draft_reply is not None:
            raise ValueError("gap_created=True requires draft_reply=None")
        if self.kb_entry_added_slug and not self.gap_created:
            raise ValueError("kb_entry_added_slug only valid on gap path")
        return self


class ReplayRun(BaseModel):
    """Aggregate metadata for one full replay run."""

    started_at: datetime
    finished_at: datetime
    seed_kb_sha: str
    ticket_count: int
    answered_count: int
    gap_count: int
    branch: str

    @property
    def answer_rate(self) -> float:
        return self.answered_count / self.ticket_count if self.ticket_count else 0.0


class RubricScore(BaseModel):
    """One rubric scoring (human or LLM-judge) for one draft."""

    ticket_id: str
    grounded: int = Field(ge=1, le=5)
    brand_voice: int = Field(ge=1, le=5)
    completeness: int = Field(ge=1, le=5)
    no_hallucination: int = Field(ge=1, le=5)
    tone_fit: int = Field(ge=1, le=5)
    notes: str = ""

    @property
    def overall(self) -> float:
        return round(
            (
                self.grounded
                + self.brand_voice
                + self.completeness
                + self.no_hallucination
                + self.tone_fit
            )
            / 5,
            2,
        )
