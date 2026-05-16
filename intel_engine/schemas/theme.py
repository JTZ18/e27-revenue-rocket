"""Theme schemas — weekly clustering output."""
from pydantic import BaseModel, Field


class Theme(BaseModel):
    slug: str
    label: str
    frequency: int = Field(ge=1)
    example_ticket_ids: list[str] = Field(min_length=1)
    summary: str


class ThemeReport(BaseModel):
    week_start: str
    week_end: str
    ticket_count: int
    themes: list[Theme] = Field(default_factory=list)

    def top_slug(self) -> str | None:
        if not self.themes:
            return None
        return max(self.themes, key=lambda t: t.frequency).slug
