"""End-to-end smoke test for the four background loops (mocked LLM)."""
import subprocess
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client_and_repo(monkeypatch, tmp_path: Path) -> tuple[TestClient, Path]:
    kb = tmp_path / "kb"
    (kb / "_workflows").mkdir(parents=True)
    (kb / "personas" / "interest").mkdir(parents=True)
    for name in (
        "persona-discovery-agent",
        "persona-drift-agent",
        "theme-clusterer-agent",
        "brief-writer-agent",
        "conflict-detector-agent",
    ):
        (kb / "_workflows" / f"{name}.md").write_text("PROMPT")
    (kb / "faqs").mkdir(parents=True)
    (kb / "faqs" / "x.md").write_text(
        f"---\nslug: x\ntitle: X\ndomain: faq\nthemes: []\nsources: []\n"
        f"last_verified: {date.today().isoformat()}\nstatus: active\n---\n\nBody.\n"
    )
    monkeypatch.setenv("KB_ROOT", str(kb))
    monkeypatch.setenv("LLM_MINIMAX_BASE_URL", "http://mock-minimax")
    monkeypatch.setenv("LLM_MINIMAX_API_KEY", "mock-key")
    monkeypatch.setenv("LLM_MINIMAX_MODEL", "mock-model")

    from intel_engine import settings
    settings.kb_root.cache_clear()
    settings.llm_config.cache_clear()

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@x"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "seed"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    from intel_engine.api import app
    return TestClient(app), tmp_path


@pytest.mark.e2e
def test_themes_round_trip(client_and_repo):
    c, repo = client_and_repo
    mock = {
        "themes": [
            {
                "slug": "bpa",
                "label": "BPA",
                "frequency": 2,
                "example_ticket_ids": ["T1", "T2"],
                "summary": "x",
            }
        ]
    }
    with patch(
        "intel_engine.agents.theme_clusterer.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ):
        r1 = c.post(
            "/themes/cluster",
            json={
                "tickets": [{"ticket_id": "T1", "message_body": "a"},
                            {"ticket_id": "T2", "message_body": "b"}],
                "week_start": "2026-05-11",
                "week_end": "2026-05-17",
            },
        )
        assert r1.status_code == 200
        r2 = c.post("/themes/persist", json={"report": r1.json()})
        assert r2.status_code == 200
        path = repo / "kb" / "themes" / "2026-05-17.md"
        assert path.exists()
        assert "BPA" in path.read_text()


@pytest.mark.e2e
def test_personas_round_trip(client_and_repo):
    c, repo = client_and_repo
    mock = {
        "proposals": [
            {
                "axis": "interest",
                "slug": "sustainability_buyer",
                "label": "Sustainability buyer",
                "description": "d",
                "signals": ["vegan"],
                "example_ticket_ids": ["T1", "T2"],
                "rationale": "r",
            }
        ]
    }
    with patch(
        "intel_engine.agents.persona_discovery.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ):
        r = c.post(
            "/personas/discover",
            json={"tickets": [{"ticket_id": "T1", "message_body": "vegan?"},
                              {"ticket_id": "T2", "message_body": "vegan?"}]},
        )
        proposal = r.json()["proposals"][0]

    r2 = c.post("/personas/persist", json={"persona": {**proposal, "status": "active"}})
    assert r2.status_code == 200
    path = repo / "kb" / "personas" / "interest" / "sustainability_buyer.md"
    assert path.exists()
    assert "Sustainability buyer" in path.read_text()


@pytest.mark.e2e
def test_conflicts_round_trip(client_and_repo):
    c, _ = client_and_repo
    mock = {"conflicts": []}
    with patch(
        "intel_engine.agents.conflict_detector.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ):
        summary = c.get("/kb/summary").json()
        r = c.post(
            "/conflicts/digest",
            json={"kb_entries": summary["entries"], "week_end": "2026-05-17"},
        )
    assert r.status_code == 200
    assert r.json()["count"] == 0


@pytest.mark.e2e
def test_brief_round_trip(client_and_repo):
    c, repo = client_and_repo
    mock = {
        "headline": "h",
        "insights": [],
        "recommendations": [],
    }
    with patch(
        "intel_engine.agents.brief_writer.LLMClient.complete_json",
        new=AsyncMock(return_value=mock),
    ):
        r1 = c.post(
            "/briefs/monthly",
            json={"month": "2026-05", "theme_reports": [], "kb_summary": ""},
        )
        assert r1.status_code == 200
        r2 = c.post("/briefs/persist", json={"brief": r1.json()})
        assert r2.status_code == 200
        path = repo / "briefs" / "2026-05-marketing-brief.md"
        assert path.exists()
        assert "h" in path.read_text()
