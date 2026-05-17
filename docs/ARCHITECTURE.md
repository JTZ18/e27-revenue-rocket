# Architecture

This document is the technical-depth handout. The 5-minute video gives the elevator pitch; this doc answers the follow-up questions.

## Design contract

Implementation follows [`docs/superpowers/specs/2026-05-16-customer-intelligence-engine-design.md`](superpowers/specs/2026-05-16-customer-intelligence-engine-design.md). Four sequential plans implement the spec end-to-end:

| Plan | Scope | Status |
|---|---|---|
| 1 | Foundation + hero gap-→-KB loop | Complete |
| 2 | Evaluation harness (longitudinal replay, judge, calibration) | Complete |
| 3 | Background loops (persona discovery + drift, themes, monthly brief, conflicts) | Complete |
| 4 | External sentiment + dashboard + handout docs | Complete |

## High-level shape

```
┌──────────────────────────────────────────────────────────────────────┐
│ HUMAN-FACING SURFACES                                                │
│   Google Sheet · Gmail Drafts · Slack interactive cards              │
│   Read-only Next.js dashboard · Weekly email digest                  │
└──────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│ N8N ORCHESTRATION  (one HITL primitive — `Wait for Webhook`)         │
│   01_intake_and_traversal      02_gap_resolution                     │
│   04_persona_discovery         05_weekly_theme_clustering            │
│   06_weekly_persona_drift      07_monthly_marketing_brief            │
│   08_weekly_conflict_digest    09_weekly_external_sentiment          │
└──────────────────────────────────────────────────────────────────────┘
                          │  HTTP (JSON)
                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│ INTEL_ENGINE  (FastAPI + Pydantic)                                   │
│   /traverse  /gap  /draft-kb-entry  /commit-to-kb                    │
│   /personas/{discover,drift,persist,list}                            │
│   /themes/{cluster,persist,list}                                     │
│   /briefs/{monthly,persist,list}                                     │
│   /conflicts/digest                                                  │
│   /sentiment/{plan,run,compare,persist,list}                         │
│   /gaps/list  /kb/summary                                            │
└──────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│ AUDIT + STORAGE  (Git — humans never see PRs)                        │
│   kb/  personas/  gap-log/  briefs/  external-intel/  eval/          │
└──────────────────────────────────────────────────────────────────────┘
```

## Key design choices

### Karpathy-style wiki traversal — no vector DB at MVP scale

The KB is ~50–100 markdown entries. The traversal agent reads `kb/index.md`, drills into specific files, and synthesises an answer. We chose this over embedding RAG because:

- **Auditable citations** — "I read `kb/faqs/bpa-straps.md` and `kb/rate-cards/servicing.md`" beats a cosine score for human trust.
- **Deterministic re-reading** — same input → same file-read path.
- **Cheap maintenance** — no embedding pipeline, no vector DB, no re-index step.
- **Self-documenting** — the file tree IS the taxonomy.

The `qmd` BM25 + embedding nav-accelerator is on the future roadmap for when the KB scales past ~200 entries (see `ROADMAP.md`).

### Markdown + frontmatter as the schema boundary

Every KB entry is a markdown file with Pydantic-validated YAML frontmatter (`slug`, `domain`, `themes`, `last_verified`, `status`, `supersedes`). The `domain` field encodes the conflict-resolution hierarchy (`pricing → rate card`, `policy → SOP`, `spec → product reference`, `faq → catch-all`). Stale entries are marked `status: stale` — never deleted — preserving the audit trail.

### One HITL primitive, five loops

All approvals route through n8n's `Wait for Webhook` node: Slack button clicks, Gmail "send" events, and email-form submissions all hit the same shape. This means we can add a new approval surface in one workflow node, not a one-off integration. Humans never open GitHub; n8n commits on their behalf with a descriptive message including approver + timestamp + source.

### Model routing — Minimax for hot path, OpenRouter for strategic

Per the spec table in §7:

