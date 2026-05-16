# Quality Rubric — Customer Intelligence Engine Drafts

Each draft is scored on **5 dimensions**, each on a **1–5 integer scale**.
The same rubric is used by the human reviewer (20 drafts) and the LLM-as-judge
(remaining 50 drafts + the 20 hand-rated drafts, for calibration).

## Dimensions

### 1. Grounded (1–5)
Every factual claim in the draft is supported by an entry in the KB the agent
cited (`pages_read`). 5 = every claim cited; 1 = invents facts.

### 2. Brand voice (1–5)
Adheres to `kb/_schema.md`: declarative openers (`Yes.`/`No.`), no forbidden
openers (`Great question!`), em-dashes ok, `SGD XX` currency, no emoji.
5 = indistinguishable from canonical FAQ; 1 = wrong register throughout.

### 3. Completeness (1–5)
Answers the customer's actual question, not a tangent. 5 = answer + relevant
caveats; 3 = answers but misses a sub-question; 1 = off-topic.

### 4. No hallucination (1–5)
Strict factual check. 5 = zero unsupported claims; 1 = contains at least one
fabricated fact (price, material, policy). Note: this is stricter than #1 —
a claim can be "uncited but true" (4 on grounded, 5 on no_hallucination) or
"cited but the cited entry says something else" (1 on both).

### 5. Tone fit (1–5)
Matches the channel and customer affect. 5 = right register for email vs IG
DM vs WhatsApp; 1 = wrong register (e.g. terse text-speak in a formal email).

## Aggregate score
`overall = mean(grounded, brand_voice, completeness, no_hallucination, tone_fit)` — rounded to 2 dp.

## Output format (both human and LLM judge)
```csv
ticket_id,grounded,brand_voice,completeness,no_hallucination,tone_fit,notes
```
