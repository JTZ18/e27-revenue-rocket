"""Load eval labels and agent-visible tickets from the CSV."""
from pathlib import Path

import pandas as pd

from eval.schemas import EvalLabel

AGENT_COLUMNS = [
    "ticket_id",
    "date_received",
    "customer_name",
    "customer_email",
    "order_id",
    "channel",
    "subject",
    "message_body",
]

LABEL_COLUMNS = [
    "ticket_id",
    "question_type",
    "buyer_persona",
    "answered_by_kb",
    "requires_escalation",
]


def _read(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    return df.sort_values("date_received").reset_index(drop=True)


def load_tickets_input(csv_path: Path) -> pd.DataFrame:
    """Return only the columns the agent is allowed to see."""
    df = _read(csv_path)
    return df[AGENT_COLUMNS].copy()


def _yn_to_bool(value: str) -> bool:
    return str(value).strip().lower() in ("yes", "true", "1")


def load_labels(csv_path: Path) -> list[EvalLabel]:
    """Return per-ticket held-out ground-truth labels."""
    df = _read(csv_path)
    out: list[EvalLabel] = []
    for _, row in df.iterrows():
        out.append(
            EvalLabel(
                ticket_id=row["ticket_id"],
                question_type=str(row["question_type"]),
                buyer_persona=str(row["buyer_persona"]),
                answered_by_kb=_yn_to_bool(row["answered_by_kb"]),
                requires_escalation=_yn_to_bool(row["requires_escalation"]),
            )
        )
    return out
