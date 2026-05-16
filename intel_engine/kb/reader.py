"""Load KB entries from disk."""
from pathlib import Path

from intel_engine.schemas.kb import KBEntry, KBStatus


def load_kb(kb_root: Path) -> list[KBEntry]:
    """Walk kb_root, parse all *.md files (excluding _*.md), filter out stale."""
    entries: list[KBEntry] = []
    for path in kb_root.rglob("*.md"):
        if path.name.startswith("_"):
            continue
        try:
            entry = KBEntry.from_markdown(path.read_text())
        except (ValueError, KeyError) as e:
            # Malformed entries are skipped, not fatal
            print(f"Skipping malformed entry {path}: {e}")
            continue
        if entry.frontmatter.status == KBStatus.stale:
            continue
        entries.append(entry)
    return sorted(entries, key=lambda e: e.frontmatter.slug)
