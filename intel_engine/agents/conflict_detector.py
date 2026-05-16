"""Weekly KB conflict detector (OpenRouter)."""
from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.llm.prompts import load_prompt
from intel_engine.schemas.conflict import ConflictDigest, KBConflict


def _format_kb(entries: list[dict]) -> str:
    return "\n".join(
        f"[{e.get('domain', 'UNKNOWN')}] {e.get('path', 'UNKNOWN')} — {e.get('title', 'UNKNOWN')}: {e.get('excerpt', '')[:200]}"
        for e in entries
    )


async def detect_conflicts(
    *,
    kb_entries: list[dict],
    week_end: str,
) -> ConflictDigest:
    system = load_prompt("conflict-detector-agent")
    user = (
        f"Week ending: {week_end}\n"
        f"=== KB ENTRIES ({len(kb_entries)} active) ===\n"
        f"{_format_kb(kb_entries)}\n\n"
        f"Detect conflicts now."
    )
    client = LLMClient(provider=LLMProvider.openrouter)
    raw = await client.complete_json(system=system, user=user)

    return ConflictDigest(
        week_end=week_end,
        conflicts=[KBConflict(**c) for c in raw.get("conflicts", [])],
    )
