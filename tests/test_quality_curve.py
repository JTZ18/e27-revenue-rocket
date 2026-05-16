"""Test quality curve renderer."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import pandas as pd

from eval.quality_curve import render_quality_curve


def test_render_quality_curve(tmp_path: Path):
    csv_path = tmp_path / "quality_scores.csv"
    pd.DataFrame(
        [
            {"ticket_index": 0, "ticket_id": "T0", "overall": 2.0},
            {"ticket_index": 5, "ticket_id": "T5", "overall": 3.0},
            {"ticket_index": 10, "ticket_id": "T10", "overall": 4.5},
        ]
    ).to_csv(csv_path, index=False)

    out_png = tmp_path / "quality_curve.png"
    final = render_quality_curve(scores_csv=csv_path, out_png=out_png)
    assert out_png.exists()
    assert out_png.stat().st_size > 0
    assert 1.0 <= final <= 5.0
