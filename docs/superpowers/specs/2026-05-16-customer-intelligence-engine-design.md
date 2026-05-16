# Self-Improving Customer Intelligence Engine — Design Spec

**Project:** E27 Echelon 2026 · Boldr Watch E-commerce Challenge
**Date:** 2026-05-16
**Status:** Validated design, ready for implementation planning
**Submission format:** Recorded video ≤ 5 minutes + handout repo

---

## 1. Problem Statement

Boldr is a Singapore titanium-watch micro-brand on Shopify. A 3-person CS team answers dozens of weekly enquiries — primarily over Gmail, with overflow on Instagram DM and WhatsApp — using a manually-maintained FAQ, two rate cards, a product reference, and an SOP that includes a hand-maintained "New Questions Log" (SOP §6).

The current system is **lossy**: every novel question is answered and forgotten. Patterns that reveal marketing opportunities (BPA-free straps, vegan materials, MRI safety, carbon-neutral shipping) disappear into inboxes. The KB grows by goodwill, not by process. There is no intelligence layer.

The challenge is to build an AI workflow that:
1. Answers known questions in the brand's voice (with human approval before send)
2. Detects gaps when KB cannot answer (without hallucinating)
3. Auto-updates the KB once humans resolve the gap
4. Clusters novel questions into themes for trend detection
5. Produces a monthly marketing-intelligence brief
6. **Bonus:** benchmarks internal signal against external market sentiment

The result must generalise to any SME Shopify brand with a considered buyer and a growing FAQ.

---

## 2. Goals & Non-Goals

### Goals (in scope for MVP)

- **G1** — Live reply pipeline: ticket → wiki traversal → human-approved Gmail draft
- **G2** — Gap detection without hallucination: structured agent output `{can_answer_fully, missing_info, …}`
- **G3** — Self-improving KB loop: human resolves gap → auto-drafted KB entry → human approval → committed to Git
- **G4** — Persona system: multi-axis personas (lifecycle / interest / behaviour), seeded by cold-start discovery, evolved by drift detection
- **G5** — Weekly theme clustering and monthly marketing brief
- **G6** — Bonus: dynamic external sentiment via `last30days` CLI with AI-generated `--plan.json` per theme
- **G7** — Longitudinal evaluation: replay harness produces t=0 → t=N answer-rate curve with Git-SHA provenance
- **G8** — Quality eval: hand-rated 20 drafts + LLM-as-judge on remaining 50, with calibration check
- **G9** — Recorded 5-min video demonstrating end-to-end loop closing
- **G10** — Handout repo + README + 90s appendix video for technical depth

### Non-Goals (explicitly out of scope)

- **NG1** — Live OAuth on demo day (video format eliminates this risk)
- **NG2** — Instagram / WhatsApp live integration (architecture-only stubs; Gmail + Google Sheet are live)
- **NG3** — Real Shopify Admin API integration (read product data from local `05b_product_reference.docx`)
- **NG4** — `qmd` / embedding nav-accelerator (future roadmap slide; plain wiki traversal at MVP scale)
- **NG5** — Multi-language support beyond English (production roadmap item)
- **NG6** — Real-time PII redaction beyond what Gmail / Sheet show natively
- **NG7** — Boldr staff on camera (legal scope-out)
- **NG8** — Daily KB conflict detector (demoted to weekly digest)
- **NG9** — Production-ready CS-team-facing dashboard polish (read-only state view is sufficient)

---

## 3. Architecture Overview

