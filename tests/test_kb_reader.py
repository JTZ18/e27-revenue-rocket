"""Test KB reader."""
from pathlib import Path

from intel_engine.kb.reader import load_kb


def test_load_kb_reads_all_markdown_files(tmp_path: Path):
    (tmp_path / "faqs").mkdir()
    (tmp_path / "faqs" / "a.md").write_text(
        "---\nslug: a\ntitle: A\ndomain: faq\nlast_verified: 2026-05-16\n---\n\nbody A"
    )
    (tmp_path / "faqs" / "b.md").write_text(
        "---\nslug: b\ntitle: B\ndomain: faq\nlast_verified: 2026-05-16\n---\n\nbody B"
    )

    entries = load_kb(tmp_path)
    assert len(entries) == 2
    slugs = {e.frontmatter.slug for e in entries}
    assert slugs == {"a", "b"}


def test_load_kb_skips_underscore_files(tmp_path: Path):
    (tmp_path / "_schema.md").write_text("# brand voice")
    (tmp_path / "_log.md").write_text("# audit")
    (tmp_path / "faqs").mkdir()
    (tmp_path / "faqs" / "a.md").write_text(
        "---\nslug: a\ntitle: A\ndomain: faq\nlast_verified: 2026-05-16\n---\n\nbody A"
    )

    entries = load_kb(tmp_path)
    assert len(entries) == 1


def test_load_kb_skips_stale_entries(tmp_path: Path):
    (tmp_path / "faqs").mkdir()
    (tmp_path / "faqs" / "active.md").write_text(
        "---\nslug: active\ntitle: A\ndomain: faq\n"
        "last_verified: 2026-05-16\nstatus: active\n---\n\nactive"
    )
    (tmp_path / "faqs" / "stale.md").write_text(
        "---\nslug: stale\ntitle: S\ndomain: faq\n"
        "last_verified: 2026-01-01\nstatus: stale\n---\n\nstale"
    )

    entries = load_kb(tmp_path)
    slugs = {e.frontmatter.slug for e in entries}
    assert slugs == {"active"}
