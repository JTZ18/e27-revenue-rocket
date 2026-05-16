"""Human vs LLM-judge agreement metrics."""
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import cohen_kappa_score

DIMENSIONS = ["grounded", "brand_voice", "completeness", "no_hallucination", "tone_fit"]


def compute_agreement(*, human: pd.DataFrame, llm: pd.DataFrame) -> dict[str, Any]:
    """Mean absolute error per dimension + overall quadratic-weighted kappa."""
    merged = human.merge(llm, on="ticket_id", suffixes=("_human", "_llm"))
    if merged.empty:
        return {"mae": {d: None for d in DIMENSIONS}, "kappa": None, "n": 0}

    mae = {}
    all_human: list[int] = []
    all_llm: list[int] = []
    for dim in DIMENSIONS:
        h = merged[f"{dim}_human"].astype(int)
        m = merged[f"{dim}_llm"].astype(int)
        mae[dim] = float((h - m).abs().mean())
        all_human.extend(h.tolist())
        all_llm.extend(m.tolist())

    kappa = cohen_kappa_score(
        all_human, all_llm, weights="quadratic", labels=[1, 2, 3, 4, 5]
    )

    return {"mae": mae, "kappa": float(kappa), "n": int(len(merged))}


def render_calibration_markdown(
    agreement: dict[str, Any], out_md: Path
) -> None:
    lines = [
        "# LLM-Judge Calibration",
        "",
        f"Hand-rated drafts re-scored by LLM judge: **{agreement['n']}**.",
        "",
        f"Quadratic-weighted Cohen's kappa (all dims): **{agreement['kappa']:.3f}**",
        "",
        "| Dimension | Mean absolute error |",
        "|---|---|",
    ]
    for dim, value in agreement["mae"].items():
        lines.append(f"| {dim} | {value:.2f} |")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n")