### 3.1 High-level diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         HUMAN-FACING SURFACES                            │
│  Google Sheet (demo intake) · Gmail Drafts · Slack interactive cards     │
│  Read-only Next.js dashboard · Weekly email digest                       │
└────────────────────┬────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   CHANNEL ADAPTERS → COMMON EVENT SCHEMA                 │
│  Google Sheet trigger (primary demo) · Gmail trigger (production)        │
│  Instagram DM stub · WhatsApp Business stub                              │
└────────────────────┬────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       N8N ORCHESTRATION (spine)                          │
│  Wait-for-Webhook = single HITL primitive across all loops               │
└────────────────────┬────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       AGENTS (Kimi / Minimax)                            │
│  Wiki-traversal · Auto-draft KB entry · Theme clusterer · Brief writer   │
│  Persona discovery · Persona-drift detector · Conflict detector          │
│  External sentiment planner · LLM-as-judge (eval)                        │
└────────────────────┬────────────────────────────────────────────────────┘
                     │ git API (auto-commit on human approval)
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                AUDIT + STORAGE (Git repo — humans never see PRs)         │
│  kb/  · personas/  · gap-log/  · edits_log/  · briefs/                   │
│  external-intel/  · _schema.md  · _workflows/                            │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Repository structure

```
e27-revenue-rocket/
├── kb/                                  ← The wiki the agent traverses
│   ├── index.md                         ← Karpathy-style entry point
│   ├── faqs/                            ← Per-entry markdown files
│   │   └── <slug>.md
│   ├── products/
│   │   └── <sku>.md
│   ├── rate-cards/
│   │   ├── engraving.md
│   │   └── servicing.md
│   ├── personas/
│   │   ├── lifecycle/                   ← prospect, first_purchase, owner_aftercare
│   │   ├── interest/                    ← health_conscious, gifter, enthusiast, active_outdoor, sustainability
│   │   └── behaviour/                   ← transactional, niche_buyer, engaged
│   ├── _schema.md                       ← Brand voice contract
│   ├── _workflows/                      ← Versioned agent prompts (Symphony pattern)
│   └── _log.md                          ← Append-only audit trail
│
├── gap-log/                             ← Open + resolved gaps
│   └── YYYY-MM-DD-<slug>.md
│
├── edits_log/                           ← CS draft-vs-sent diffs (future feedback loop)
│   └── YYYY-MM-DD-<ticket-id>.json
│
├── external-intel/                      ← Cached last30days reports
│   └── YYYY-MM/<theme>.json
│
├── briefs/                              ← Monthly marketing briefs
│   └── YYYY-MM-marketing-brief.md
│
├── eval/                                ← Evaluation harness + outputs
│   ├── replay_harness.py
│   ├── rubric.md                        ← LLM-as-judge rubric
│   ├── manual_ratings.csv               ← 20 hand-rated drafts
│   ├── curve.png                        ← Headline chart
│   └── curve_data.csv                   ← Raw data for transparency
│
├── workflows/
│   └── n8n/*.json                       ← Exported n8n workflows
│
├── dashboard/                           ← Next.js read-only state viewer
│   └── (Next.js project)
│
├── data/                                ← Original Boldr-provided dummy data
│   └── (untouched source files)
│
├── docs/
│   ├── README.md                        ← Submission entry point
│   ├── ARCHITECTURE.md                  ← Technical depth
│   ├── EVAL.md                          ← Evaluation methodology
│   ├── ROADMAP.md                       ← Future work (qmd, real channels)
│   └── superpowers/specs/               ← This spec lives here
│
└── video/
    ├── storyboard.md
    ├── script.md
    └── (raw recordings, edited cuts)
```

### 3.3 Common Event Schema

All channel adapters normalise to a single shape consumed by the downstream pipeline:

```json
{
  "event_id": "evt_2026-05-16T14:23:11_abc123",
  "source": "google_sheet | gmail | instagram_dm | whatsapp",
  "channel_meta": { "thread_id": "...", "row_index": 42 },
  "customer": { "id": "anon_c042", "name": "Sarah K." },
  "body": "Hi, are your watches safe to wear during an MRI?",
  "subject": null,
  "ts": "2026-05-16T14:23:11+08:00",
  "attachments": []
}
```

This schema is the **contract**. Anything downstream of it is brand-agnostic; anything upstream is channel-specific.

---

## 4. Knowledge Base Design

### 4.1 Wiki-traversal pattern (Karpathy-style)

The agent reads `kb/index.md` first, drills into specific entries by file path, and synthesises an answer. **No vector search at MVP scale** — KB is ~50-100 entries, well within an LLM's ability to navigate from the index. The `qmd` nav-accelerator is on the future roadmap for when KB scales past ~200 entries.

