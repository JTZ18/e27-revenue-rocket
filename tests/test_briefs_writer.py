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
    assert "## Insights" in text
    assert "## Recommendations" in text
    assert "**[product_page]** Promote BPA-free badge" in text
    assert "Expected impact: Reduce CS load" in text
    assert sha

    log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=repo, capture_output=True, text=True, check=True,
    ).stdout
    assert "briefs: monthly marketing brief 2026-05" in log


def test_render_includes_external_sentiment_section(tmp_path: Path):
    from intel_engine.briefs.writer import _render
    from intel_engine.schemas.brief import (
        BriefInsight,
        BriefRecommendation,
        BriefTarget,
        MarketingBrief,
    )
    from intel_engine.schemas.sentiment import SentimentComparison, SentimentVerdict

    brief = MarketingBrief(
        month="2026-05",
        headline="May highlights.",
        insights=[
            BriefInsight(theme="vegan", ticket_count=4, persona_segments=[], observation="x")
        ],
        recommendations=[
            BriefRecommendation(
                target=BriefTarget.product_page,
                action="Add PDP block.",
                expected_impact="lower CS load",
                evidence_themes=["vegan"],
            )
        ],
        external_sentiment=[
            SentimentComparison(
                theme_slug="vegan",
                internal_frequency=4,
                external_mentions=27,
                verdict=SentimentVerdict.market_wide,
                reasoning="external dwarfs internal",
                suggested_action="Add a vegan-strap PDP block.",
            )
        ],
    )
    md = _render(brief)
    assert "## External Sentiment" in md
    assert "vegan" in md
    assert "market_wide" in md
    assert "Add a vegan-strap PDP block." in md
