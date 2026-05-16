"""Test themes writer."""
import subprocess
from pathlib import Path

from intel_engine.schemas.theme import Theme, ThemeReport
from intel_engine.themes.writer import write_and_commit_theme_report


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "kb").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@x"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)
    (repo / "README.md").write_text("seed")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "seed"],
        cwd=repo, check=True,
    )
    return repo


def test_writer_writes_markdown_and_commits(tmp_path: Path):
    repo = _init_repo(tmp_path)
    report = ThemeReport(
        week_start="2026-05-11",
        week_end="2026-05-17",
        ticket_count=12,
        themes=[
            Theme(
                slug="bpa_safety",
                label="BPA safety",
                frequency=4,
                example_ticket_ids=["T1", "T2"],
                summary="Customers asking about BPA-free straps.",
            )
        ],
    )

    sha = write_and_commit_theme_report(report, repo_root=repo)
    out = repo / "kb" / "themes" / "2026-05-17.md"
    assert out.exists()
    assert "BPA safety" in out.read_text()
    assert "frequency: 4" in out.read_text()
    log = subprocess.run(
        ["git", "log", "--oneline"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout
    assert "themes: weekly report 2026-05-17" in log
    assert sha