**Why this beats embedding RAG at MVP scale:**
- **Auditable citations:** "I read `kb/faqs/bpa-straps.md` and `kb/rate-cards/servicing.md`" — interpretable by humans, not a cosine score
- **Deterministic re-reading:** the same input produces the same file-read path
- **Cheap to maintain:** no embedding pipeline, no vector DB, no re-index step
- **Self-documenting:** the file tree IS the taxonomy

### 4.2 Entry format (frontmatter contract)

```yaml
---
slug: bpa-free-straps
title: Are Boldr FKM rubber straps BPA-free?
domain: spec | pricing | policy | faq | persona
themes: [materials_safety, sustainability]
sources: [vendor_email_2026-04-12, faq_v3]
last_verified: 2026-05-16
supersedes: []
status: active | stale | draft
---

Yes. All Boldr FKM rubber and silicone straps are 100% BPA-free. This applies
to all current strap SKUs in the catalogue.

Cited compliance: EU REACH, RoHS, ISO 3157.
```

### 4.3 Conflict resolution: per-domain hierarchy

When the agent finds two entries answering the same question, it picks by **domain authority** (declared in `kb/_schema.md`):

| Fact type | Canonical domain |
|---|---|
| Service prices | `pricing` (rate cards) |
| Process / escalation rules | `policy` (SOP) |
| Product specs / materials | `spec` (product reference) |
| Catch-all consumer-facing answers | `faq` |

Same-domain disagreement → escalates to weekly conflict digest.

### 4.4 `kb/_schema.md` — brand voice contract

A single markdown file containing:
- Opening conventions (`"Yes."` / `"No."` declaratives; preferred openers; forbidden openers like *"Great question!"* per SOP §5)
- Tone profile (declarative, technical-but-accessible, em-dash usage, currency format `SGD XX`)
- Cited-standards style (ISO 3157, EU REACH, RoHS, Grade 5 Ti)
- Channel-specific overrides (formal email, terse IG DM, etc.)
- Negative examples and positive examples from existing FAQ

Seeded by hand from the existing 28 FAQs + SOP §5. Updated through the brand-voice loop (future).

---

## 5. The Five Self-Improving Loops

Five active loops in MVP (5.1–5.5) plus one architecture-only loop (5.6 — Brand voice — deferred for activation post-hackathon). All share **one HITL primitive** in n8n: `Wait for Webhook` → human signal (Slack button / Gmail send / email click) → agent writes the approved artefact to Git via n8n's GitHub node. Humans never see Git.

### 5.1 Loop 1 — Gap → KB (HERO LOOP)

```
Ticket arrives → wiki-traversal agent
  └── if can_answer_fully → draft to Gmail Drafts → human sends → done
  └── if too vague → draft clarification question to customer → human approves → sent
  └── if can't answer → create gap entry → notify CS on Slack
                            │
                            ▼
                  CS resolves however they want
                  (asks vendor, boss, themselves)
                            │
                            ▼
                  CS posts answer to gap thread
                            │
                            ▼
                  Agent auto-drafts KB entry in brand voice
                            │
                            ▼
                  Slack interactive card: Approve / Edit / Reject
                            │
                            ▼
                  n8n commits to kb/ on approval
                  (frontmatter complete, sources cited)
```

### 5.2 Loop 2 — Persona drift

- **Cold-start (one-time on deployment):** discovery agent reads historical tickets, proposes initial personas across three axes (lifecycle, interest, behaviour), human approves via Slack, written to `kb/personas/`
- **Steady-state:** drift detector runs weekly. Trigger: ≥3 tickets in a 6-week window not matching any active persona definition. Proposes new persona OR proposes axis extension. Human approves. Old personas marked `status: stale` — never deleted (audit trail preserved).

### 5.3 Loop 3 — Weekly theme clusterer + monthly marketing brief

