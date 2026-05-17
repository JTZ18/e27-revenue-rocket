# Boldr Watch — Self-Improving Customer Intelligence Engine

E27 Echelon 2026 · Boldr Watch E-commerce Challenge submission.

This repo is a working customer-intelligence system for a Singapore titanium-watch
micro-brand. It answers known questions in the brand voice, detects gaps without
hallucinating, auto-updates its knowledge base when humans resolve a gap, clusters
weekly themes, writes monthly marketing briefs, benchmarks internal signal against
external market sentiment via `last30days`, and ships a read-only Next.js dashboard
over the whole state machine. All audit trail is in Git; humans never see a PR.

## 60-second tour

1. **Open the pitch deck:** <https://jtz18.github.io/e27-revenue-rocket/> — 16 slides, judging-rubric aligned. (Source: [`pitch/index.html`](pitch/index.html).)
2. **Read the submission writeup:** [`docs/SUBMISSION.md`](docs/SUBMISSION.md) — workflow logic, business impact, cost realism, safeguards, proof of execution.
3. **Read the spec:** [`docs/superpowers/specs/2026-05-16-customer-intelligence-engine-design.md`](docs/superpowers/specs/2026-05-16-customer-intelligence-engine-design.md) — the design contract this repo implements.
4. **Watch the video:** see the linked Loom / YouTube URL on the submission form.
5. **See the headline proof:** [`eval/curve.png`](eval/curve.png) is the longitudinal answer-rate curve over 70 replayed tickets, with Git short SHAs annotated at each KB-growth event. [`docs/EVAL.md`](docs/EVAL.md) explains methodology and numbers.
6. **Skim the architecture:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — one-primitive / five-loops diagram + every component covered.
7. **Read the roadmap:** [`docs/ROADMAP.md`](docs/ROADMAP.md) — what's MVP today and what's deferred.

## What's in this repo

| Path | Purpose |
|---|---|
| `intel_engine/` | Python service: agents, schemas, KB writer, gap logger, sentiment runner |
| `kb/` | The Karpathy-style markdown wiki the agents read and write |
| `kb/_workflows/` | Versioned LLM prompts (one per agent) |
| `gap-log/` | Open + resolved gap entries (one JSON file per gap) |
| `briefs/` | Monthly marketing briefs (Markdown, auto-committed) |
| `external-intel/YYYY-MM/` | Cached `last30days` reports + comparator verdicts |
| `eval/` | Replay harness, headline curve, judge scores, ground-truth report |
| `workflows/n8n/` | Exported n8n workflows (one per loop) |
| `dashboard/` | Read-only Next.js 15 state viewer |
| `data/` | Original Boldr-provided dummy data (CSVs, FAQ PDF, SOP) |
| `docs/` | Submission docs: ARCHITECTURE, EVAL, ROADMAP, N8N_SETUP |

## Running it locally

### Prerequisites

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) for Python dependency management
- Node 20+ (for the dashboard)
- Docker + Docker Compose (for n8n)
- Provider API keys (OpenRouter, Minimax) — see `.env.example`
- The `last30days` CLI v3.0.5 (vendored; path configurable via `LAST30DAYS_SCRIPT`)

### Quickstart

```bash
# 1. Install Python deps
uv sync

# 2. Copy env and fill in provider keys
cp .env.example .env
$EDITOR .env

# 3. Start the FastAPI service (port 8000)
uv run uvicorn intel_engine.api:app --port 8000

# 4. Start n8n in another terminal
docker compose up -d n8n
# Open http://localhost:5678 and import workflows/n8n/*.json

# 5. Start the dashboard in a third terminal
cd dashboard
cp .env.example .env.local
npm install
npm run dev
# Open http://localhost:3000
```

### Reproducing the headline curve

```bash
git checkout -b eval/reproduce-$(date +%Y-%m-%d)
uv run python -m eval all
open eval/curve.png
```

Detailed setup and per-workflow notes in [`docs/N8N_SETUP.md`](docs/N8N_SETUP.md).

## The five loops at a glance

1. **Gap → KB (hero loop)** — ticket → traversal agent → either Gmail Draft or Slack gap card → human resolves → auto-drafted KB entry → Slack approval → Git commit.
2. **Persona discovery + drift** — Kimi cold-start across three axes (lifecycle / interest / behaviour); weekly Minimax drift detector proposes new personas when ≥3 unmatched tickets accumulate in a 6-week window.
3. **Weekly theme clusterer + monthly brief** — Minimax weekly clusters, Kimi monthly synthesises a marketing brief.
4. **Weekly KB conflict digest** — Kimi reads the whole KB; Slack digest with one-click resolution.
5. **External sentiment benchmark (bonus)** — Minimax plans `last30days` queries per top theme; the CLI runs; an OpenRouter comparator emits `market_wide / boldr_specific / aligned / insufficient_data` verdicts that feed into the monthly brief.

All loops share a single n8n HITL primitive: `Wait for Webhook`.

## Tests

```bash
uv run pytest -v
```

E2E smoke tests cover the hero loop and each of the background loops; the
replay harness in `eval/` produces real Git commits against a temporary branch.

## Licence + acknowledgements

Dummy customer data, FAQ, rate cards, SOP and product reference: © Boldr Watch.
Used for the E27 hackathon submission per the brief's data-handling permissions.

Code and documentation in this repo: see `LICENSE`.
