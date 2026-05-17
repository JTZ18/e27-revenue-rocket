"""Test sentiment schemas."""
import pytest
from pydantic import ValidationError

from intel_engine.schemas.sentiment import (
    ExternalSentimentReport,
    SentimentComparison,
    SentimentQueryPlan,
    SentimentVerdict,
    SentimentWeeklyDigest,
)


def test_query_plan_requires_topic():
    with pytest.raises(ValidationError):
        SentimentQueryPlan(topic="", search_terms=["bpa"])


def test_query_plan_minimum_terms():
    plan = SentimentQueryPlan(
        topic="BPA-free titanium watch straps",
        search_terms=["BPA-free silicone", "BPA-free straps"],
        subreddits=["AskScience", "watches"],
        related_handles=[],
    )
    assert plan.topic.startswith("BPA")
    assert len(plan.search_terms) == 2


def test_external_report_carries_findings():
    report = ExternalSentimentReport(
        theme_slug="bpa_free",
        ran_at="2026-05-17T10:00:00+08:00",
        topic="BPA-free titanium watch straps",
        external_mentions=14,
        top_sources=["reddit.com/r/watches", "hn"],
        snippets=["FKM is generally BPA-free."],
        raw_emit={"clusters": []},
    )
    assert report.external_mentions == 14
    assert report.theme_slug == "bpa_free"


def test_sentiment_verdict_is_constrained():
    with pytest.raises(ValidationError):
        SentimentComparison(
            theme_slug="bpa_free",
            internal_frequency=4,
            external_mentions=14,
            verdict="not_a_verdict",  # type: ignore[arg-type]
            reasoning="This reasoning is long enough.",
            suggested_action="Take action",
        )


def test_sentiment_comparison_round_trip():
    cmp = SentimentComparison(
        theme_slug="vegan_straps",
        internal_frequency=8,
        external_mentions=42,
        verdict=SentimentVerdict.market_wide,
        reasoning="42 external vs 8 internal — broad market signal.",
        suggested_action="Add vegan-strap explainer to Expedition PDP.",
    )
    assert cmp.verdict == SentimentVerdict.market_wide
    assert cmp.model_dump()["verdict"] == "market_wide"


def test_weekly_digest_aggregates():
    digest = SentimentWeeklyDigest(
        week_end="2026-05-17",
        comparisons=[
            SentimentComparison(
                theme_slug="bpa_free",
                internal_frequency=2,
                external_mentions=14,
                verdict=SentimentVerdict.market_wide,
                reasoning="reasoning here",
                suggested_action="action here",
            ),
        ],
    )
    assert digest.count == 1
