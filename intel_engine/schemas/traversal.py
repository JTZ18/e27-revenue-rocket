"""Wiki-traversal agent structured output."""
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class Confidence(str, Enum):
    low = "low"
    med = "med"
    high = "high"


class TraversalResult(BaseModel):
    pages_read: list[str] = Field(
        description="KB file paths the agent considered relevant"
    )
    can_answer_fully: bool
    missing_info: list[str] = Field(
        default_factory=list,
        description="What the agent would need to know to answer fully; non-empty iff can_answer_fully=False",
    )
    draft_reply: str | None = Field(
        default=None,
        description="Brand-voice draft reply; None iff can_answer_fully=False",
    )
    themes_detected: list[str]
    persona_hints: list[str] = Field(default_factory=list)
    confidence: Confidence

    @model_validator(mode="after")
    def _consistency(self) -> "TraversalResult":
        if self.can_answer_fully and self.draft_reply is None:
            raise ValueError("draft_reply must be present when can_answer_fully is True")
        if not self.can_answer_fully and self.draft_reply is not None:
            raise ValueError("draft_reply must be None when can_answer_fully is False")
        return self
