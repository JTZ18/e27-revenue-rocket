"""Test KB snapshot/restore."""
from pathlib import Path

from eval.kb_snapshot import KBSnapshot


def test_snapshot_clears_only_faqs(tmp_path: Path):
    kb = tmp_path / "kb"
    (kb / "faqs").mkdir(parents=True)
    (kb / "rate-cards").mkdir()
    (kb / "products").mkdir()
    (kb / "faqs" / "bpa.md").write_text("---\nslug: bpa\n---\n")
    (kb / "faqs" / "vegan.md").write_text("---\nslug: vegan\n---\n")
    (kb / "rate-cards" / "engraving.md").write_text("---\nslug: engraving\n---\n")
    (kb / "products" / "expedition.md").write_text("---\nslug: expedition\n---\n")
    (kb / "index.md").write_text("# Index\n")

    snap = KBSnapshot(kb)
    snap.start_replay_state()

    assert not (kb / "faqs" / "bpa.md").exists()
    assert not (kb / "faqs" / "vegan.md").exists()
    assert (kb / "rate-cards" / "engraving.md").exists()
    assert (kb / "products" / "expedition.md").exists()


def test_restore_brings_back_originals(tmp_path: Path):
    kb = tmp_path / "kb"
    (kb / "faqs").mkdir(parents=True)
    (kb / "faqs" / "bpa.md").write_text("ORIGINAL")

    snap = KBSnapshot(kb)
    snap.start_replay_state()

    # simulate harness writing a new entry
    (kb / "faqs" / "mri.md").write_text("FABRICATED")
    assert (kb / "faqs" / "mri.md").exists()

    snap.restore()

    assert (kb / "faqs" / "bpa.md").read_text() == "ORIGINAL"
    assert not (kb / "faqs" / "mri.md").exists()
