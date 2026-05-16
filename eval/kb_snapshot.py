"""Snapshot kb/ before a replay; clear kb/faqs/; restore after."""
import shutil
from pathlib import Path


class KBSnapshot:
    """In-memory + on-disk snapshot of kb/faqs/.

    The replay harness starts with an empty faqs/ directory and fabricates new
    entries as it processes tickets. After the run, restore() puts the original
    files back so the working tree is clean.
    """

    def __init__(self, kb_root: Path) -> None:
        self.kb_root = kb_root
        self.faqs_dir = kb_root / "faqs"
        self._backup: dict[str, str] = {}

    def start_replay_state(self) -> None:
        self._backup = {}
        if self.faqs_dir.exists():
            for path in self.faqs_dir.glob("*.md"):
                self._backup[path.name] = path.read_text()
                path.unlink()
        else:
            self.faqs_dir.mkdir(parents=True)

    def restore(self) -> None:
        if not self.faqs_dir.exists():
            self.faqs_dir.mkdir(parents=True)
        # Delete anything the harness wrote
        for path in self.faqs_dir.glob("*.md"):
            path.unlink()
        # Restore originals
        for name, body in self._backup.items():
            (self.faqs_dir / name).write_text(body)


def copy_seed_kb(src: Path, dest: Path) -> None:
    """Copy a KB directory tree for use in a sandbox run."""
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
