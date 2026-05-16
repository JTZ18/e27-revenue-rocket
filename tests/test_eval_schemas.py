"""Test eval schemas."""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from eval.schemas import (
    EvalLabel,
    ReplayRun,
    ReplayStep,
    RubricScore,
)


def test_eval_label_validates_yes_no():
    label = EvalLabel(
        ticket_id="TKT-1046",
        question_type="knowledge_gap",
        buyer_persona="niche_buyer",
        answered_by_kb=False,
        requires_escalation=True,
    )
    assert label.answered_by_kb is False
    assert label.requires_escalation is True


def test_replay_step_records_provenance():
    step = ReplayStep(
        ticket_id="TKT-1046",
        ticket_index=0,
        received_at=datetime(2025, 11, 15, 16, 19, tzinfo=timezone.utc),
        pages_read=["kb/faqs/bpa.md"],
        can_answer_fully=True,
        themes_detected=["materials_safety"],
        persona_hints=["health_conscious"],
        confidence="high",
        draft_reply="Yes. All Boldr straps are BPA-free.",
        gap_created=False,
        kb_entry_added_slug=None,
        kb_commit_sha=None,
    )
    assert step.gap_created is False


def test_replay_step_gap_path_requires_no_reply():
    with pytest.raises(ValidationError):
        ReplayStep(
            ticket_id="TKT-1010",
            ticket_index=1,
            received_at=datetime(2025, 11, 19, tzinfo=timezone.utc),
            pages_read=[],
            can_answer_fully=False,
            themes_detected=[],
            persona_hints=[],
            confidence="low",
            draft_reply="this should not be here",
            gap_created=True,
            kb_entry_added_slug="some-slug",
            kb_commit_sha="abc1234",
        )


def test_rubric_score_clamps_range():
    with pytest.raises(ValidationError):
        RubricScore(
            ticket_id="TKT-1046",
            grounded=6,
            brand_voice=5,
            completeness=5,
            no_hallucination=5,
            tone_fit=5,
        )


def test_rubric_score_overall_mean():
    score = RubricScore(
        ticket_id="TKT-1046",
        grounded=5,
        brand_voice=4,
        completeness=5,
        no_hallucination=5,
        tone_fit=4,
    )
    assert score.overall == 4.6


def test_replay_run_aggregates():
    run = ReplayRun(
        started_at=datetime(2026, 5, 17, tzinfo=timezone.utc),
        finished_at=datetime(2026, 5, 17, 1, tzinfo=timezone.utc),
        seed_kb_sha="seed123",
        ticket_count=70,
        answered_count=42,
        gap_count=28,
        branch="eval/replay-2026-05-17",
    )
    assert run.answer_rate == pytest.approx(0.6)
