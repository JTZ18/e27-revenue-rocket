"""Split provided customer_tickets.csv into agent-visible vs eval-only columns."""
import csv
from pathlib import Path

INPUT_COLUMNS = ["ticket_id", "date_received", "channel", "customer_name", "subject", "message_body"]
LABEL_COLUMNS = [
    "ticket_id",
    "question_type",
    "buyer_persona",
    "answered_by_kb",
    "requires_escalation",
]


def split_tickets(src: Path, out_dir: Path) -> None:
    """Read src CSV, write tickets_input.csv + eval_labels.csv to out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(src.open()))

    with (out_dir / "tickets_input.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=INPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in INPUT_COLUMNS})

    with (out_dir / "eval_labels.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LABEL_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in LABEL_COLUMNS})


if __name__ == "__main__":
    import sys

    src = Path(sys.argv[1] if len(sys.argv) > 1 else "data/01_customer_tickets.csv")
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "eval/data")
    split_tickets(src, out_dir)
    print(f"Wrote {out_dir}/tickets_input.csv and {out_dir}/eval_labels.csv")
