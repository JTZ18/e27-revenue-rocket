"""Test ground-truth accuracy report."""
from pathlib import Path

import pandas as pd

from eval.ground_truth import build_report
from eval.schemas import EvalLabel


def _predictions(tmp_path: Path) -> Path:
    rows = [
        {
            "ticket_id": "T1",
            "can_answer_fully": True,
            "themes_detected": "materials_safety",
            "persona_hints": "health_conscious",
        },
        {
            "ticket_id": "T2",
            "can_answer_fully": False,
            "themes_detected": "movement_safety",
            "persona_hints": "niche_buyer",
        },
        {
            "ticket_id": "T3",
            "can_answer_fully": True,
            "themes_detected": "pricing",
            "persona_hints": "prospect",
        },
    ]
    path = tmp_path / "preds.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_build_report_aggregates_metrics(tmp_path: Path):
    preds = _predictions(tmp_path)
    labels = [
        EvalLabel(
            ticket_id="T1",
            question_type="materials_safety",
            buyer_persona="health_conscious",
            answered_by_kb=True,
            requires_escalation=False,
        ),
        EvalLabel(
            ticket_id="T2",
            question_type="movement_safety",
            buyer_persona="niche_buyer",
            answered_by_kb=False,
            requires_escalation=True,
        ),
        EvalLabel(
            ticket_id="T3",
            question_type="pricing",
            buyer_persona="prospect",
            answered_by_kb=True,
            requires_escalation=False,
        ),
    ]

    report = build_report(predictions_csv=preds, labels=labels)

    assert report["theme_accuracy"] == 1.0
    assert report["persona_accuracy"] == 1.0
    # answered_by_kb prediction matches can_answer_fully exactly here
    assert report["gap_detection"]["precision"] == 1.0
    assert report["gap_detection"]["recall"] == 1.0
    assert report["ticket_count"] == 3
