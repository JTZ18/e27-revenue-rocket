"""Weekly theme clusterer (Minimax)."""
from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.llm.prompts import load_prompt
from intel_engine.schemas.theme import Theme, ThemeReport


def _format_tickets(tickets: list[dict]) -> str:
    return "\n".join(
        f"[{t['ticket_id']}] {str(t.get('message_body') or '')[:240]}"
        for t in tickets
    )


async def cluster_themes(
    *,
    tickets: list[dict],
    week_start: str,
    week_end: str,
) -> ThemeReport:
    system = load_prompt("theme-clusterer-agent")
    user = (
        f"=== TICKETS ({week_start} → {week_end}) ===\n"
        f"{_format_tickets(tickets)}\n\n"
        f"Cluster now."
    )
    client = LLMClient(provider=LLMProvider.minimax)
    raw = await client.complete_json(system=system, user=user)
    themes = [Theme(**t) for t in raw.get("themes", [])]
    return ThemeReport(
        week_start=week_start,
        week_end=week_end,
        ticket_count=len(tickets),
        themes=themes,
    )
