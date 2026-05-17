"""Monthly marketing brief writer (OpenRouter)."""
from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.llm.prompts import load_prompt
from intel_engine.schemas.brief import (
    BriefInsight,
    BriefRecommendation,
    MarketingBrief,
)
from intel_engine.schemas.persona import PersonaDefinition
from intel_engine.schemas.sentiment import SentimentComparison
from intel_engine.schemas.theme import ThemeReport


def _format_themes(reports: list[ThemeReport]) -> str:
    lines = []
    for report in reports:
        lines.append(f"=== Week {report.week_start} → {report.week_end} ===")
        for theme in report.themes:
            lines.append(
                f"  [{theme.slug}] freq={theme.frequency} — {theme.summary}"
            )
    return "\n".join(lines)


def _format_personas(personas: list[PersonaDefinition]) -> str:
    return "\n".join(
        f"- [{p.axis.value}/{p.slug}] {p.label}" for p in personas
    )


def _format_sentiment(comparisons: list[SentimentComparison]) -> str:
    if not comparisons:
        return "(no external sentiment data this month)"
    return "\n".join(
        f"- [{c.theme_slug}] verdict={c.verdict.value} "
        f"internal={c.internal_frequency} external={c.external_mentions} — "
        f"{c.suggested_action}"
        for c in comparisons
    )


async def write_brief(
    *,
    month: str,
    theme_reports: list[ThemeReport],
    personas: list[PersonaDefinition],
    kb_summary: str,
    sentiment: list[SentimentComparison] | None = None,
) -> MarketingBrief:
    """Generate a monthly marketing brief from theme reports, personas, and sentiment."""
    sentiment = sentiment or []
    system = load_prompt("brief-writer-agent")
    user = (
        f"=== MONTH: {month} ===\n\n"
        f"=== WEEKLY THEME REPORTS ===\n{_format_themes(theme_reports)}\n\n"
        f"=== ACTIVE PERSONAS ===\n{_format_personas(personas)}\n\n"
        f"=== EXTERNAL SENTIMENT (last30days) ===\n{_format_sentiment(sentiment)}\n\n"
        f"=== KB SUMMARY ===\n{kb_summary}\n\n"
        f"Write the brief now. When citing a theme that has external sentiment data, "
        f"reference the verdict in your recommendation."
    )
    client = LLMClient(provider=LLMProvider.openrouter)
    raw = await client.complete_json(system=system, user=user)

    return MarketingBrief(
        month=month,
        headline=raw.get("headline"),
        insights=[BriefInsight(**i) for i in raw.get("insights", [])],
        recommendations=[
            BriefRecommendation(**r) for r in raw.get("recommendations", [])
        ],
        external_sentiment=sentiment,
    )
