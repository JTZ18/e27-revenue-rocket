# Roadmap

What's deliberately out of MVP and the plan for activating it.

## In MVP (this repo)

- Five active self-improving loops (gap-→-KB, persona discovery + drift, weekly themes, monthly brief, weekly conflicts).
- External sentiment benchmarking via `last30days` (bonus loop).
- Wiki-traversal agent with file-path citations.
- Pydantic-validated KB frontmatter with conflict-resolution domain hierarchy.
- Read-only Next.js dashboard over the full state machine.
- Reproducible longitudinal evaluation with Git-SHA provenance, hand-rate + LLM-judge calibration, ground-truth accuracy report.

## Deferred — production roadmap

### qmd nav-accelerator

Activate when the KB exceeds ~200 entries. Integrate the `qmd` MCP server for BM25 + embedding pre-ranking ahead of the traversal call. Keeps the agent's working set small without sacrificing the auditable file-read pattern.

### Live Instagram + WhatsApp channels

Architecture-only stubs today. Activation requires Meta app review, WhatsApp Business onboarding, and Singpass-compliant data handling. Common Event Schema already lets either channel feed the pipeline once adapters are written.

### Real Shopify Admin API

Order-status lookup (per SOP §3) and inventory signals into persona weighting. The dummy `data/05b_product_reference.docx` stands in for the live catalogue today.

### Multi-language

Detection + brand-voice variants for Singlish, Bahasa Melayu, and Mandarin. The `_schema.md` brand-voice contract is per-channel today; extension is per-language.

### Brand-voice loop activation

Capture `diff(sent, draft)` from Gmail, weekly analyser, schema updates. Architecture is in place (see spec §5.6); just not live-demoed.

### PII redaction layer

For production deployment. The MVP relies on Gmail/Sheet's native handling and on the fact that the dummy data is already anonymised.

### Per-brand cold-start onboarding wizard

To support the "deploys to your brand in a week" claim. Walk a new brand through KB seeding, `_schema.md` voice contract authoring, and persona discovery in a guided flow.

### Daily KB conflict detector

Demoted to weekly in the MVP per premortem v2 (Slack approval fatigue). Re-promote to daily once volume justifies it.

### CS-team dashboard polish

Today's dashboard is read-only. Future work: action affordances (approve from dashboard, edit KB entries inline) gated by the same Slack-approved auth flow that gates the n8n primitive.

### Provider redundancy

OpenRouter handles strategic calls; Minimax handles hot path. Future: Anthropic / OpenAI fallback when either provider is degraded. The `LLMClient` enum makes the swap trivial.

## Deferred from Plan 4

The following items were scoped in Plan 4 but deliberately deferred so write-ups and the pitch deck could ship first:

### Dashboard development

- Next.js 15 dashboard scaffold (`dashboard/`)
- Dashboard API client + TypeScript types
- Dashboard pages: Status home, KB, Gaps, Themes, Personas, Briefs, Sentiment
- Dashboard-supporting API endpoints (`/gaps/list`, `/personas/list`, `/briefs/list`)

### Final integration check

- Full test suite run + dashboard smoke build
- All n8n workflow JSON validation
- Pitch deck 16-slide sanity check
- GitHub Pages live confirmation
- Tag `plan-4-complete`

These will be picked up in a follow-up Plan 5 or merged ad-hoc once the dashboard is ready.
