"""Test eval-labels loader."""
from pathlib import Path

import pytest

from eval.labels import AGENT_COLUMNS, LABEL_COLUMNS, load_labels, load_tickets_input


@pytest.fixture
def csv_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "eval" / "tickets_small.csv"


def test_agent_columns_exclude_held_out(csv_path):
    df = load_tickets_input(csv_path)
    assert set(df.columns) == set(AGENT_COLUMNS)
    for held in LABEL_COLUMNS:
        if held == "ticket_id":
            continue
        assert held not in df.columns
    assert len(df) == 5


def test_load_labels_returns_typed_models(csv_path):
    labels = load_labels(csv_path)
    assert len(labels) == 5
    by_id = {label.ticket_id: label for label in labels}
    assert by_id["TKT-9001"].answered_by_kb is True
    assert by_id["TKT-9001"].requires_escalation is False
    assert by_id["TKT-9005"].answered_by_kb is False
    assert by_id["TKT-9005"].requires_escalation is True
    assert by_id["TKT-9005"].buyer_persona == "niche_buyer"


def test_tickets_input_sorted_chronologically(csv_path):
    df = load_tickets_input(csv_path)
    dates = list(df["date_received"])
    assert dates == sorted(dates)
