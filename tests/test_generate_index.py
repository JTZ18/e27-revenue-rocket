"""Test index generation."""
from pathlib import Path

from scripts.generate_index import generate_index


def test_generate_index_lists_all_entries(tmp_path: Path):
    (tmp_path / "faqs").mkdir()
    (tmp_path / "faqs" / "bpa.md").write_text(
        "---\nslug: bpa\ntitle: BPA-free?\ndomain: faq\n"
        "themes: [materials]\nlast_verified: 2026-05-16\n---\n\nbody"
    )
    (tmp_path / "rate-cards").mkdir()
    (tmp_path / "rate-cards" / "engraving.md").write_text(
        "---\nslug: engraving-rates\ntitle: Engraving prices\ndomain: pricing\n"
        "themes: [engraving]\nlast_verified: 2026-05-16\n---\n\nbody"
    )

    out = tmp_path / "index.md"
    generate_index(tmp_path, out)

    md = out.read_text()
    assert "# Knowledge Base Index" in md
    assert "bpa" in md
    assert "engraving-rates" in md
    assert "## faq" in md.lower() or "### faq" in md.lower()
