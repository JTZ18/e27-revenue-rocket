"""Test briefs writer."""
import subprocess
from pathlib import Path

from intel_engine.briefs.writer import write_and_commit_brief
from intel_engine.schemas.brief import (
    BriefInsight,
    BriefRecommendation,
    MarketingBrief,
)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
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


def test_writer_renders_and_commits(tmp_path: Path):
    repo = _init_repo(tmp_path)
    brief = MarketingBrief(
        month="2026-05",
        headline="May highlights",
        insights=[
            BriefInsight(
                theme="bpa_safety",
                ticket_count=5,
                persona_segments=["health_conscious"],
                observation="Recurring BPA-free questions.",
            )
        ],
        recommendations=[
            BriefRecommendation(
                target="product_page",
                action="Promote BPA-free badge",
                expected_impact="Reduce CS load",
                evidence_themes=["bpa_safety"],
            )
        ],
    )
    sha = write_and_commit_brief(brief, repo_root=repo)
    out = repo / "briefs" / "2026-05-marketing-brief.md"
    assert out.exists()
    text = out.read_text()
    assert "May highlights" in text
    assert "Promote BPA-free badge" in text
    assert sha
