"""Test rate card seeding."""
import csv
from pathlib import Path

from intel_engine.schemas.kb import KBEntry
from scripts.seed_rate_cards import seed_rate_card


def test_seed_engraving_rate_card(tmp_path: Path):
    src = tmp_path / "engraving.csv"
    src.write_text(
        "service,price_sgd,notes\n"
        "Initials engraving,25,Up to 4 Latin characters\n"
        "Full name engraving,45,Up to 15 Latin characters\n"
    )
    out = tmp_path / "kb" / "rate-cards" / "engraving.md"

    seed_rate_card(
        src=src,
        out_path=out,
        slug="engraving-rate-card",
        title="Engraving services — pricing and rules",
        themes=["engraving", "pricing"],
    )

    assert out.exists()
    md = out.read_text()
    entry = KBEntry.from_markdown(md)
    assert entry.frontmatter.slug == "engraving-rate-card"
    assert entry.frontmatter.domain.value == "pricing"
    assert "Initials engraving" in entry.body
    assert "SGD 25" in entry.body
