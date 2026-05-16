"""Snapshot kb/ before a replay; clear kb/faq/; restore after."""
import shutil
from pathlib import Path


class KBSnapshot:
    """In-memory + on-disk snapshot of kb/faq/.

    The replay harness starts with an empty faq/ directory and fabricates new
    entries as it processes tickets. After the run, restore() puts the original
    files back so the working tree is clean.
    """

    def __init__(self, kb_root: Path) -> None:
        self.kb_root = kb_root
        self.faq_dir = kb_root / "faq"
        self._backup: dict[str, str] = {}

    def start_replay_state(self) -> None:
        self._backup = {}
        if self.faq_dir.exists():
            for path in self.faq_dir.glob("*.md"):
                self._backup[path.name] = path.read_text()
                path.unlink()
        else:
            self.faq_dir.mkdir(parents=True)

    def restore(self) -> None:
        if not self.faq_dir.exists():
            self.faq_dir.mkdir(parents=True)
        # Delete anything the harness wrote
        for path in self.faq_dir.glob("*.md"):
            path.unlink()
        # Restore originals
        for name, body in self._backup.items():
            (self.faq_dir / name).write_text(body)


def copy_seed_kb(src: Path, dest: Path) -> None:
    """Copy a KB directory tree for use in a sandbox run."""
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
