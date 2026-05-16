"""Extract SOP §5 (brand voice) and §7 (escalation) into KB."""
import asyncio
from datetime import date
from pathlib import Path

from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter
from scripts.seed_product_reference import extract_docx_text

EXTRACT_PROMPT = """\
You are extracting structured policy data from a customer-service SOP document.

Return JSON with two keys:
{
  "brand_voice": "...",      // The full content of Section 5 (Brand Voice / Response Style)
                              // including preferred openers, forbidden phrases, tone rules,
                              // currency conventions, and any examples — verbatim.
  "escalation": "..."         // The full content of Section 7 (Escalation Triggers) —
                              // a list of conditions that require escalating to senior staff,
                              // verbatim.
}

If a section is missing, set the value to an empty string.
"""


def write_schema(body: str, out_path: Path) -> None:
    content = (
        "# Brand Voice Contract\n\n"
        "This file defines Boldr's customer-service voice. "
        "The wiki-traversal agent reads this on every draft reply.\n\n"
        f"{body.strip()}\n"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content)


def write_escalation_policy(body: str, out_path: Path, source_file: str) -> None:
    entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="escalation-policy",
            title="Escalation triggers — when to route to senior staff",
            domain=KBDomain.policy,
            themes=["escalation", "policy"],
            sources=[f"data/{source_file}"],
            last_verified=date.today(),
        ),
        body=body.strip(),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(entry.to_markdown())


async def main() -> None:
    src = Path("data/05a_SOP.docx")
    text = extract_docx_text(src)
    client = LLMClient(provider=LLMProvider.kimi)
    result = await client.complete_json(
        system=EXTRACT_PROMPT,
        user=f"SOP:\n\n{text}",
    )

    write_schema(result["brand_voice"], Path("kb/_schema.md"))
    write_escalation_policy(
        result["escalation"],
        Path("kb/policies/escalation.md"),
        source_file=src.name,
    )
    print("Wrote kb/_schema.md and kb/policies/escalation.md")


if __name__ == "__main__":
    asyncio.run(main())
