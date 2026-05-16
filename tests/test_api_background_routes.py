"""Test API routes for background loops."""
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
