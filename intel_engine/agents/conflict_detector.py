"""Weekly KB conflict detector (Kimi)."""
from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.llm.prompts import load_prompt
from intel_engine.schemas.conflict import ConflictDigest, KBConflict


def _format_kb(entries: list[dict]) -> str:
    return "\n".join(
        f"[{e['domain']}] {e['path']} — {e['title']}: {e.get('excerpt', '')[:200]}"
        for e in entries
    )


async def detect_conflicts(
    *,
    kb_entries: list[dict],
    week_end: str,
) -> ConflictDigest:
    system = load_prompt("conflict-detector-agent")
    user = (
        f"=== KB ENTRIES ({len(kb_entries)} active) ===\n"
        f"{_format_kb(kb_entries)}\n\n"
        f"Detect conflicts now."
    )
    client = LLMClient(provider=LLMProvider.kimi)
    raw = await client.complete_json(system=system, user=user)

    return ConflictDigest(
        week_end=week_end,
        conflicts=[KBConflict(**c) for c in raw.get("conflicts", [])],
    )
