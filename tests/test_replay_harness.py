"""Test replay harness."""
import subprocess
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from eval.replay_harness import run_replay
from intel_engine import settings


@pytest.fixture
def sandbox_repo(tmp_path: Path, fixtures_dir: Path, monkeypatch) -> Path:
    """Create a throwaway git repo with a minimal seeded KB."""
    repo = tmp_path / "repo"
    repo.mkdir()
    kb = repo / "kb"
    (kb / "rate-cards").mkdir(parents=True)
    (kb / "products").mkdir()
    (kb / "faqs").mkdir()
    (kb / "_workflows").mkdir(parents=True)
    (kb / "_workflows" / "traversal-agent.md").write_text(
        "# Traversal\nOutput JSON.\n"
    )
    (kb / "_schema.md").write_text("# Brand voice\nOpen with Yes/No.")
    (kb / "rate-cards" / "engraving.md").write_text(
        "---\nslug: engraving\ntitle: Engraving\ndomain: pricing\n"
        "themes: [pricing]\nsources: [seed]\nlast_verified: 2026-05-17\n"
        "status: active\n---\n\nSGD 30.\n"
    )

    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@x"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "seed"],
        cwd=repo,
        check=True,
    )

    monkeypatch.setenv("KB_ROOT", str(kb))
    monkeypatch.setenv("LLM_MINIMAX_BASE_URL", "http://mock")
    monkeypatch.setenv("LLM_MINIMAX_API_KEY", "mock")
    monkeypatch.setenv("LLM_MINIMAX_MODEL", "mock")
    settings.kb_root.cache_clear()
    settings.gap_log_root.cache_clear()
    return repo


def _mock_traversal_responses():
    """Return a list of canned LLM responses — one per ticket."""
    return [
        # TKT-9001: BPA — gap (no kb/faqs/ entry yet)
        {
            "pages_read": ["kb/rate-cards/engraving.md"],
            "can_answer_fully": False,
            "missing_info": ["BPA safety not in KB"],
            "draft_reply": None,
            "themes_detected": ["materials_safety"],
            "persona_hints": ["health_conscious"],
            "confidence": "low",
        },
        # TKT-9002: dye — gap again
        {
            "pages_read": ["kb/rate-cards/engraving.md"],
            "can_answer_fully": False,
            "missing_info": ["Dye safety not in KB"],
            "draft_reply": None,
            "themes_detected": ["materials_safety"],
            "persona_hints": ["health_conscious"],
            "confidence": "low",
        },
        # TKT-9003: servicing — answerable from rate card
        {
            "pages_read": ["kb/rate-cards/engraving.md"],
            "can_answer_fully": True,
            "missing_info": [],
            "draft_reply": "Yes. Older models are serviced — SGD 30.",
            "themes_detected": ["servicing"],
            "persona_hints": ["owner_aftercare"],
            "confidence": "high",
        },
        # TKT-9004: price match — gap
        {
            "pages_read": [],
            "can_answer_fully": False,
            "missing_info": ["No price match policy"],
            "draft_reply": None,
            "themes_detected": ["pricing"],
            "persona_hints": ["prospect"],
            "confidence": "low",
        },
        # TKT-9005: MRI — gap
        {
            "pages_read": [],
            "can_answer_fully": False,
            "missing_info": ["MRI not in KB"],
            "draft_reply": None,
            "themes_detected": ["movement_safety"],
            "persona_hints": ["niche_buyer"],
            "confidence": "low",
        },
    ]


@pytest.mark.asyncio
async def test_replay_produces_run_summary_and_csv(
    sandbox_repo: Path, fixtures_dir: Path, tmp_path: Path
):
    out_csv = tmp_path / "curve_data.csv"
    responses = _mock_traversal_responses()

    with patch(
        "intel_engine.agents.traversal.LLMClient.complete_json",
        new=AsyncMock(side_effect=responses),
    ):
        run = await run_replay(
            tickets_csv=fixtures_dir / "eval" / "tickets_small.csv",
            repo_root=sandbox_repo,
            out_csv=out_csv,
            today=date(2026, 5, 17),
        )

    assert run.ticket_count == 5
    assert run.answered_count == 1     # only TKT-9003
    assert run.gap_count == 4
    assert run.answer_rate == pytest.approx(0.2)
    assert out_csv.exists()

    # Four synthetic KB entries should have been committed
    log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=sandbox_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    synth_commits = [line for line in log.splitlines() if "kb: add synth-" in line]
    assert len(synth_commits) == 4
