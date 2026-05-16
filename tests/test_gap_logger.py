"""Test gap logger."""
from datetime import UTC, datetime
from pathlib import Path

from intel_engine.gap.logger import load_gap, write_gap
from intel_engine.schemas.gap import Gap, GapStatus


def test_write_gap_creates_file(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GAP_LOG_ROOT", str(tmp_path))

    gap = Gap(
        gap_id="gap_2026-05-16_mri",
        source_event_id="evt_xyz",
        customer_question="Are Boldr watches MRI-safe?",
        missing_info=["MRI compatibility unknown"],
        themes_detected=["materials_safety"],
        created_at=datetime(2026, 5, 16, 14, 23, tzinfo=UTC),
    )
    path = write_gap(gap)
    assert path.exists()
    assert path.name == "gap_2026-05-16_mri.md"


def test_load_gap_round_trip(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GAP_LOG_ROOT", str(tmp_path))

    gap = Gap(
        gap_id="gap_test",
        source_event_id="evt_test",
        customer_question="Q?",
        missing_info=["m1", "m2"],
        themes_detected=["t1"],
    )
    write_gap(gap)
    loaded = load_gap("gap_test")
    assert loaded.customer_question == "Q?"
    assert loaded.missing_info == ["m1", "m2"]
    assert loaded.status == GapStatus.open
