"""Test API routes for background loops."""
import json
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path: Path) -> TestClient:
    # Minimal KB so settings + prompt loads work
    kb = tmp_path / "kb" / "_workflows"
    kb.mkdir(parents=True)
    for name in (
        "persona-discovery-agent",
        "persona-drift-agent",
        "theme-clusterer-agent",
        "brief-writer-agent",
        "conflict-detector-agent",
    ):
        (kb / f"{name}.md").write_text("PROMPT")
    (tmp_path / "kb" / "personas" / "interest").mkdir(parents=True)
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))
    monkeypatch.setenv("LLM_MINIMAX_BASE_URL", "http://mock-minimax")
    monkeypatch.setenv("LLM_MINIMAX_API_KEY", "mock-key")
    monkeypatch.setenv("LLM_MINIMAX_MODEL", "mock-model")

    from intel_engine import settings
    settings.kb_root.cache_clear()
    settings.llm_config.cache_clear()

    from intel_engine.api import app
    return TestClient(app)


def test_themes_cluster_endpoint(client: TestClient):
    mock = {
        "themes": [
            {
                "slug": "bpa",
                "label": "BPA",
                "frequency": 2,
                "example_ticket_ids": ["T1", "T2"],
                "summary": "BPA questions.",
            }
        ]
    }
    with patch(
        "intel_engine.agents.theme_clusterer.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ):
        r = client.post(
            "/themes/cluster",
            json={
                "tickets": [
                    {"ticket_id": "T1", "message_body": "BPA?"},
                    {"ticket_id": "T2", "message_body": "BPA?"},
                ],
                "week_start": "2026-05-11",
                "week_end": "2026-05-17",
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["ticket_count"] == 2
    assert body["themes"][0]["slug"] == "bpa"


def test_personas_discover_endpoint(client: TestClient):
    mock = {
        "proposals": [
            {
                "axis": "interest",
                "slug": "health_conscious",
                "label": "Health-conscious",
                "description": "d",
                "signals": ["BPA"],
                "example_ticket_ids": ["T1", "T2"],
                "rationale": "Two tickets.",
            }
        ]
    }
    with patch(
        "intel_engine.agents.persona_discovery.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ):
        r = client.post(
            "/personas/discover",
            json={
                "tickets": [
                    {"ticket_id": "T1", "message_body": "BPA?"},
                    {"ticket_id": "T2", "message_body": "BPA?"},
                ]
            },
        )
    assert r.status_code == 200
    assert len(r.json()["proposals"]) == 1


def test_personas_drift_endpoint(client: TestClient):
    mock = {
        "proposals": [],
        "stale_candidates": [],
    }
    with patch(
        "intel_engine.agents.persona_drift.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ):
        r = client.post(
            "/personas/drift",
            json={
                "tickets": [
                    {"ticket_id": "T1", "message_body": "BPA?"},
                    {"ticket_id": "T2", "message_body": "BPA?"},
                ],
                "window_start": "2026-05-11",
                "window_end": "2026-05-17",
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert "proposals" in body
    assert "stale_candidates" in body


def test_briefs_monthly_endpoint(client: TestClient):
    mock = {
        "headline": "May Brief",
        "insights": [
            {
                "theme": "BPA",
                "ticket_count": 2,
                "persona_segments": ["health_conscious"],
                "observation": "People ask about BPA.",
            }
        ],
        "recommendations": [
            {
                "target": "kb",
                "action": "Add BPA FAQ.",
                "expected_impact": "Fewer tickets.",
                "evidence_themes": ["bpa"],
            }
        ],
    }
    with patch(
        "intel_engine.agents.brief_writer.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ):
        r = client.post(
            "/briefs/monthly",
            json={
                "month": "2026-05",
                "theme_reports": [
                    {
                        "week_start": "2026-05-11",
                        "week_end": "2026-05-17",
                        "ticket_count": 2,
                        "themes": [
                            {
                                "slug": "bpa",
                                "label": "BPA",
                                "frequency": 2,
                                "example_ticket_ids": ["T1", "T2"],
                                "summary": "BPA questions.",
                            }
                        ],
                    }
                ],
                "kb_summary": "KB looks good.",
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["month"] == "2026-05"


def test_conflicts_digest_endpoint(client: TestClient):
    mock = {"conflicts": []}
    with patch(
        "intel_engine.agents.conflict_detector.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ):
        r = client.post(
            "/conflicts/digest",
            json={
                "kb_entries": [
                    {"path": "kb/x.md", "domain": "faq", "title": "x", "excerpt": ""}
                ],
                "week_end": "2026-05-17",
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 0
    assert body["slack_blocks"]


def test_themes_persist_endpoint(client: TestClient, tmp_path: Path, monkeypatch):
    import subprocess

    repo = tmp_path
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@x"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)
    (repo / "seed.txt").write_text("seed")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "seed"],
        cwd=repo,
        check=True,
    )

    r = client.post(
        "/themes/persist",
        json={
            "report": {
                "week_start": "2026-05-11",
                "week_end": "2026-05-17",
                "ticket_count": 1,
                "themes": [
                    {
                        "slug": "x",
                        "label": "X",
                        "frequency": 2,
                        "example_ticket_ids": ["T1", "T2"],
                        "summary": "s",
                    }
                ],
            }
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["week_end"] == "2026-05-17"
    assert "committed_sha" in body
    assert (repo / "kb" / "themes" / "2026-05-17.md").exists()


def test_personas_persist_endpoint(client: TestClient, tmp_path: Path):
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@x"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True)
    (tmp_path / "seed.txt").write_text("seed")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "seed"],
        cwd=tmp_path,
        check=True,
    )

    r = client.post(
        "/personas/persist",
        json={
            "persona": {
                "axis": "interest",
                "slug": "sustainability_buyer",
                "label": "Sustainability buyer",
                "description": "d",
                "signals": ["vegan"],
            },
            "approver": "cs-alice",
        },
    )
    assert r.status_code == 200
    assert r.json()["slug"] == "sustainability_buyer"
    assert "committed_sha" in r.json()
    assert (tmp_path / "kb" / "personas" / "interest" / "sustainability_buyer.md").exists()


def test_briefs_persist_endpoint(client: TestClient, tmp_path: Path):
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@x"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True)
    (tmp_path / "seed.txt").write_text("seed")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "seed"],
        cwd=tmp_path,
        check=True,
    )

    r = client.post(
        "/briefs/persist",
        json={
            "brief": {
                "month": "2026-05",
                "headline": "May test",
                "insights": [],
                "recommendations": [],
            }
        },
    )
    assert r.status_code == 200
    assert r.json()["month"] == "2026-05"
    assert "committed_sha" in r.json()
    assert (tmp_path / "briefs" / "2026-05-marketing-brief.md").exists()


def test_kb_summary_endpoint(client: TestClient, tmp_path: Path, monkeypatch):
    kb = tmp_path / "kb"
    (kb / "faqs").mkdir(parents=True, exist_ok=True)
    (kb / "faqs" / "bpa.md").write_text(
        "---\nslug: bpa\ntitle: BPA?\ndomain: faq\nthemes: []\nsources: []\n"
        "last_verified: 2026-05-17\nstatus: active\n---\n\nYes.\n"
    )
    monkeypatch.setenv("KB_ROOT", str(kb))
    from intel_engine import settings
    settings.kb_root.cache_clear()

    r = client.get("/kb/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 1
    assert any(e["title"] == "BPA?" for e in body["entries"])


def _init_repo(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@x"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True, capture_output=True)
    (repo / "seed.txt").write_text("seed")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "seed"],
        cwd=repo, check=True, capture_output=True,
    )


@pytest.fixture
def sentiment_client(monkeypatch, tmp_path: Path) -> tuple[TestClient, Path]:
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
    _init_repo(tmp_path)
    from intel_engine.api import app
    return TestClient(app), tmp_path


def test_sentiment_plan_endpoint(sentiment_client):
    c, _ = sentiment_client
    mock = {
        "topic": "BPA-free titanium watch straps",
        "search_terms": ["BPA-free silicone"],
        "subreddits": ["watches"],
        "related_handles": [],
        "notes": "",
    }
    with patch(
        "intel_engine.agents.sentiment_planner.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ):
        r = c.post(
            "/sentiment/plan",
            json={
                "theme": {
                    "slug": "bpa_free",
                    "label": "BPA-free",
                    "frequency": 3,
                    "example_ticket_ids": ["T1", "T2"],
                    "summary": "BPA questions.",
                },
                "kb_excerpt": "",
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["topic"].startswith("BPA-free")
    assert body["search_terms"] == ["BPA-free silicone"]


def test_sentiment_compare_endpoint(sentiment_client):
    c, _ = sentiment_client
    mock = {
        "verdict": "market_wide",
        "reasoning": "external > internal",
        "suggested_action": "Add PDP note.",
    }
    with patch(
        "intel_engine.agents.sentiment_comparator.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ):
        r = c.post(
            "/sentiment/compare",
            json={
                "theme": {
                    "slug": "vegan",
                    "label": "Vegan",
                    "frequency": 8,
                    "example_ticket_ids": ["T1", "T2"],
                    "summary": "x",
                },
                "external": {
                    "theme_slug": "vegan",
                    "ran_at": "2026-05-17T10:00:00+08:00",
                    "topic": "Vegan watch straps",
                    "external_mentions": 42,
                    "top_sources": ["reddit"],
                    "snippets": ["x"],
                    "raw_emit": {},
                },
            },
        )
    assert r.status_code == 200
    assert r.json()["verdict"] == "market_wide"


def test_sentiment_persist_and_list(sentiment_client):
    c, repo = sentiment_client
    persist_body = {
        "report": {
            "theme_slug": "vegan",
            "ran_at": "2026-05-17T10:00:00+08:00",
            "topic": "Vegan watch straps",
            "external_mentions": 42,
            "top_sources": ["reddit"],
            "snippets": ["x"],
            "raw_emit": {},
        },
        "comparison": {
            "theme_slug": "vegan",
            "internal_frequency": 8,
            "external_mentions": 42,
            "verdict": "market_wide",
            "reasoning": "external dwarfs internal",
            "suggested_action": "Add PDP note.",
        },
    }
    r = c.post("/sentiment/persist", json=persist_body)
    assert r.status_code == 200
    assert r.json()["month"] == "2026-05"
    assert (repo / "external-intel" / "2026-05" / "vegan.json").exists()

    r2 = c.get("/sentiment/list")
    assert r2.status_code == 200
    items = r2.json()["reports"]
    assert any(i["theme_slug"] == "vegan" for i in items)
    assert any(i["verdict"] == "market_wide" for i in items)


def test_sentiment_run_invokes_runner(sentiment_client):
    c, _ = sentiment_client
    from intel_engine.schemas.sentiment import ExternalSentimentReport

    fake = ExternalSentimentReport(
        theme_slug="vegan",
        ran_at="2026-05-17T10:00:00+08:00",
        topic="Vegan watch straps",
        external_mentions=42,
        top_sources=["reddit"],
        snippets=["x"],
        raw_emit={"clusters": []},
    )
    with patch("intel_engine.api.run_last30days", return_value=fake):
        r = c.post(
            "/sentiment/run",
            json={
                "theme_slug": "vegan",
                "ran_at": "2026-05-17T10:00:00+08:00",
                "plan": {
                    "topic": "Vegan watch straps",
                    "search_terms": ["vegan"],
                    "subreddits": [],
                    "related_handles": [],
                    "notes": "",
                },
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["external_mentions"] == 42
    assert body["theme_slug"] == "vegan"
