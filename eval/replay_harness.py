"""Longitudinal replay harness.

Replays tickets chronologically through the real traversal agent. For each
gap, fabricates a synthetic resolution and commits it to git, so the next
ticket on the same topic can retrieve it. Outputs per-step provenance to CSV
and returns an aggregate ReplayRun.
"""
import csv
import subprocess
from datetime import date, datetime
from pathlib import Path

from eval.kb_snapshot import KBSnapshot
from eval.labels import load_tickets_input
from eval.schemas import ReplayRun, ReplayStep
from eval.synthetic_resolver import synthesise_resolution
from intel_engine import settings
from intel_engine.agents.traversal import traverse
from intel_engine.kb.writer import write_and_commit_entry
from intel_engine.schemas.event import Channel, CommonEvent, Customer


def _git_head_sha(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _event_from_row(row: dict, idx: int) -> CommonEvent:
    return CommonEvent(
        event_id=f"replay_{idx:03d}_{row['ticket_id']}",
        source=Channel.google_sheet,
        channel_meta={"original_channel": row.get("channel", "")},
        customer=Customer(
            id=f"anon_{row['ticket_id']}",
            name=str(row["customer_name"]),
        ),
        subject=str(row.get("subject") or "") or None,
        body=str(row["message_body"]),
        ts=datetime.fromisoformat(str(row["date_received"])),
    )


async def run_replay(
    *,
    tickets_csv: Path,
    repo_root: Path,
    out_csv: Path,
    today: date,
) -> ReplayRun:
    """Execute the full replay, writing curve_data.csv and committing entries."""
    kb_root = repo_root / "kb"
    settings.kb_root.cache_clear()

    snapshot = KBSnapshot(kb_root)
    snapshot.start_replay_state()
    seed_sha = _git_head_sha(repo_root)

    tickets = load_tickets_input(tickets_csv)
    started_at = datetime.now().astimezone()
    steps: list[ReplayStep] = []

    try:
        for idx, row in tickets.iterrows():
            event = _event_from_row(row.to_dict(), idx)
            result = await traverse(event)

            kb_slug: str | None = None
            commit_sha: str | None = None

            if not result.can_answer_fully:
                entry = synthesise_resolution(
                    ticket_id=str(row["ticket_id"]),
                    customer_question=event.body,
                    question_type=str(row.get("subject") or "general"),
                    themes_detected=result.themes_detected,
                    today=today,
                )
                commit_sha = write_and_commit_entry(
                    entry,
                    approver="replay-harness",
                    repo_root=repo_root,
                )
                kb_slug = entry.frontmatter.slug

            steps.append(
                ReplayStep(
                    ticket_id=str(row["ticket_id"]),
                    ticket_index=int(idx),
                    received_at=event.ts,
                    pages_read=result.pages_read,
                    can_answer_fully=result.can_answer_fully,
                    themes_detected=result.themes_detected,
                    persona_hints=result.persona_hints,
                    confidence=result.confidence.value,
                    draft_reply=result.draft_reply,
                    gap_created=not result.can_answer_fully,
                    kb_entry_added_slug=kb_slug,
                    kb_commit_sha=commit_sha,
                )
            )
    finally:
        _write_csv(out_csv, steps)
        snapshot.restore()

    answered = sum(1 for s in steps if s.can_answer_fully)
    return ReplayRun(
        started_at=started_at,
        finished_at=datetime.now().astimezone(),
        seed_kb_sha=seed_sha,
        ticket_count=len(steps),
        answered_count=answered,
        gap_count=len(steps) - answered,
        branch=_current_branch(repo_root),
    )


def _current_branch(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _write_csv(out_csv: Path, steps: list[ReplayStep]) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "ticket_index",
        "ticket_id",
        "received_at",
        "pages_read",
        "can_answer_fully",
        "themes_detected",
        "persona_hints",
        "confidence",
        "draft_reply",
        "gap_created",
        "kb_entry_added_slug",
        "kb_commit_sha",
    ]
    with out_csv.open("w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for step in steps:
            writer.writerow(
                {
                    "ticket_index": step.ticket_index,
                    "ticket_id": step.ticket_id,
                    "received_at": step.received_at.isoformat(),
                    "pages_read": "|".join(step.pages_read),
                    "can_answer_fully": step.can_answer_fully,
                    "themes_detected": "|".join(step.themes_detected),
                    "persona_hints": "|".join(step.persona_hints),
                    "confidence": step.confidence,
                    "draft_reply": step.draft_reply or "",
                    "gap_created": step.gap_created,
                    "kb_entry_added_slug": step.kb_entry_added_slug or "",
                    "kb_commit_sha": step.kb_commit_sha or "",
                }
            )
