"""Eval CLI.

Usage:
    uv run python -m eval replay          # full longitudinal replay
    uv run python -m eval curve           # render curve.png from existing data
    uv run python -m eval ground-truth    # accuracy vs held-out labels
    uv run python -m eval judge           # LLM-judge 50 drafts
    uv run python -m eval quality-curve   # render quality_curve.png
    uv run python -m eval calibration     # human vs LLM-judge agreement
    uv run python -m eval all             # everything in order
"""
import argparse
import asyncio
import csv
import json
import random
import sys
from datetime import date
from pathlib import Path

from eval.calibration import compute_agreement, render_calibration_markdown
from eval.curve import render_curve
from eval.ground_truth import build_report, render_report_markdown
from eval.judge import judge_draft
from eval.labels import load_labels
from eval.quality_curve import render_quality_curve
from eval.replay_harness import run_replay
from eval.schemas import RubricScore

REPO_ROOT = Path(__file__).resolve().parents[1]
TICKETS_CSV = REPO_ROOT / "data" / "01_customer_tickets.csv"
EVAL_DIR = REPO_ROOT / "eval"
CURVE_DATA = EVAL_DIR / "curve_data.csv"
CURVE_PNG = EVAL_DIR / "curve.png"
QUALITY_SCORES = EVAL_DIR / "quality_scores.csv"
QUALITY_PNG = EVAL_DIR / "quality_curve.png"
GROUND_TRUTH_MD = EVAL_DIR / "ground_truth_report.md"
CALIBRATION_MD = EVAL_DIR / "calibration_report.md"
MANUAL_CSV = EVAL_DIR / "manual_ratings.csv"


async def _cmd_replay() -> None:
    run = await run_replay(
        tickets_csv=TICKETS_CSV,
        repo_root=REPO_ROOT,
        out_csv=CURVE_DATA,
        today=date.today(),
    )
    print(json.dumps(run.model_dump(mode="json"), indent=2, default=str))


def _cmd_curve() -> None:
    final = render_curve(curve_data_csv=CURVE_DATA, out_png=CURVE_PNG)
    print(f"Final answer rate: {final:.2%}  →  {CURVE_PNG}")


def _cmd_ground_truth() -> None:
    labels = load_labels(TICKETS_CSV)
    report = build_report(predictions_csv=CURVE_DATA, labels=labels)
    render_report_markdown(report, GROUND_TRUTH_MD)
    print(json.dumps(report, indent=2))


async def _cmd_judge(n: int = 50, seed: int = 17) -> None:
    rows = _load_drafts_for_judging()
    if not rows:
        print("No answerable drafts found in curve_data.csv — run replay first.")
        sys.exit(1)

    rng = random.Random(seed)
    sample = rng.sample(rows, min(n, len(rows)))

    schema = (REPO_ROOT / "kb" / "_schema.md").read_text() if (
        REPO_ROOT / "kb" / "_schema.md"
    ).exists() else ""

    scores: list[RubricScore] = []
    for row in sample:
        score = await judge_draft(
            ticket_id=row["ticket_id"],
            customer_message=row["message_body"],
            draft_reply=row["draft_reply"],
            cited_excerpts=row["pages_read"],
            brand_voice_contract=schema,
        )
        scores.append(score)
        print(f"  {row['ticket_id']}  overall={score.overall}")

    _write_scores(scores, sample)


def _load_drafts_for_judging() -> list[dict]:
    import pandas as pd

    curve = pd.read_csv(CURVE_DATA)
    tickets = pd.read_csv(TICKETS_CSV)
    merged = curve.merge(tickets, on="ticket_id", suffixes=("", "_t"))
    out = []
    for _, row in merged.iterrows():
        if not bool(row["can_answer_fully"]):
            continue
        out.append(
            {
                "ticket_id": row["ticket_id"],
                "ticket_index": int(row["ticket_index"]),
                "message_body": str(row["message_body"]),
                "draft_reply": str(row.get("draft_reply") or ""),
                "pages_read": str(row.get("pages_read") or "").split("|"),
            }
        )
    return out


def _write_scores(scores: list[RubricScore], rows: list[dict]) -> None:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    index_by_id = {r["ticket_id"]: r["ticket_index"] for r in rows}
    with QUALITY_SCORES.open("w", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(
            [
                "ticket_index",
                "ticket_id",
                "grounded",
                "brand_voice",
                "completeness",
                "no_hallucination",
                "tone_fit",
                "overall",
                "notes",
            ]
        )
        for s in scores:
            writer.writerow(
                [
                    index_by_id.get(s.ticket_id, ""),
                    s.ticket_id,
                    s.grounded,
                    s.brand_voice,
                    s.completeness,
                    s.no_hallucination,
                    s.tone_fit,
                    s.overall,
                    s.notes,
                ]
            )


def _cmd_quality_curve() -> None:
    final = render_quality_curve(scores_csv=QUALITY_SCORES, out_png=QUALITY_PNG)
    print(f"Final rubric overall: {final:.2f}  →  {QUALITY_PNG}")


def _cmd_calibration() -> None:
    import pandas as pd

    human = pd.read_csv(MANUAL_CSV)
    human = human[~human["ticket_id"].astype(str).str.startswith("TKT-PLACEHOLDER")]
    llm = pd.read_csv(QUALITY_SCORES)
    llm = llm[llm["ticket_id"].isin(human["ticket_id"])]

    if human.empty or llm.empty:
        print("Need filled manual_ratings.csv + judge output overlap.")
        sys.exit(1)

    agreement = compute_agreement(human=human, llm=llm)
    render_calibration_markdown(agreement, CALIBRATION_MD)
    print(json.dumps(agreement, indent=2))


async def _cmd_all() -> None:
    await _cmd_replay()
    _cmd_curve()
    _cmd_ground_truth()
    await _cmd_judge()
    _cmd_quality_curve()
    _cmd_calibration()


def main() -> None:
    parser = argparse.ArgumentParser(prog="eval")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("replay", "curve", "ground-truth", "judge", "quality-curve", "calibration", "all"):
        sub.add_parser(name)
    args = parser.parse_args()

    if args.cmd == "replay":
        asyncio.run(_cmd_replay())
    elif args.cmd == "curve":
        _cmd_curve()
    elif args.cmd == "ground-truth":
        _cmd_ground_truth()
    elif args.cmd == "judge":
        asyncio.run(_cmd_judge())
    elif args.cmd == "quality-curve":
        _cmd_quality_curve()
    elif args.cmd == "calibration":
        _cmd_calibration()
    elif args.cmd == "all":
        asyncio.run(_cmd_all())


if __name__ == "__main__":
    main()
