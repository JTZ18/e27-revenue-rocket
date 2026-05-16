"""Test brief schemas."""
import pytest
from pydantic import ValidationError

from intel_engine.schemas.brief import (
    BriefInsight,
    BriefRecommendation,
    MarketingBrief,
)


def test_marketing_brief_minimum_sections():
    brief = MarketingBrief(
        month="2026-05",
        headline="May: sustainability moving fast.",
        insights=[
            BriefInsight(
                theme="sustainability",
                ticket_count=8,
                persona_segments=["sustainability_buyer"],
                observation="8 unaddressed vegan-strap mentions.",
            )
        ],
        recommendations=[
            BriefRecommendation(
                target="product_page",
                action="Add vegan-strap section",
                expected_impact="Reduce repeated CS queries by ~20%",
                evidence_themes=["sustainability"],
            )
        ],
    )
    assert brief.month == "2026-05"
    assert len(brief.insights) == 1


def test_brief_recommendation_target_is_constrained():
    with pytest.raises(ValidationError):
        BriefRecommendation(
            target="invalid_surface",
            action="x",
            expected_impact="y",
            evidence_themes=["z"],
        )


def test_marketing_brief_rejects_invalid_month():
    with pytest.raises(ValidationError):
        MarketingBrief(
            month="2026-5",
            headline="x",
            insights=[
                BriefInsight(
                    theme="t",
                    ticket_count=1,
                    persona_segments=["p"],
                    observation="o",
                )
            ],
            recommendations=[
                BriefRecommendation(
                    target="product_page",
                    action="a",
                    expected_impact="i",
                    evidence_themes=["t"],
                )
            ],
        )
