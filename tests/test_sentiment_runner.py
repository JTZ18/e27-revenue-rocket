"""Test the last30days subprocess runner."""
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from intel_engine.schemas.sentiment import SentimentQueryPlan
from intel_engine.sentiment.runner import RunnerError, run_last30days


def _fake_completed(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=["fake"], returncode=returncode, stdout=stdout, stderr=""
    )


def test_runner_parses_emit_json(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("LAST30DAYS_SCRIPT", str(tmp_path / "last30days.py"))
    monkeypatch.setenv("LAST30DAYS_PYTHON", "python3")
    (tmp_path / "last30days.py").write_text("# stub")  # existence-checked only

    fake_emit = {
        "topic": "BPA-free straps",
        "clusters": [
            {
                "title": "Reddit watches discussion",
                "source": "reddit.com/r/watches",
                "items": [
                    {"snippet": "FKM is BPA-free.", "url": "https://reddit.com/x"},
                    {"snippet": "Silicone watch straps are safe.", "url": "https://reddit.com/y"},
                ],
            },
            {
                "title": "Hacker News",
                "source": "news.ycombinator.com",
                "items": [{"snippet": "BPA concerns are overblown.", "url": "https://hn"}],
            },
        ],
    }

    plan = SentimentQueryPlan(
        topic="BPA-free straps",
        search_terms=["BPA-free silicone"],
        subreddits=["watches"],
    )

    with patch(
        "intel_engine.sentiment.runner.subprocess.run",
        return_value=_fake_completed(stdout=json.dumps(fake_emit)),
    ):
        report = run_last30days(theme_slug="bpa_free", plan=plan, ran_at="2026-05-17T10:00:00+08:00")

    assert report.theme_slug == "bpa_free"
    assert report.topic == "BPA-free straps"
    assert report.external_mentions == 3
    assert "reddit.com/r/watches" in report.top_sources
    assert "news.ycombinator.com" in report.top_sources
    assert any("FKM" in s for s in report.snippets)
    assert report.raw_emit == fake_emit


def test_runner_raises_on_nonzero_exit(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("LAST30DAYS_SCRIPT", str(tmp_path / "last30days.py"))
    monkeypatch.setenv("LAST30DAYS_PYTHON", "python3")
    (tmp_path / "last30days.py").write_text("# stub")

    plan = SentimentQueryPlan(topic="xyz", search_terms=["x"])
    proc = subprocess.CompletedProcess(args=["fake"], returncode=2, stdout="", stderr="boom")
    with patch("intel_engine.sentiment.runner.subprocess.run", return_value=proc):
        with pytest.raises(RunnerError, match="exit 2"):
            run_last30days(theme_slug="x", plan=plan, ran_at="2026-05-17T10:00:00+08:00")


def test_runner_requires_script_to_exist(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("LAST30DAYS_SCRIPT", str(tmp_path / "missing.py"))
    monkeypatch.setenv("LAST30DAYS_PYTHON", "python3")
    plan = SentimentQueryPlan(topic="xyz", search_terms=["x"])
    with pytest.raises(RunnerError, match="not found"):
        run_last30days(theme_slug="x", plan=plan, ran_at="2026-05-17T10:00:00+08:00")