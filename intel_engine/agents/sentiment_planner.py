"""Weekly sentiment planner agent (Minimax)."""
from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.llm.prompts import load_prompt
from intel_engine.schemas.sentiment import SentimentQueryPlan
from intel_engine.schemas.theme import Theme


def _format_theme(theme: Theme) -> str:
    return (
        f"slug: {theme.slug}\n"
        f"label: {theme.label}\n"
        f"frequency: {theme.frequency}\n"
        f"example_ticket_ids: {', '.join(theme.example_ticket_ids)}\n"
        f"summary: {theme.summary}\n"
    )


async def plan_query_for_theme(
    *,
    theme: Theme,
    kb_excerpt: str = "",
) -> SentimentQueryPlan:
    """Produce a SentimentQueryPlan suitable for last30days --plan."""
    system = load_prompt("sentiment-planner-agent")
    user = (
        f"=== THEME ===\n{_format_theme(theme)}\n"
        f"=== KB CONTEXT (optional) ===\n{kb_excerpt}\n\n"
        f"Produce the query plan now."
    )
    client = LLMClient(provider=LLMProvider.minimax)
    raw = await client.complete_json(system=system, user=user)
    return SentimentQueryPlan(
        topic=raw.get("topic", theme.label),
        search_terms=raw.get("search_terms", [theme.label]),
        subreddits=raw.get("subreddits", []),
        related_handles=raw.get("related_handles", []),
        notes=raw.get("notes", ""),
    )
