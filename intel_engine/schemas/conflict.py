"""KB conflict schemas."""
from pydantic import BaseModel, Field


class KBConflict(BaseModel):
    domain: str
    fact_topic: str
    entries: list[str] = Field(min_length=2)
    canonical_proposal: str
    reasoning: str


class ConflictDigest(BaseModel):
    week_end: str
    conflicts: list[KBConflict] = Field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.conflicts)
