# E27 Echelon Submission — Self-Improving Customer Intelligence Engine

A 5-minute read for the judges. The repo, the spec, the eval, and the dashboard back every claim here with evidence.

## The 30-second version

Boldr Watch's CS team answers dozens of weekly customer enquiries and forgets every novel question. We built a self-improving customer-intelligence engine that turns SOP §6 "New Questions Log" — already a manual habit — into an active system. The wiki-traversal agent reads the KB, answers in brand voice, flags gaps without hallucinating, lets a human resolve each gap once, auto-drafts a new KB entry, and commits it to Git on Slack approval. Five loops, one HITL primitive, zero-PR audit trail. The headline proof is `eval/curve.png`: a longitudinal answer-rate curve over 70 replayed tickets with Git short SHAs annotated at each KB-growth event.

## Our USP — two frontier-tech bets

### 1. Karpathy-style LLM wiki, not embeddings RAG

At ~50–100 KB entries we deliberately do **not** use a vector DB. The agent reads `kb/index.md`, drills into specific files, and synthesises an answer — exactly the pattern Andrej Karpathy outlined for LLM-readable wikis. Four reasons this wins at MVP scale:

1. **Auditable citations** — the agent literally says "I read `kb/faqs/bpa-straps.md`". A cosine score doesn't survive a Q&A.
2. **Deterministic re-reading** — same input → same file-read path. Embedding drift is a thing; markdown isn't.
3. **Zero infra** — no embedding pipeline, no vector DB, no re-index step. Markdown in Git is the entire stack.
4. **Self-documenting taxonomy** — the file tree IS the schema. Reviewers can read the wiki without our help.

When the KB grows past ~200 entries we drop in `qmd` (BM25 + embedding pre-ranking) as a *prefix* to the same traversal — the agent's mental model and the audit trail are unchanged. See `docs/ROADMAP.md`.

### 2. We treat external sentiment as a first-class skill

The `last30days` CLI is a frontier agent skill — an installable, prompt-driven research tool that pulls live signal from Reddit, X, YouTube, TikTok, HN, and the open web in one shot. Most submissions would either ignore external signal or write a brittle scraper. We use the skill the way it's designed: an LLM planner emits a `--plan.json` per top theme, the skill runs, an LLM comparator emits a verdict (`market_wide | boldr_specific | aligned | insufficient_data`), and the verdict feeds the monthly marketing brief. Result: the system distinguishes "broad market signal — capitalise" from "niche concern — patch KB".

This is also our scalability story: when Boldr wants to launch a campaign in a new region or category, the system can already see what the rest of the internet is saying about that topic.

## Workflow logic

One HITL primitive (`Wait for Webhook` in n8n), five active loops:

| Loop | Trigger | Output | Human approval |
|---|---|---|---|
| Gap → KB (hero) | Ticket arrives | Gmail draft OR Slack gap card → KB commit | Gmail send + Slack button |
| Persona discovery + drift | Manual (cold start) + weekly cron | `kb/personas/<axis>/<slug>.md` | Slack interactive card |
| Weekly theme clusterer | Cron Mon 09:00 | `kb/themes/<date>.md` | Auto-commit; humans review on dashboard |
| Monthly brief | Cron 1st 09:00 | `briefs/<YYYY-MM>-marketing-brief.md` | Auto-commit; humans review |
| Weekly conflict digest | Cron Mon 11:00 | Slack Block Kit digest | One-click resolution per conflict |
| External sentiment (bonus) | Cron Mon 12:00 | `external-intel/<YYYY-MM>/<theme>.json` | Auto-commit; surfaced in brief |

Workflow is built in n8n so the CS team can inspect, debug, and modify the orchestration without a developer. The HTTP nodes call our FastAPI service for everything that needs typed Python logic; n8n owns triggers, queueing, and human-facing surfaces.

## Business impact

| Today (manual) | With the engine |
|---|---|
| Every novel question is answered and forgotten | Every novel question becomes a KB entry |
| FAQ grows by goodwill | FAQ grows by process |
| Sustainability + vegan-strap demand stays in inboxes | Patterns surface in monthly brief with internal-vs-external sentiment context |
| KB contradictions silently accumulate | Weekly conflict digest with one-click resolution |
| New campaigns rely on intuition | Briefs cite internal frequency + external mentions per theme |

**Quantified:** the headline answer-rate curve climbs from 0% (empty KB) to a stable high-confidence rate over 70 chronologically-replayed tickets. LLM-judge quality scores (5-dimension rubric: grounded / brand_voice / completeness / no_hallucination / tone_fit) are calibrated against 20 hand-rated drafts; agreement reported in `eval/calibration_report.md`.

