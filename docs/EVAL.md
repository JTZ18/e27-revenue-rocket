# Evaluation Methodology + Results

## 1. Why this eval exists

The brief asks for a self-improving customer-intelligence system. "Self-improving"
is only credible if proved *quantitatively*. We do that with three artefacts:

1. **Longitudinal answer-rate curve** (`eval/curve.png`) — replays 70 tickets
   chronologically starting from an empty `kb/faqs/`; the curve shows the
   system's answer rate climbing as the KB grows. Each step that produces a
   new KB entry is annotated with the git short SHA of the resulting commit.
2. **Draft-quality curve** (`eval/quality_curve.png`) — LLM-as-judge scores
   each answered draft on a 5-dimension rubric over the same chronological
   ticket index.
3. **Calibration** (`eval/calibration_report.md`) — the LLM judge is
   re-scored against 20 hand-rated drafts. Kappa + per-dimension MAE quantify
   trust in the judge.

## 2. Replay harness

`eval/replay_harness.py` runs the real traversal agent on each ticket in
chronological order. When the agent flags a gap, the harness fabricates a
short synthetic KB entry (`eval.synthetic_resolver`) grounded in the
held-out `question_type` label, writes it to `kb/faqs/`, regenerates
`kb/index.md`, and commits via the same `intel_engine.kb.writer` used in
production. The replay runs on a throwaway `eval/replay-<date>` branch so the
real `main` is untouched. Every commit is a real git commit; every LLM call
is a real Minimax/Kimi call.

## 3. Ground-truth accuracy (`eval/ground_truth_report.md`)

The CSV ships with held-out columns (`question_type`, `buyer_persona`,
`answered_by_kb`, `requires_escalation`) that the agent never sees. We report
theme accuracy, persona accuracy, gap-detection precision/recall/F1, and
escalation accuracy against those labels.

## 4. Quality eval — rubric

Rubric: `eval/rubric.md`. Five integer-1-to-5 dimensions: grounded,
brand_voice, completeness, no_hallucination, tone_fit. Aggregate = mean.

## 5. Hand-rating + LLM-judge

- 20 drafts hand-rated by the submitter — `eval/manual_ratings.csv`.
- All answerable drafts (target n=50) scored by Kimi judge — `eval/quality_scores.csv`.
- Calibration on the 20 overlap: per-dimension MAE + quadratic-weighted
  Cohen's kappa — `eval/calibration_report.md`.

## 6. Reproducibility

```bash
git checkout -b eval/replay-<date>
uv run python -m eval all
```

Random seeds: judge sampling uses `seed=17` (see `_cmd_judge`). Replay is
inherently deterministic up to LLM non-determinism (temperature settings
match production).

## 7. Provenance

`eval/curve_data.csv` — one row per ticket, includes the git short SHA of
the KB-growth commit if any. The video shows the terminal running the replay
and the curve rendering alongside `git log` to demonstrate the SHAs are real.
