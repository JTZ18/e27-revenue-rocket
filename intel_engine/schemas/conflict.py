"""KB conflict schemas."""
from pydantic import BaseModel, Field, model_validator


class KBConflict(BaseModel):
    domain: str
    fact_topic: str
    entries: list[str] = Field(min_length=2)
    canonical_proposal: str
    reasoning: str

    @model_validator(mode="after")
    def check_canonical_in_entries(self):
        if self.canonical_proposal not in self.entries:
            raise ValueError("canonical_proposal must be one of the entries")
        return self


class ConflictDigest(BaseModel):
    week_end: str
    conflicts: list[KBConflict] = Field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.conflicts)
