"""Test KB writer + git auto-commit."""
import subprocess
from datetime import date
from pathlib import Path

import pytest

from intel_engine.kb.writer import write_and_commit_entry
from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter


@pytest.fixture
def git_repo(tmp_path: Path, monkeypatch) -> Path:
    """Create a fresh git repo at tmp_path with kb/ structure."""
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Test Bot")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "test@test.local")

    (tmp_path / "kb" / "_workflows").mkdir(parents=True)
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test Bot"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.local"], cwd=tmp_path, check=True
    )
    # Initial commit so HEAD exists
    (tmp_path / "README.md").write_text("# Test repo")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-m", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    return tmp_path


def test_write_and_commit_writes_entry_to_correct_path(git_repo: Path):
    entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="test-entry",
            title="Test entry",
            domain=KBDomain.faq,
            themes=["test"],
            sources=["test-source"],
            last_verified=date(2026, 5, 16),
        ),
        body="Test body.",
    )
    sha = write_and_commit_entry(
        entry,
        approver="sarah@boldr.sg",
        repo_root=git_repo,
    )
    expected_path = git_repo / "kb" / "faq" / "test-entry.md"
    assert expected_path.exists()
    assert "test body" in expected_path.read_text().lower()
    assert len(sha) >= 7  # short SHA


def test_write_and_commit_includes_approver_in_commit_message(git_repo: Path):
    entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="test2",
            title="T2",
            domain=KBDomain.faq,
            themes=[],
            sources=[],
            last_verified=date(2026, 5, 16),
        ),
        body="body",
    )
    write_and_commit_entry(entry, approver="alice@boldr.sg", repo_root=git_repo)
    log = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        cwd=git_repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "alice@boldr.sg" in log
    assert "kb: add" in log or "kb: update" in log


def test_write_and_commit_regenerates_index(git_repo: Path):
    entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="indexed",
            title="Indexed entry",
            domain=KBDomain.faq,
            themes=["x"],
            sources=[],
            last_verified=date(2026, 5, 16),
        ),
        body="body",
    )
    write_and_commit_entry(entry, approver="x@x.com", repo_root=git_repo)
    index_path = git_repo / "kb" / "index.md"
    assert index_path.exists()
    assert "indexed" in index_path.read_text()