**Generalises beyond Boldr.** Channel adapters are the only Boldr-specific layer; everything downstream of the Common Event Schema (in `intel_engine/schemas/event.py`) is brand-agnostic. The "deploys to any SME with a growing FAQ" claim is grounded in this contract.

## Cost realism

We chose tools that keep recurring cost flat or near-zero:

- **Storage**: Markdown in Git. Zero ongoing cost. No vector DB, no managed search.
- **LLM routing**: Minimax (Sonnet-tier) for the hot/frequent path (traversal, gap detection, theme clustering, drift detection, sentiment planning). OpenRouter (Kimi-tier reasoning) reserved for monthly/weekly strategic calls (persona discovery, brief writer, conflict detector, sentiment comparator, LLM-as-judge). Estimated steady-state cost for Boldr volume: well under USD 50/month.
- **Orchestration**: Self-hosted n8n in a single Docker container. Free.
- **External sentiment**: `last30days` ships 10,000 free ScrapeCreators calls — enough for weekly scans on the top 3 themes for ~2 years. Optional paid providers (xAI, Brave, Exa) are pluggable, not required.
- **Dashboard**: Next.js static-ish read-only deploy. Can run on Vercel free tier or any Node host.

**No re-embedding cost** is the killer line. Every competitor that picked vector RAG signed up for an ongoing index-maintenance bill we don't have.

## Safeguards

| Risk | Mitigation |
|---|---|
| Hallucinated answers | Agent emits structured `{can_answer_fully, missing_info, ...}`. If `can_answer_fully=false`, the pipeline branches to gap creation — never to a fabricated reply. |
| Bad KB entries getting committed | Every KB write requires Slack approval. The auto-drafter only stages; the human Approve button is what triggers the git commit. |
| Brand-voice drift | `kb/_schema.md` is the brand-voice contract loaded into the drafter's system prompt every call. Future activation: brand-voice loop (diff between sent and draft) — architecture in place, not yet live. |
| Stale KB entries | Frontmatter `status: active | stale | draft` is filtered in the traversal prompt. Entries are never deleted (preserves audit). |
| Same-fact contradictions | Conflict detector runs weekly; per-domain hierarchy (`pricing → rate card`, `policy → SOP`, `spec → product reference`) resolves cross-domain disagreements deterministically. |
| Persona drift false positives | Drift threshold = ≥3 unmatched tickets in 6 weeks. Tunable; defaults sized for Boldr volume. |
| Unbounded LLM cost | Provider client wraps `complete_json` with structured-output mode + a single retry, no infinite re-tries. Long workflows are cron-scheduled, not event-driven. |
| Approval fatigue | Low-urgency loops (conflicts, drift) batch into weekly Slack digests, not per-event pings. |
| PII | We rely on Gmail / Sheet's native handling; production roadmap calls out a dedicated PII redaction layer. |

## Proof of execution

We commit to "self-improving" being a measurable claim, not a marketing one.

1. **Longitudinal replay** — `eval/replay_harness.py` starts with empty `kb/faqs/`, replays 70 tickets chronologically, calls real LLMs, produces real git commits on a throwaway `eval/replay-<date>` branch. Output: `eval/curve.png` annotated with Git short SHAs at every KB-growth event.
2. **Ground-truth accuracy** — held-out CSV labels (`question_type`, `buyer_persona`, `answered_by_kb`, `requires_escalation`) the agent never sees. Per-class precision / recall / F1 in `eval/ground_truth_report.md`.
3. **Quality eval** — 20 drafts hand-rated by the submitter against a published 5-dimension rubric (`eval/rubric.md`), 50 more rated by an LLM judge, Cohen's kappa + per-dimension MAE between the two in `eval/calibration_report.md`.
4. **End-to-end smoke tests** — `tests/test_e2e_*.py` exercise every loop with mocked LLM responses against the real FastAPI app, real KB writer, and real git commits in a tmpdir.
5. **Visible audit trail** — every KB / persona / theme / brief / conflict / sentiment artefact is a real git commit with approver + timestamp in the message. `git log --grep="^kb:"` is the audit query.

Reviewers can run `uv run python -m eval all` on a clean checkout to reproduce the curve from scratch.

## Where to look

| You want to see | Open |
|---|---|
| The system live | `docker compose up -d n8n && uv run uvicorn intel_engine.api:app --port 8000 && cd dashboard && npm run dev` |
| The headline proof | `eval/curve.png` + `docs/EVAL.md` |
| The architecture diagram | `docs/ARCHITECTURE.md` |
| The pitch deck | https://jtz18.github.io/e27-revenue-rocket/ (see `pitch/index.html`) |
| The design contract | `docs/superpowers/specs/2026-05-16-customer-intelligence-engine-design.md` |
| The five-minute video | See submission form |

Thank you for reading.
