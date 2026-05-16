"""KB Drafter agent — converts a resolved gap into a KB entry."""
from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.llm.prompts import load_prompt
from intel_engine.schemas.gap import Gap
from intel_engine.schemas.kb import KBEntry, KBFrontmatter


async def draft_kb_entry(gap: Gap) -> KBEntry:
    if gap.resolution is None:
        raise ValueError("Cannot draft KB entry: gap has no resolution")

    system_prompt = load_prompt("kb-drafter-agent")

    schema_text = ""
    from intel_engine.settings import kb_root
    schema_path = kb_root() / "_schema.md"
    if schema_path.exists():
        schema_text = schema_path.read_text()

    user_message = (
        f"=== BRAND VOICE CONTRACT ===\n{schema_text}\n\n"
        f"=== CUSTOMER QUESTION ===\n{gap.customer_question}\n\n"
        f"=== THEMES DETECTED ===\n{', '.join(gap.themes_detected)}\n\n"
        f"=== HUMAN RESOLUTION ===\n{gap.resolution.resolution_text}\n\n"
        f"=== SOURCE NOTE ===\n{gap.resolution.source_note or '(none)'}\n\n"
        f"=== GAP ID (for sources field) ===\n{gap.gap_id}"
    )

    client = LLMClient(provider=LLMProvider.openrouter)
    raw = await client.complete_json(system=system_prompt, user=user_message)
    return KBEntry(
        frontmatter=KBFrontmatter.model_validate(raw["frontmatter"]),
        body=raw["body"],
    )
