"""Test ticket seeding script."""
import csv
from pathlib import Path

import pytest

from scripts.seed_tickets import split_tickets


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    src = tmp_path / "tickets.csv"
    src.write_text(
        "ticket_id,date_received,channel,customer_name,subject,message_body,"
        "question_type,buyer_persona,answered_by_kb,requires_escalation\n"
        "TKT-1001,2025-11-15,email,Alice,BPA?,Is this BPA-free?,"
        "materials_safety,health_conscious,yes,no\n"
        "TKT-1002,2025-11-16,chat,Bob,MRI?,Is this MRI-safe?,"
        "knowledge_gap,enthusiast,no,yes\n"
    )
    return src


def test_split_tickets_creates_two_files(sample_csv: Path, tmp_path: Path):
    out_dir = tmp_path / "out"
    split_tickets(sample_csv, out_dir)

    input_csv = out_dir / "tickets_input.csv"
    labels_csv = out_dir / "eval_labels.csv"
    assert input_csv.exists()
    assert labels_csv.exists()


def test_split_tickets_input_has_only_input_columns(sample_csv: Path, tmp_path: Path):
    out_dir = tmp_path / "out"
    split_tickets(sample_csv, out_dir)
    rows = list(csv.DictReader((out_dir / "tickets_input.csv").open()))
    assert len(rows) == 2
    assert set(rows[0].keys()) == {
        "ticket_id", "date_received", "channel", "customer_name", "subject", "message_body",
    }


def test_split_tickets_labels_has_id_plus_label_columns(sample_csv: Path, tmp_path: Path):
    out_dir = tmp_path / "out"
    split_tickets(sample_csv, out_dir)
    rows = list(csv.DictReader((out_dir / "eval_labels.csv").open()))
    assert rows[0]["ticket_id"] == "TKT-1001"
    assert rows[0]["question_type"] == "materials_safety"
    assert rows[0]["buyer_persona"] == "health_conscious"
