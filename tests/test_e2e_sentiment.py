"""End-to-end smoke test for the external sentiment loop (mocked LLM + CLI)."""
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def sentiment_e2e(monkeypatch, tmp_path: Path) -> tuple[TestClient, Path]:
    kb = tmp_path / "kb"
    (kb / "_workflows").mkdir(parents=True)
    (kb / "_workflows" / "sentiment-planner-agent.md").write_text("P")
    (kb / "_workflows" / "sentiment-comparator-agent.md").write_text("P")
    monkeypatch.setenv("KB_ROOT", str(kb))
    monkeypatch.setenv("LLM_MINIMAX_BASE_URL", "http://m")
    monkeypatch.setenv("LLM_MINIMAX_API_KEY", "k")
    monkeypatch.setenv("LLM_MINIMAX_MODEL", "m")
    monkeypatch.setenv("LLM_OPENROUTER_BASE_URL", "http://o")
    monkeypatch.setenv("LLM_OPENROUTER_API_KEY", "k")
    monkeypatch.setenv("LLM_OPENROUTER_MODEL", "o")
    from intel_engine import settings
    settings.kb_root.cache_clear()
    settings.llm_config.cache_clear()

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@x"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "seed.txt").write_text("seed")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "seed"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    from intel_engine.api import app
    return TestClient(app), tmp_path


@pytest.mark.e2e
def test_sentiment_round_trip(sentiment_e2e):
    c, repo = sentiment_e2e

    theme = {
        "slug": "bpa_free",
        "label": "BPA-free",
        "frequency": 4,
        "example_ticket_ids": ["T1", "T2"],
        "summary": "BPA-free strap questions.",
    }

    plan_mock = {
        "topic": "BPA-free titanium watch straps",
        "search_terms": ["BPA-free silicone"],
        "subreddits": ["watches"],
        "related_handles": [],
        "notes": "",
    }
    compare_mock = {
        "verdict": "market_wide",
        "reasoning": "external dwarfs internal",
        "suggested_action": "Add PDP note.",
    }

    from intel_engine.schemas.sentiment import ExternalSentimentReport

    fake_external = ExternalSentimentReport(
        theme_slug="bpa_free",
        ran_at="2026-05-17T10:00:00+08:00",
        topic="BPA-free titanium watch straps",
        external_mentions=14,
        top_sources=["reddit"],
        snippets=["x"],
        raw_emit={"clusters": []},
    )

    with patch(
        "intel_engine.agents.sentiment_planner.LLMClient.complete_json",
        new=AsyncMock(return_value=plan_mock),
    ), patch(
        "intel_engine.api.run_last30days", return_value=fake_external,
    ), patch(
        "intel_engine.agents.sentiment_comparator.LLMClient.complete_json",
        new=AsyncMock(return_value=compare_mock),
    ):
        r_plan = c.post("/sentiment/plan", json={"theme": theme, "kb_excerpt": ""})
        assert r_plan.status_code == 200

        r_run = c.post(
            "/sentiment/run",
            json={
                "theme_slug": "bpa_free",
                "ran_at": "2026-05-17T10:00:00+08:00",
                "plan": r_plan.json(),
            },
        )
        assert r_run.status_code == 200

        r_cmp = c.post(
            "/sentiment/compare",
            json={"theme": theme, "external": r_run.json()},
        )
        assert r_cmp.status_code == 200

        r_persist = c.post(
            "/sentiment/persist",
            json={"report": r_run.json(), "comparison": r_cmp.json()},
        )
        assert r_persist.status_code == 200

    assert (repo / "external-intel" / "2026-05" / "bpa_free.json").exists()

    r_list = c.get("/sentiment/list")
    assert r_list.status_code == 200
    reports = r_list.json()["reports"]
    assert any(r["theme_slug"] == "bpa_free" and r["verdict"] == "market_wide" for r in reports)
