"""Marketing brief schemas."""
from enum import Enum

from pydantic import BaseModel, Field


class BriefTarget(str, Enum):
    product_page = "product_page"
    campaign = "campaign"
    kb = "kb"
    sop = "sop"


class BriefInsight(BaseModel):
    theme: str
    ticket_count: int = Field(ge=1)
    persona_segments: list[str] = Field(default_factory=list)
    observation: str


class BriefRecommendation(BaseModel):
    target: BriefTarget
    action: str
    expected_impact: str
    evidence_themes: list[str] = Field(min_length=1)


class MarketingBrief(BaseModel):
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
    headline: str
    insights: list[BriefInsight] = Field(default_factory=list)
    recommendations: list[BriefRecommendation] = Field(default_factory=list)
