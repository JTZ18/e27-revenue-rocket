"""Test FAQ seeding (LLM parsing mocked)."""
from pathlib import Path

from intel_engine.schemas.kb import KBEntry
from scripts.seed_faq import write_faqs_from_parsed


def test_write_faqs_creates_one_file_per_entry(tmp_path: Path):
    parsed = [
        {
            "theme": "materials_safety",
            "question": "Are Boldr FKM rubber straps BPA-free?",
            "answer": "Yes. All Boldr FKM rubber and silicone straps are 100% BPA-free.",
        },
        {
            "theme": "engraving",
            "question": "Do you support Arabic engraving?",
            "answer": "Yes. Arabic script is supported with a custom font option.",
        },
    ]
    out_dir = tmp_path / "kb" / "faqs"
    written = write_faqs_from_parsed(parsed, out_dir, source_file="04_faq_document.pdf")

    assert len(written) == 2
    for path in written:
        assert path.exists()
        entry = KBEntry.from_markdown(path.read_text())
        assert entry.frontmatter.domain.value == "faq"
        assert entry.frontmatter.sources == ["data/04_faq_document.pdf"]


def test_slug_generation_handles_punctuation(tmp_path: Path):
    parsed = [
        {
            "theme": "materials_safety",
            "question": "Is this watch safe for kids? (children's edition)",
            "answer": "Yes, all watches meet EU REACH toy safety standards.",
        }
    ]
    written = write_faqs_from_parsed(parsed, tmp_path, source_file="04_faq_document.pdf")
    assert written[0].stem == "is-this-watch-safe-for-kids-childrens-edition"
