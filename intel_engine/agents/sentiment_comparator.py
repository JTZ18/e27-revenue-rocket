"""Internal vs external sentiment comparator (OpenRouter / Kimi-tier)."""
from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.llm.prompts import load_prompt
from intel_engine.schemas.sentiment import (
    ExternalSentimentReport,
    SentimentComparison,
    SentimentVerdict,
)
from intel_engine.schemas.theme import Theme


def _format_theme(theme: Theme) -> str:
    return (
        f"slug: {theme.slug}\n"
        f"label: {theme.label}\n"
        f"internal_frequency: {theme.frequency}\n"
        f"example_ticket_ids: {', '.join(theme.example_ticket_ids)}\n"
        f"summary: {theme.summary}\n"
    )


def _format_external(report: ExternalSentimentReport) -> str:
    snippets = "\n".join(f"  - {s}" for s in report.snippets[:5])
    sources = ", ".join(report.top_sources)
    return (
        f"theme_slug: {report.theme_slug}\n"
        f"topic: {report.topic}\n"
        f"external_mentions: {report.external_mentions}\n"
        f"top_sources: {sources}\n"
        f"snippets:\n{snippets}\n"
    )


async def compare_sentiment(
    *,
    theme: Theme,
    external: ExternalSentimentReport,
) -> SentimentComparison:
    """Produce an internal-vs-external verdict for one theme."""
    if theme.slug != external.theme_slug:
        raise ValueError(
            f"theme slug mismatch: theme={theme.slug!r} report={external.theme_slug!r}"
        )

    system = load_prompt("sentiment-comparator-agent")
    user = (
        f"=== INTERNAL (Boldr tickets, last week) ===\n{_format_theme(theme)}\n"
        f"=== EXTERNAL (last30days, last 30 days) ===\n{_format_external(external)}\n\n"
        f"Produce the comparison JSON now."
    )
    client = LLMClient(provider=LLMProvider.openrouter)
    raw = await client.complete_json(system=system, user=user)

    try:
        verdict = SentimentVerdict(raw.get("verdict", "insufficient_data"))
    except ValueError:
        verdict = SentimentVerdict.insufficient_data

    return SentimentComparison(
        theme_slug=theme.slug,
        internal_frequency=theme.frequency,
        external_mentions=external.external_mentions,
        verdict=verdict,
        reasoning=raw.get("reasoning", "No reasoning provided."),
        suggested_action=raw.get("suggested_action", "No action suggested."),
    )
