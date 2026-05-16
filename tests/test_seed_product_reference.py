"""Test product reference seeding."""
from pathlib import Path

from intel_engine.schemas.kb import KBDomain, KBEntry
from scripts.seed_product_reference import write_products_from_parsed


def test_write_products_creates_files_with_spec_domain(tmp_path: Path):
    parsed = [
        {
            "sku": "BOLDR-VENT-TI",
            "name": "Venture Titanium",
            "specs": "Grade 5 titanium case, 38mm, 200m WR, Miyota 9015 movement.",
        },
        {
            "sku": "BOLDR-FKM-22",
            "name": "FKM Rubber Strap 22mm",
            "specs": "100% BPA-free, hypoallergenic, salt-resistant.",
        },
    ]
    written = write_products_from_parsed(parsed, tmp_path, source_file="05b_product_reference.docx")
    assert len(written) == 2

    entry = KBEntry.from_markdown(written[0].read_text())
    assert entry.frontmatter.domain == KBDomain.spec
    assert entry.frontmatter.title == "Venture Titanium"
    assert "Grade 5 titanium" in entry.body
