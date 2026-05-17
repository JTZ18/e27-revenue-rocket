"""Sentiment loop schemas — external benchmarking via last30days."""
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SentimentVerdict(str, Enum):
    boldr_specific = "boldr_specific"   # internal >> external — niche concern
    market_wide = "market_wide"         # external >> internal — capitalise
    aligned = "aligned"                 # comparable signal both sides
    insufficient_data = "insufficient_data"


class SentimentQueryPlan(BaseModel):
    """JSON plan fed to last30days.py via --plan."""

    topic: str = Field(min_length=3)
    search_terms: list[str] = Field(min_length=1)
    subreddits: list[str] = Field(default_factory=list)
    related_handles: list[str] = Field(default_factory=list)
    notes: str = ""


class ExternalSentimentReport(BaseModel):
    """Parsed result of running last30days.py for a single theme."""

    theme_slug: str
    ran_at: str
    topic: str
    external_mentions: int = Field(ge=0)
    top_sources: list[str] = Field(default_factory=list)
    snippets: list[str] = Field(default_factory=list)
    raw_emit: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw JSON returned by `last30days --emit json` for audit/replay.",
    )


class SentimentComparison(BaseModel):
    """Verdict from the comparator agent for one theme."""

    theme_slug: str
    internal_frequency: int = Field(ge=0)
    external_mentions: int = Field(ge=0)
    verdict: SentimentVerdict
    reasoning: str = Field(min_length=10)
    suggested_action: str = Field(min_length=5)


class SentimentWeeklyDigest(BaseModel):
    week_end: str
    comparisons: list[SentimentComparison] = Field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.comparisons)
