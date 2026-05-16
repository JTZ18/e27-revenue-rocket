"""Wiki-traversal agent."""
from intel_engine.kb.reader import load_kb
from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.llm.prompts import load_prompt
from intel_engine.schemas.event import CommonEvent
from intel_engine.schemas.traversal import TraversalResult
from intel_engine.settings import kb_root


def _format_kb_for_prompt(kb_path) -> str:
    """Render the entire KB into a single text block the LLM can read."""
    entries = load_kb(kb_path)
    schema_path = kb_path / "_schema.md"
    schema_text = schema_path.read_text() if schema_path.exists() else ""

    parts: list[str] = []
    if schema_text:
        parts.append("=== BRAND VOICE CONTRACT (kb/_schema.md) ===")
        parts.append(schema_text)
        parts.append("")

    parts.append(f"=== KB ENTRIES ({len(entries)} active) ===\n")
    for entry in entries:
        fm = entry.frontmatter
        # Map slug back to relative path for citation accuracy
        path_hint = f"kb/{fm.domain.value}/{fm.slug}.md"  # agent uses this in pages_read
        parts.append(f"--- {path_hint} ---")
        parts.append(f"slug: {fm.slug}")
        parts.append(f"title: {fm.title}")
        parts.append(f"domain: {fm.domain.value}")
        parts.append(f"themes: {', '.join(fm.themes)}")
        parts.append("")
        parts.append(entry.body)
        parts.append("")
    return "\n".join(parts)


async def traverse(event: CommonEvent) -> TraversalResult:
    """Run the wiki-traversal agent on a single event."""
    kb_path = kb_root()
    system_prompt = load_prompt("traversal-agent")
    kb_block = _format_kb_for_prompt(kb_path)

    user_message = (
        f"=== CUSTOMER MESSAGE ===\n"
        f"Channel: {event.source.value}\n"
        f"From: {event.customer.name}\n"
        f"Subject: {event.subject or '(none)'}\n"
        f"Body:\n{event.body}\n\n"
        f"{kb_block}"
    )

    client = LLMClient(provider=LLMProvider.openrouter)
    raw = await client.complete_json(system=system_prompt, user=user_message)
    return TraversalResult.model_validate(raw)