- **Minimax** (Sonnet-tier): traversal, gap detection, KB-drafter, theme clustering, drift detection, sentiment query planning. Hot path, latency-sensitive, frequent.
- **OpenRouter** (Kimi-tier reasoning): cold-start persona discovery, monthly marketing brief, conflict detector, sentiment comparator, LLM-as-judge. Strategic, rare, exec-facing.

Both use the same `LLMClient` wrapper (`intel_engine/llm/client.py`) — OpenAI-compatible API, base URL switched by `LLMProvider` enum.

### Structured JSON outputs, not free-form text

Every agent call uses `complete_json` with `response_format={"type": "json_object"}`. The wrapper tolerates accidental ``` fences and retries once on parse failure. Output models live in `intel_engine/schemas/`. This makes the system testable end-to-end with mocked LLM responses (see `tests/test_*_agent.py`).

### Replay harness — every commit is real

The longitudinal eval (`eval/replay_harness.py`) starts with an empty `kb/faqs/`, replays 70 tickets chronologically, calls the real traversal agent, fabricates synthetic gap resolutions grounded in held-out CSV labels, and commits each resulting KB entry through the same `intel_engine.kb.writer` used in production. Every commit is a real git commit on a throwaway `eval/replay-<date>` branch. The headline `eval/curve.png` annotates each KB-growth event with the resulting short SHA so the curve is independently verifiable.

### External sentiment — bounded, audited, optional

The sentiment loop is gated by environment configuration (`LAST30DAYS_SCRIPT` must point to a working CLI). It runs weekly, processes the top 3 themes from the latest theme report, and writes one JSON file per `external-intel/YYYY-MM/<theme>.json`. The monthly brief reads these files when generating recommendations. If the loop is disabled, the brief still works — `external_sentiment` is an optional field on `MarketingBrief`.

## Module map

```
intel_engine/
├── api.py              ← FastAPI app; the contract n8n calls
├── settings.py         ← env-driven config (LLM endpoints, KB paths)
├── schemas/            ← Pydantic models — the typed contract between agents
├── llm/                ← Provider-agnostic chat client + prompt loader
├── agents/             ← One agent module per LLM-call surface
├── kb/                 ← KB reader (load_kb) + writer (write_and_commit_entry) + index regenerator
├── gap/                ← gap-log writer + reader
├── personas/           ← personas reader + writer
├── themes/             ← themes writer
├── briefs/             ← briefs writer
├── conflicts/          ← conflict digest renderer (Slack Block Kit)
└── sentiment/          ← last30days runner + external-intel writer
```

## n8n workflow summary

| File | Trigger | Purpose |
|---|---|---|
| `01_intake_and_traversal.json` | Google Sheets row added | Normalise → POST `/traverse` |
| `01b_gmail_intake_and_traversal.json` | Gmail trigger | Same, for live email channel |
| `02_gap_resolution.json` | Wait for Webhook (Slack) | Capture gap resolution → draft KB entry → wait again → commit |
| `04_persona_discovery.json` | Manual | One-shot cold-start across all historical tickets |
| `05_weekly_theme_clustering.json` | Cron Mon 09:00 | Cluster last week's tickets → persist report |
| `06_weekly_persona_drift.json` | Cron Mon 10:00 | Detect drift, propose new personas to Slack |
| `07_monthly_marketing_brief.json` | Cron 1st of month 09:00 | Synthesise + commit monthly brief |
| `08_weekly_conflict_digest.json` | Cron Mon 11:00 | Detect KB contradictions → Slack digest |
| `09_weekly_external_sentiment.json` | Cron Mon 12:00 | Plan → run last30days → compare → persist |

## Evaluation discipline

Held-out labels live in a second sheet tab and the eval module — never visible to the agent. See [`docs/EVAL.md`](EVAL.md) for the full methodology: longitudinal curve, ground-truth precision/recall/F1, LLM-judge with calibration against 20 hand-rated drafts, and the rubric in `eval/rubric.md`.

## Where to push back

If a reviewer wants to challenge the design, the doc to argue with is the spec — every decision here was made there. The risk register in spec §12 lists each premortem-identified failure mode and how the implementation mitigates it.
