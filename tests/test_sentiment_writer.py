"""Test sentiment writer."""
import json
import subprocess
from pathlib import Path

from intel_engine.schemas.sentiment import (
    ExternalSentimentReport,
    SentimentComparison,
    SentimentVerdict,
)
from intel_engine.sentiment.writer import write_and_commit_sentiment


def _init_repo(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@x"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True, capture_output=True)
    (repo / "seed.txt").write_text("seed")
    subprocess.run(["git", "add", "seed.txt"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "seed"],
        cwd=repo, check=True, capture_output=True,
    )


def test_writes_to_external_intel_subdir(tmp_path: Path):
    _init_repo(tmp_path)
    report = ExternalSentimentReport(
        theme_slug="bpa_free",
        ran_at="2026-05-17T10:00:00+08:00",
        topic="BPA-free titanium straps",
        external_mentions=14,
        top_sources=["reddit"],
        snippets=["FKM is BPA-free."],
        raw_emit={"clusters": []},
    )
    cmp = SentimentComparison(
        theme_slug="bpa_free",
        internal_frequency=2,
        external_mentions=14,
        verdict=SentimentVerdict.market_wide,
        reasoning="external dwarfs internal",
        suggested_action="Add product-page note.",
    )

    sha = write_and_commit_sentiment(report=report, comparison=cmp, repo_root=tmp_path)

    out_path = tmp_path / "external-intel" / "2026-05" / "bpa_free.json"
    assert out_path.exists()
    payload = json.loads(out_path.read_text())
    assert payload["report"]["theme_slug"] == "bpa_free"
    assert payload["comparison"]["verdict"] == "market_wide"
    assert sha  # non-empty short SHA


def test_overwrites_same_theme_same_month(tmp_path: Path):
    _init_repo(tmp_path)
    report = ExternalSentimentReport(
        theme_slug="vegan",
        ran_at="2026-05-17T10:00:00+08:00",
        topic="vegan",
        external_mentions=1,
        top_sources=[],
        snippets=[],
        raw_emit={},
    )
    cmp = SentimentComparison(
        theme_slug="vegan",
        internal_frequency=1,
        external_mentions=1,
        verdict=SentimentVerdict.aligned,
        reasoning="aligned signal",
        suggested_action="watch the metric",
    )
    write_and_commit_sentiment(report=report, comparison=cmp, repo_root=tmp_path)

    # second run same month, higher external mentions
    report2 = report.model_copy(update={"external_mentions": 9})
    cmp2 = cmp.model_copy(update={"external_mentions": 9, "verdict": SentimentVerdict.market_wide})
    write_and_commit_sentiment(report=report2, comparison=cmp2, repo_root=tmp_path)

    path = tmp_path / "external-intel" / "2026-05" / "vegan.json"
    payload = json.loads(path.read_text())
    assert payload["report"]["external_mentions"] == 9
    assert payload["comparison"]["verdict"] == "market_wide"
