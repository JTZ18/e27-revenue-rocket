"""Parse FAQ PDF into KB markdown via LLM."""
import asyncio
import re
from datetime import date
from pathlib import Path

import pdfplumber

from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter

PARSE_PROMPT = """\
You are converting a Boldr customer-service FAQ PDF into a structured list.

Return a JSON object with key "entries" whose value is an array of objects:
{
  "entries": [
    {
      "theme": "...",         // one of: materials_safety, engraving,
                                // strap_compatibility, servicing, order_status,
                                // shipping, product_general, sustainability,
                                // aftercare
      "question": "...",      // the question verbatim
      "answer": "..."         // the answer verbatim, preserving the brand voice
    }
  ]
}

Rules:
- Preserve punctuation, currency formatting ("SGD 85"), and cited standards verbatim
- Do not summarise or rephrase
- One entry per Q/A pair; do not merge entries
- If a section header introduces multiple Q/A pairs, tag each with the section theme
"""


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:80]


def extract_pdf_text(pdf_path: Path) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        return "\n\n".join((page.extract_text() or "") for page in pdf.pages)


async def parse_faq_with_llm(text: str) -> list[dict[str, str]]:
    client = LLMClient(provider=LLMProvider.kimi)
    result = await client.complete_json(
        system=PARSE_PROMPT,
        user=f"FAQ document:\n\n{text}",
    )
    return result["entries"]


def write_faqs_from_parsed(
    parsed: list[dict[str, str]],
    out_dir: Path,
    source_file: str,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for item in parsed:
        slug = slugify(item["question"])
        entry = KBEntry(
            frontmatter=KBFrontmatter(
                slug=slug,
                title=item["question"],
                domain=KBDomain.faq,
                themes=[item["theme"]],
                sources=[f"data/{source_file}"],
                last_verified=date.today(),
            ),
            body=item["answer"],
        )
        path = out_dir / f"{slug}.md"
        path.write_text(entry.to_markdown())
        written.append(path)
    return written


async def main() -> None:
    pdf_path = Path("data/04_faq_document.pdf")
    text = extract_pdf_text(pdf_path)
    parsed = await parse_faq_with_llm(text)
    written = write_faqs_from_parsed(parsed, Path("kb/faqs"), source_file=pdf_path.name)
    print(f"Wrote {len(written)} FAQ entries to kb/faqs/")


if __name__ == "__main__":
    asyncio.run(main())
