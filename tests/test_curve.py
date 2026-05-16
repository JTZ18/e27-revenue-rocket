"""Test curve generator."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import pandas as pd

from eval.curve import render_curve


def _make_csv(path: Path) -> Path:
    rows = [
        {
            "ticket_index": i,
            "ticket_id": f"TKT-{9000 + i}",
            "received_at": f"2025-11-{15 + i}T10:00:00",
            "pages_read": "",
            "can_answer_fully": i % 2 == 1,
            "themes_detected": "",
            "persona_hints": "",
            "confidence": "high",
            "gap_created": i % 2 == 0,
            "kb_entry_added_slug": f"synth-{i}" if i % 2 == 0 else "",
            "kb_commit_sha": f"sha{i:03d}" if i % 2 == 0 else "",
        }
        for i in range(10)
    ]
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_render_curve_writes_png_and_returns_rate(tmp_path: Path):
    csv_path = _make_csv(tmp_path / "curve_data.csv")
    png_path = tmp_path / "curve.png"

    final_rate = render_curve(
        curve_data_csv=csv_path,
        out_png=png_path,
        title="Test curve",
    )

    assert png_path.exists()
    assert png_path.stat().st_size > 0
    assert 0.0 <= final_rate <= 1.0
    assert final_rate == 0.5
