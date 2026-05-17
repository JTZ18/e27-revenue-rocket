# Internal vs External Sentiment Comparator

Compare one Boldr theme (with its internal ticket frequency) against the recent
external chatter for the same topic (mention count, top sources, snippets).
Produce a one-paragraph verdict and a concrete suggested action.

## Output format

Return ONLY JSON — no prose, no code fences:

```json
{
  "verdict": "boldr_specific | market_wide | aligned | insufficient_data",
  "reasoning": "2–4 sentences explaining how internal frequency relates to external mentions and source mix.",
  "suggested_action": "One concrete brand action: product-page edit, campaign angle, KB entry, or SOP update."
}
```

## Verdict rubric

- `market_wide` — external mentions clearly dominate internal frequency; the
  topic is hot in the wider market and Boldr should capitalise.
- `boldr_specific` — internal frequency clearly dominates external mentions;
  this is a niche concern unique (or near-unique) to Boldr's customers.
- `aligned` — internal and external signals are comparable in scale.
- `insufficient_data` — fewer than 3 external mentions AND fewer than 3
  internal occurrences. Do not invent a verdict from nothing.

## Action constraints

- 1 sentence, declarative, brand-team-actionable.
- Reference the theme by name; reference a specific surface (PDP, campaign,
  KB entry, SOP §X) where relevant.
- No hedging language ("might", "could", "perhaps"). Pick a direction.
