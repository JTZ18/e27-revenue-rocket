# Persona Drift Detector

You receive (a) the current active persona taxonomy and (b) tickets from the
last 6 weeks. Decide which tickets DO NOT match any active persona's signals,
then propose new personas or extensions when a cluster of ≥3 unmatched
tickets shares a topic.

## Output format

Return ONLY JSON — no prose, no code fences:

```json
{
  "unmatched_tickets": 5,
  "stale_candidates": ["slug_of_persona_that_no_longer_fires"],
  "proposals": [
    {
      "axis": "lifecycle | interest | behaviour",
      "slug": "snake_case_slug",
      "label": "Human label",
      "description": "1–2 sentences",
      "signals": ["keyword", "..."],
      "example_ticket_ids": ["TKT-1041", "TKT-1052", "TKT-1063"],
      "rationale": "Why this is distinct from existing personas."
    }
  ]
}
```

## Constraints

- Threshold for proposing a new persona: **≥3 unmatched tickets in 6 weeks**.
- `stale_candidates`: list slugs of personas whose signals didn't fire on any ticket in the window. Stale ≠ delete — humans review.
- Every proposal must include ≥3 `example_ticket_ids` from the input.
