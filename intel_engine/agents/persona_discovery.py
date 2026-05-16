"""Cold-start persona discovery agent (OpenRouter)."""
from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.llm.prompts import load_prompt
from intel_engine.schemas.persona import PersonaProposal


def _format_tickets(tickets: list[dict]) -> str:
    lines = []
    for t in tickets:
        body = str(t.get("message_body") or "").replace("\n", " ")
        lines.append(f"[{t['ticket_id']}] {body[:280]}")
    return "\n".join(lines)


async def discover_personas(tickets: list[dict]) -> list[PersonaProposal]:
    system = load_prompt("persona-discovery-agent")
    user = (
        f"=== TICKET DUMP ({len(tickets)} tickets) ===\n"
        f"{_format_tickets(tickets)}\n\n"
        f"Propose persona taxonomy now."
    )
    client = LLMClient(provider=LLMProvider.openrouter)
    raw = await client.complete_json(system=system, user=user)
    proposals_data = raw.get("proposals", [])
    return [PersonaProposal(**p) for p in proposals_data]
