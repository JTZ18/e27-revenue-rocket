# Evaluation Methodology + Results

## 1. Why this eval exists

The brief asks for a self-improving customer-intelligence system. "Self-improving"
is only credible if proved *quantitatively*. We do that with three artefacts:

1. **Longitudinal answer-rate curve** (`eval/curve.png`) — replays 70 tickets
   chronologically starting from an empty `kb/faq/`; the curve shows the
   system's answer rate climbing as the KB grows. Each step that produces a
   new KB entry is annotated with the git short SHA of the resulting commit.
2. **Draft-quality curve** (`eval/quality_curve.png`) — LLM-as-judge scores
   each answered draft on a 5-dimension rubric over the same chronological
   ticket index.
3. **Calibration** (`eval/calibration_report.md`) — the LLM judge is
   re-scored against 20 hand-rated drafts. Kappa + per-dimension MAE quantify
   trust in the judge. (Pending manual ratings.)

## 2. Replay harness

`eval/replay_harness.py` runs the real traversal agent on each ticket in
chronological order. When the agent flags a gap, the harness fabricates a
short synthetic KB entry (`eval.synthetic_resolver`) grounded in the
held-out `question_type` label, writes it to `kb/faq/`, regenerates
`kb/index.md`, and commits via the same `intel_engine.kb.writer` used in
production. The replay runs on a throwaway `eval/replay-<date>` branch so the
real `main` is untouched. Every commit is a real git commit; every LLM call
is a real OpenRouter call.

**Live run (2026-05-17)**
- Tickets: 70
- Answered fully: 13 (18.57%)
- Gaps created: 57
- Branch: `eval/replay-2026-05-17-rerun`

## 3. Ground-truth accuracy (`eval/ground_truth_report.md`)

The CSV ships with held-out columns (`question_type`, `buyer_persona`,
`answered_by_kb`, `requires_escalation`) that the agent never sees.

| Metric | Value |
|---|---|
| Theme classification accuracy | 44.29% |
| Persona classification accuracy | 27.14% |
| Gap detection — precision | 33.33% |
| Gap detection — recall | 95.00% |
| Gap detection — F1 | 49.35% |
| Escalation accuracy | 50.00% |

## 4. Quality eval — rubric

Rubric: `eval/rubric.md`. Five integer-1-to-5 dimensions: grounded,
brand_voice, completeness, no_hallucination, tone_fit. Aggregate = mean.

**LLM-judge sample (n = 13 answerable drafts)**

| Ticket | Overall |
|---|---|
| TKT-1026 | 2.4 |
| TKT-1063 | 4.2 |
| TKT-1049 | 3.0 |
| TKT-1008 | 4.2 |
| TKT-1050 | 2.6 |
| TKT-1033 | 3.8 |
| TKT-1070 | 2.4 |
| TKT-1020 | 2.6 |
| TKT-1069 | 2.2 |
| TKT-1041 | 2.0 |
| TKT-1006 | 2.4 |
| TKT-1001 | 2.2 |
| TKT-1047 | 4.2 |

**Mean rubric overall: 2.20 / 5.00**

## 5. Hand-rating + LLM-judge

- 20 drafts hand-rated by the submitter — `eval/manual_ratings.csv`.
- All answerable drafts scored by LLM judge — `eval/quality_scores.csv`.
- Calibration on the 20 overlap: pending manual ratings.

## 6. Reproducibility

```bash
git checkout -b eval/replay-$(date +%Y-%m-%d)
uv run python -m eval all
```

Random seeds: judge sampling uses `seed=17` (see `_cmd_judge`). Replay is
inherently deterministic up to LLM non-determinism (temperature settings
match production).

## 7. Provenance

`eval/curve_data.csv` — one row per ticket, includes the git short SHA of
the KB-growth commit if any.
