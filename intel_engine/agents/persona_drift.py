"""Persona drift detector (Minimax)."""
from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.llm.prompts import load_prompt
from intel_engine.schemas.persona import (
    PersonaDefinition,
    PersonaDriftReport,
    PersonaProposal,
)


def _format_personas(personas: list[PersonaDefinition]) -> str:
    if not personas:
        return "(none)"
    parts = []
    for p in personas:
        parts.append(
            f"- [{p.axis.value}/{p.slug}] {p.label} — signals: {', '.join(p.signals)}"
        )
    return "\n".join(parts)


def _format_tickets(tickets: list[dict]) -> str:
    lines = []
    for t in tickets:
        body = str(t.get("message_body") or "").replace("\n", " ")
        lines.append(f"[{t['ticket_id']}] {body[:240]}")
    return "\n".join(lines)


async def detect_drift(
    *,
    active_personas: list[PersonaDefinition],
    tickets: list[dict],
    window_start: str,
    window_end: str,
) -> PersonaDriftReport:
    system = load_prompt("persona-drift-agent")
    user = (
        f"=== ACTIVE PERSONAS ===\n{_format_personas(active_personas)}\n\n"
        f"=== TICKETS ({window_start} → {window_end}) ===\n"
        f"{_format_tickets(tickets)}\n\n"
        f"Detect drift now."
    )
    client = LLMClient(provider=LLMProvider.minimax)
    raw = await client.complete_json(system=system, user=user)

    return PersonaDriftReport(
        window_start=window_start,
        window_end=window_end,
        unmatched_tickets=int(raw.get("unmatched_tickets", 0)),
        proposals=[PersonaProposal(**p) for p in raw.get("proposals", [])],
        stale_candidates=list(raw.get("stale_candidates", [])),
    )
