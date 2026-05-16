"""End-to-end smoke test for the hero gap -> KB loop.

This test bypasses n8n and Slack/Gmail; it directly drives the API endpoints
to prove the loop closes. Each external LLM call is mocked.
"""
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from intel_engine.api import app
from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter
from intel_engine.schemas.traversal import Confidence, TraversalResult


@pytest.fixture
def repo_with_kb(tmp_path: Path, monkeypatch, fixtures_dir):
    """Set up a git repo with a tiny KB."""
    import shutil

    kb_src = fixtures_dir / "sample_kb"
    kb_dst = tmp_path / "kb_repo"
    shutil.copytree(kb_src, kb_dst)

    monkeypatch.setenv("KB_ROOT", str(kb_dst))
    monkeypatch.setenv("GAP_LOG_ROOT", str(tmp_path / "gap-log"))
    (tmp_path / "gap-log").mkdir(exist_ok=True)

    # Clear cached path lookups so env changes are respected
    from intel_engine.settings import gap_log_root, kb_root

    kb_root.cache_clear()
    gap_log_root.cache_clear()

    subprocess.run(
        ["git", "init", "-b", "main"], cwd=tmp_path, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.local"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-m", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    import intel_engine.api as api_mod

    monkeypatch.setattr(api_mod, "DRAFT_STAGE_DIR", tmp_path / "draft-stage")

    return tmp_path


@pytest.mark.asyncio
async def test_full_loop_gap_to_commit(repo_with_kb):
    """Drive the loop: traverse -> gap -> resolve -> draft -> stage -> commit."""
    gap_response = TraversalResult(
        pages_read=["kb/faqs/bpa.md"],
        can_answer_fully=False,
        missing_info=["MRI compatibility not in KB"],
        draft_reply=None,
        themes_detected=["materials_safety"],
        persona_hints=[],
        confidence=Confidence.low,
    )
    drafted_entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="mri-safety",
            title="Are Boldr watches MRI-safe?",
            domain=KBDomain.spec,
            themes=["materials_safety"],
            sources=["gap_test"],
            last_verified=datetime(2026, 5, 16, tzinfo=UTC).date(),
        ),
        body="Yes. Boldr Grade 5 titanium watches are MRI-safe. "
        "Titanium is non-magnetic.",
    )

    event = {
        "event_id": "evt_smoke",
        "source": "google_sheet",
        "customer": {"id": "c1", "name": "Sarah"},
        "body": "Are Boldr watches MRI-safe?",
        "ts": datetime(2026, 5, 16, tzinfo=UTC).isoformat(),
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        with patch(
            "intel_engine.api.traverse", new=AsyncMock(return_value=gap_response)
        ):
            r = await ac.post("/traverse", json=event)
        assert r.status_code == 200
        assert r.json()["can_answer_fully"] is False

        r = await ac.post(
            "/gap",
            json={
                "source_event_id": "evt_smoke",
                "customer_question": "Are Boldr watches MRI-safe?",
                "missing_info": ["MRI compatibility not in KB"],
                "themes_detected": ["materials_safety"],
            },
        )
        assert r.status_code == 200
        gap_id = r.json()["gap_id"]

        r = await ac.post(
            "/gap/resolve",
            json={
                "gap_id": gap_id,
                "resolved_by": "sarah@boldr.sg",
                "resolution_text": (
                    "Titanium is non-magnetic; watches are MRI-safe."
                ),
            },
        )
        assert r.status_code == 200
        assert r.json()["status"] == "resolved"

        with patch(
            "intel_engine.api.draft_kb_entry",
            new=AsyncMock(return_value=drafted_entry),
        ):
            r = await ac.post("/draft-kb-entry", json={"gap_id": gap_id})
        assert r.status_code == 200

        r = await ac.post(
            "/draft/stage",
            json={
                "gap_id": gap_id,
                "entry": drafted_entry.model_dump(mode="json"),
            },
        )
        assert r.status_code == 200

        r = await ac.get(f"/draft/staged/{gap_id}")
        assert r.status_code == 200
        staged = r.json()
        assert staged["frontmatter"]["slug"] == "mri-safety"

        r = await ac.post(
            "/commit-to-kb",
            json={
                "entry": staged,
                "approver": "sarah@boldr.sg",
                "gap_id": gap_id,
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert "sha" in body
        assert body["path"] == "kb/spec/mri-safety.md"

    committed = repo_with_kb / "kb" / "spec" / "mri-safety.md"
    assert committed.exists()
    assert "MRI-safe" in committed.read_text()

    log = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        cwd=repo_with_kb,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "sarah@boldr.sg" in log
