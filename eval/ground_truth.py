"""Compare model predictions against held-out labels."""
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from eval.schemas import EvalLabel


def _first(value: object) -> str:
    """Take the first '|'-separated token from a multi-value cell."""
    if value is None:
        return ""
    text = str(value)
    if not text or text == "nan":
        return ""
    return text.split("|", 1)[0].strip()


def build_report(
    *,
    predictions_csv: Path,
    labels: list[EvalLabel],
) -> dict[str, Any]:
    """Build the ground-truth accuracy report dict."""
    preds = pd.read_csv(predictions_csv)
    labels_by_id = {label.ticket_id: label for label in labels}

    rows = []
    for _, row in preds.iterrows():
        ticket_id = str(row["ticket_id"])
        if ticket_id not in labels_by_id:
            continue
        label = labels_by_id[ticket_id]
        rows.append(
            {
                "ticket_id": ticket_id,
                "pred_theme": _first(row.get("themes_detected")),
                "true_theme": label.question_type,
                "pred_persona": _first(row.get("persona_hints")),
                "true_persona": label.buyer_persona,
                "pred_answered": bool(row["can_answer_fully"]),
                "true_answered": label.answered_by_kb,
                "true_escalation": label.requires_escalation,
            }
        )

    df = pd.DataFrame(rows)

    theme_acc = accuracy_score(df["true_theme"], df["pred_theme"])
    persona_acc = accuracy_score(df["true_persona"], df["pred_persona"])

    # Gap detection: positive class = "is a gap" = NOT answered_by_kb
    y_true_gap = (~df["true_answered"]).astype(int)
    y_pred_gap = (~df["pred_answered"]).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true_gap, y_pred_gap, average="binary", zero_division=0
    )

    # Escalation: a ticket should escalate if labelled requires_escalation=True.
    # As a simple proxy the model "escalates" when it cannot answer.
    y_true_esc = df["true_escalation"].astype(int)
    y_pred_esc = (~df["pred_answered"]).astype(int)
    esc_acc = accuracy_score(y_true_esc, y_pred_esc)

    return {
        "ticket_count": len(df),
        "theme_accuracy": float(theme_acc),
        "persona_accuracy": float(persona_acc),
        "gap_detection": {
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
        },
        "escalation_accuracy": float(esc_acc),
    }


def render_report_markdown(report: dict[str, Any], out_md: Path) -> None:
    gd = report["gap_detection"]
    md = (
        "# Ground-Truth Accuracy Report\n\n"
        f"Tickets evaluated: **{report['ticket_count']}**\n\n"
        "## Per-class metrics\n\n"
        "| Metric | Value |\n"
        "|---|---|\n"
        f"| Theme classification accuracy | {report['theme_accuracy']:.2%} |\n"
        f"| Persona classification accuracy | {report['persona_accuracy']:.2%} |\n"
        f"| Gap detection — precision | {gd['precision']:.2%} |\n"
        f"| Gap detection — recall | {gd['recall']:.2%} |\n"
        f"| Gap detection — F1 | {gd['f1']:.2%} |\n"
        f"| Escalation accuracy | {report['escalation_accuracy']:.2%} |\n"
    )
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md)