- Weekly: extract themes from resolved + open tickets, cluster, write to `kb/themes/<week>.md`
- Monthly: brief generator reads themes + KB + persona files + (stubbed) product page content, produces `briefs/YYYY-MM-marketing-brief.md` highlighting:
  - Themes asked N times not covered in product pages
  - Persona-segmented intelligence ("Sustainability buyers: 8 vegan-strap mentions, currently unaddressed")
  - Recommended product page edits

### 5.4 Loop 4 — Weekly KB conflict digest

- Conflict detector reads KB on a weekly schedule (demoted from daily per premortem)
- Finds entries that disagree on the same fact type within the same domain
- Proposes which entry should be canonical (with reasoning)
- Slack digest to CS, one-click resolution per conflict
- Resolution = commit removing or marking-stale the loser

### 5.5 Loop 5 — External sentiment benchmarking (BONUS)

```
Weekly theme clusters → AI orchestrator (Minimax) generates --plan.json per theme
                              │
                              ▼
              python last30days.py "<theme>" --plan plan.json --emit json
                              │
                              ▼
              External report cached in external-intel/YYYY-MM/<theme>.json
                              │
                              ▼
              Comparison agent (Kimi): internal frequency vs external frequency
                              │
                              ▼
              Verdict appended to monthly brief:
                "Boldr-specific concern" | "Market-wide signal — capitalise"
                + suggested action (product page edit, campaign angle, etc.)
```

**Three minimum themes compared:** BPA-free straps, vegan straps, sustainability (carbon-neutral shipping). Two minimum external sources via last30days defaults (web + Reddit-via-Brave; ScrapeCreators if available enables deeper Reddit comment scrape).

### 5.6 Loop 6 — Brand voice (deprioritised in MVP)

Architecture-only in MVP. Captures `diff(sent, draft)` from Gmail; weekly analyser proposes `_schema.md` updates; human approves. Mentioned on the "one primitive, five loops" architecture slide; not live-demoed.

---

## 6. Human-in-the-Loop Surfaces

| Pinch point | Surface | Rationale |
|---|---|---|
| Reply approval (Loop 1) | **Gmail Drafts** | Zero context switch — CS team already in Gmail |
| Gap resolution conversation | **Slack thread** | Natural async conversation surface |
| KB entry approval | **Slack interactive card** | Inline diff view, Approve/Edit/Reject buttons |
| Persona proposal review | **Slack interactive card** | Same pattern, low urgency |
| Weekly conflict digest | **Slack daily message** | Batched, low-friction |
| Schema voice changes | **Email weekly digest** | Lowest urgency |
| **State viewing** (KB list, gap log, briefs) | **Read-only Next.js dashboard** | Single source of truth for "what's the system's state?" |

**Critical design choice:** the CS team never opens GitHub. All approvals route through Slack/Gmail/email. n8n commits to Git on the human's behalf with a descriptive commit message including approver, timestamp, and source. Git is invisible storage; the audit trail is preserved without UX friction.

---

## 7. Model Routing

API plan keys: Kimi 2.6 (Opus-tier reasoning), Minimax 2.7 (Sonnet-tier).

| Component | Model | Reason |
|---|---|---|
| Wiki-traversal agent (live path) | Minimax | Hot path, latency-sensitive, frequent |
| Gap-detection structured output | Minimax | Same call as traversal |
| Clarification-question drafting | Minimax | Lightweight |
| Auto-draft new KB entry | Minimax | Voice-matching is well within Sonnet-tier |
| Cold-start persona discovery | Kimi | Hardest reasoning task, runs once per brand |
| Persona-drift detector | Minimax | Pattern matching on clusters |
| Weekly theme clusterer | Minimax | Mechanical |
| Monthly marketing brief | Kimi | Strategic, exec-facing, runs monthly |
| Weekly KB conflict detector | Kimi | Subtle contradictions need depth |
| External sentiment query planner | Minimax | Structured `--plan.json` generation |
| Internal-vs-external comparison verdict | Kimi | Cross-data reasoning, judge-facing |
| LLM-as-judge (eval) | Kimi | Rubric application needs reliability |

**Principle:** Minimax for the hot/frequent path, Kimi for strategic/rare/eval. Both via OpenAI-compatible API; integrate through n8n HTTP node with custom base URLs.

