"""Test dashboard-supporting list endpoints."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def dash_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[TestClient, Path]:
    kb = tmp_path / "kb"
    (kb / "personas" / "interest").mkdir(parents=True)
    (kb / "personas" / "interest" / "sustainability_buyer.md").write_text(
        "---\n"
        "axis: interest\n"
        "slug: sustainability_buyer\n"
        "label: Sustainability buyer\n"
        "description: cares about vegan/carbon-neutral.\n"
        "signals:\n"
        "  - vegan\n"
        "status: active\n"
        "---\n\nBody.\n"
    )
    (tmp_path / "gap-log").mkdir(exist_ok=True)
    (tmp_path / "briefs").mkdir(exist_ok=True)
    (tmp_path / "briefs" / "2026-05-marketing-brief.md").write_text("# Brief 2026-05\n\nbody")
    monkeypatch.setenv("KB_ROOT", str(kb))
    monkeypatch.setenv("GAP_LOG_ROOT", str(tmp_path / "gap-log"))
    from intel_engine import settings
    settings.kb_root.cache_clear()
    settings.gap_log_root.cache_clear()

    # Write one gap with the production logger to ensure the schema matches.
    from intel_engine.gap.logger import write_gap
    from intel_engine.schemas.gap import Gap
    write_gap(Gap(
        gap_id="gap_2026-05-17_abc",
        source_event_id="evt_x",
        customer_question="Are straps BPA-free?",
        missing_info=["BPA"],
        themes_detected=["bpa_free"],
        persona_hints=["health_conscious"],
    ))

    from intel_engine.api import app
    return TestClient(app), tmp_path


def test_gaps_list_returns_open_gap(dash_client):
    c, _ = dash_client
    r = c.get("/gaps/list")
    assert r.status_code == 200
    gaps = r.json()["gaps"]
    assert any(g["gap_id"] == "gap_2026-05-17_abc" for g in gaps)
    target = next(g for g in gaps if g["gap_id"] == "gap_2026-05-17_abc")
    assert target["status"] == "open"
    assert target["customer_question"].startswith("Are straps")


def test_personas_list_returns_active(dash_client):
    c, _ = dash_client
    r = c.get("/personas/list")
    assert r.status_code == 200
    items = r.json()["personas"]
    assert any(p["slug"] == "sustainability_buyer" for p in items)


def test_briefs_list_surfaces_files(dash_client):
    c, _ = dash_client
    r = c.get("/briefs/list")
    assert r.status_code == 200
    items = r.json()["briefs"]
    assert any(b["month"] == "2026-05" for b in items)
    assert "# Brief 2026-05" in items[0]["markdown"]