---

## 8. Evaluation Strategy

### 8.1 Longitudinal replay harness (headline proof)

The single most important artefact. Demonstrates "self-improving" *quantitatively*.

```python
# eval/replay_harness.py

# 1. Start with EMPTY kb/faqs/, only kb/rate-cards/ + kb/products/ seeded
# 2. Replay 70 tickets in chronological order
# 3. For each ticket:
#    - Run the full pipeline
#    - Record can_answer_fully? (bool)
#    - If gap: simulate gap-resolution using the pre-labels in the original CSV
#      (which were stripped from agent input) — auto-commit synthetic KB entry
#    - Record git SHA at each commit
# 4. Plot answer-rate over time with annotations
```

**Output:**
- `eval/curve.png` — answer rate over ticket index, with Git SHA annotations at each KB-growth event
- `eval/curve_data.csv` — raw data, publishable
- `eval/quality_curve.png` — second curve: LLM-as-judge quality score over time

**Provenance overlays in the video:** show terminal generating the curve live, scroll the git log alongside, include 2-3 non-monotonic dips where a wrong KB entry was superseded (these are real — they validate the curve isn't smoothed).

### 8.2 Quality eval — hand-rate + LLM-judge

- Submitter hand-rates 20 drafts on a 1-5 rubric (5 dimensions: grounded, brand_voice, completeness, no_hallucination, tone_fit). Named reviewer credited in `docs/EVAL.md`.
- LLM-as-judge (Kimi) rates remaining 50 against the same rubric
- Calibration check: rerun LLM-judge on the 20 hand-rated drafts, report agreement percentage between human and LLM scores
- **Rubric published** in `eval/rubric.md` for transparency

### 8.3 Pre-labeled ground truth from dummy data

The dummy `01_customer_tickets.csv` includes labels (`question_type`, `buyer_persona`, `answered_by_kb`, `requires_escalation`). These columns are **stripped before passing to the agent** but kept as held-out ground truth. Per-class accuracy reported in `docs/EVAL.md`:

- Theme classification accuracy vs `question_type`
- Persona classification accuracy vs `buyer_persona`
- Gap-detection precision/recall vs `answered_by_kb`
- Escalation accuracy vs `requires_escalation`

### 8.4 Eval discipline

- Two-tab Google Sheet for demo: `tickets_input` (agent reads), `eval_labels` (eval reads). Prevents label leakage.
- The replay harness has a deterministic seed.
- All curve data published; nothing is "trust me."

---

## 9. Demo / Video Strategy

### 9.1 Format

Recorded video, ≤ 5 minutes (target 4:30), produced with Hyperframes + a video-editing AI agent. User records workflow screen-captures and voice-over. Storyboard locked in `video/storyboard.md`.

### 9.2 Seven-beat storyboard (locked)

| Beat | Time | Content | Recorded by user |
|---|---|---|---|
| 1. Cold open | 0:00–0:15 | Inbox-pileup montage, ticket counter ticking, title card | No (AI-generated) |
| 2. Problem framing | 0:15–0:45 | Google Sheet of 70 tickets, theme highlights | Yes (screen-capture) |
| 3. Hero loop demo | 0:45–2:15 | Sheet row → traversal → gap → Slack resolve → KB commit → second ticket auto-answered | Yes (5 sub-recordings) |
| 4. Architecture | 2:15–3:00 | Animated "one primitive, five loops" diagram + sentiment loop sub-beat | No (AI-animated) |
| 5. Longitudinal proof | 3:00–4:00 | Terminal running replay harness, curve rendering with Git SHA overlay | Yes (terminal recording) |
| 6. Scalability | 4:00–4:30 | Architecture diagram morphing across brand types | No (AI animation) |
| 7. Close | 4:30–4:45 | Boldr logo, repo URL held 5 full seconds | No |

### 9.3 Production polish (per premortem v2)

- Screen recording native 2x retina, exported 1080p
- VO: USB condenser mic or Fiverr ($30-80 budget)
- Burned captions (auto via Descript/CapCut + manual fix)
- One royalty-free track ducked -18dB under VO
- Full edit day budgeted

### 9.4 Handout (where technical depth lives)

- `README.md` — submission entry point with repo tour
- `docs/ARCHITECTURE.md` — full technical depth (everything we'd say in Q&A)
- `docs/EVAL.md` — evaluation methodology + numbers
- `docs/ROADMAP.md` — future work (qmd, Shopify Admin API, live IG/WhatsApp, multi-language)
- Optional 90-second appendix video on traversal-agent internals, linked from video description

---

## 10. Demo Data Pipeline

The Google Sheet is the **primary demo intake**, framed in the narrative as an upgrade of SOP §6 "New Questions Log" — turning the team's existing manual habit into the active system input.

### 10.1 Sheet setup

- Import `data/01_customer_tickets.csv` as a Google Sheet
- **Tab 1: `tickets_input`** — columns the agent sees (`ticket_id`, `received_at`, `channel`, `customer_name`, `subject`, `body`)
- **Tab 2: `eval_labels`** — held-out columns (`question_type`, `buyer_persona`, `answered_by_kb`, `requires_escalation`) used only by the eval harness
- n8n Google Sheets trigger watches Tab 1 for new rows

### 10.2 KB seeding

- FAQ PDF parsed into `kb/faqs/<slug>.md` (28 entries from the existing FAQ doc)
- Rate cards converted to `kb/rate-cards/{engraving,servicing}.md`
- Product reference docx parsed into `kb/products/<sku>.md`
- SOP §5 (brand voice) + §7 (escalation) extracted to `kb/_schema.md` and `kb/policies/escalation.md`
- Index `kb/index.md` hand-written initially, then auto-maintained

### 10.3 Replay harness data

- Uses the same 70 tickets
- Starts with empty `kb/faqs/`, seeded only with rate-cards + products
- Pre-labels from CSV used to simulate "human resolved this gap" automatically during the replay
- Real LLM calls are made; resulting commits are real git commits in a temporary branch

---

## 11. Tech Stack Summary

| Layer | Tool | Reason |
|---|---|---|
| Orchestration | n8n (self-hosted) | Open-source, brief-aligned, CS team can inspect |
| KB storage | Markdown in Git | Versioned, diffable, portable, auditable |
| Channel adapters | n8n Google Sheets / Gmail / (stubs) | Native triggers |
| LLM reasoning | Kimi 2.6, Minimax 2.7 | Plan keys available, OpenAI-compatible |
| HITL primitive | n8n `Wait for Webhook` | Same primitive across every loop |
| Dashboard | Next.js (read-only) | State viewer, not action surface |
| External sentiment | `last30days` CLI (3.0.5 vendored) | Already installed, supports `--plan.json` |
| Evaluation | Python `replay_harness.py` + matplotlib | Reproducible |
| Auto-commit | n8n GitHub API node | Behind-the-scenes audit trail |
| Notifications | Slack interactive + email digest | Where the team already is |

---

## 12. Risk Register & Mitigations

Top risks from premortems v1 and v2, with mitigations baked into the design:

| Risk | Mitigation |
|---|---|
| Curve looks fabricated | Show terminal generating it; Git SHA overlay; 2-3 non-monotonic dips; publish raw data |
| First 15s doesn't hook | Cold open with ticket-counter pileup (Beat 1); problem stated by 0:20 |
| 5-min overrun | Storyboard locked with second-level timestamps; target 4:30; non-negotiable beats identified |
| Hero-only undersells thesis | "One primitive, five loops" animated diagram in Beat 4; sentiment loop gets dedicated 25-30s |
| Production polish gap | Native-res capture, USB mic, burned captions, music, full edit day |
| Wiki traversal slow at scale | qmd nav-accelerator on roadmap; MVP KB is small |
| Answer rate ≠ quality | Second metric (LLM-judge + hand-rated) shown alongside answer-rate curve |
| Persona drift false positives | Threshold 3 tickets in 6 weeks; can tune up to 5/2-weeks if noisy |
| Slack approval fatigue | Batch low-urgency approvals (conflicts, persona) into daily/weekly digests |
| Markdown merge conflicts | Serialise n8n commits through a single queue node |
| `supersedes` not honoured | Status field `active|stale|draft`; agent prompt explicitly filters stale |

---

## 13. Future Roadmap (post-hackathon)

Explicitly out of MVP, included in `docs/ROADMAP.md` and the architecture slide:

- **qmd nav-accelerator** — when KB exceeds ~200 entries, integrate qmd MCP server for BM25 + embedding pre-ranking
- **Live Instagram + WhatsApp** — Meta app review, WhatsApp Business onboarding
- **Real Shopify Admin API** — order-status lookup (SOP §3), inventory signal feeding persona weighting
- **Multi-language** — Singlish, Bahasa, Mandarin detection + brand-voice variants
- **Brand-voice loop activated** — capture diff(sent, draft), weekly analyser, schema updates
- **PII redaction layer** — for production deployment
- **Per-brand `_schema.md` cold-start onboarding wizard** — for "deploys to your brand in a week" claim

---

## 14. Open Items Before Implementation

None blocking. All design decisions resolved across the brainstorming sessions. Implementation plan to be created via `superpowers:writing-plans`.

The implementation phasing will cover:
1. Repo + KB seeding (parse provided data into structured markdown)
2. n8n workflow scaffold + Google Sheet trigger + Common Event Schema
3. Wiki-traversal agent + structured output contract
4. Gmail Drafts integration + reply path
5. Gap loop + Slack interactive approval
6. Auto-commit to Git via n8n GitHub node
7. Replay harness + curve generation
8. Quality eval (hand-rate + LLM-judge)
9. Persona discovery + drift detector
10. Theme clusterer + monthly brief
11. External sentiment loop (last30days `--plan.json` orchestration)
12. Read-only Next.js dashboard
13. Video production: recording, VO, editing
14. Handout repo + README + ARCHITECTURE.md + EVAL.md + ROADMAP.md

---

## Appendix A: Brand Voice Contract (excerpt)

To be expanded in `kb/_schema.md`. Seed values:

**Openers (preferred):** `Yes.` `No.` `Hi [Name], thanks for reaching out — happy to help with that.`
**Openers (forbidden):** `Great question!` `Dear Sir/Madam` `I hope this email finds you well`
**Tone:** Declarative, confident, technical-but-accessible. Lead with the answer, then evidence.
**Sentence length:** 15–25 words typical. Avoid run-ons.
**Currency:** `SGD 85`, never `$85` or `S$85`.
**Standards cited:** ISO 3157, EU REACH, RoHS, Grade 5 Ti — when relevant, by exact name.
**Punctuation:** Em-dashes liberal. No emoji. No exclamation marks.
**Per-channel:**
- Email: full template (Hi/sign-off)
- IG DM: terser, no formal sign-off
- WhatsApp: shortest, single paragraph preferred

---

## Appendix B: Glossary

| Term | Definition |
|---|---|
| **Hero loop** | Gap → KB loop, the primary self-improving flow demoed in the video |
| **Common Event Schema** | The normalised ticket shape all channel adapters produce |
| **HITL primitive** | n8n `Wait for Webhook` node — same shape across every approval pinch point |
| **Wiki traversal** | Karpathy-style retrieval pattern: agent reads `index.md`, drills into files |
| **Nav accelerator** | (Future) qmd-based BM25+embedding pre-ranking to keep traversal fast at scale |
| **Domain hierarchy** | Per-fact-type canonical source policy (pricing → rate card, policy → SOP, etc.) |
| **Cold-start persona discovery** | One-time pass on historical tickets to seed `kb/personas/` at deployment |
| **Persona drift** | Steady-state detection of unmatched tickets triggering new-persona proposals |
| **Replay harness** | Deterministic eval that replays N tickets with growing KB, producing the answer-rate curve |
| **Provenance overlay** | Git SHA + commit metadata shown alongside the curve to prove non-fabrication |

---

*End of design spec. Ready for `superpowers:writing-plans` invocation upon user approval.*
