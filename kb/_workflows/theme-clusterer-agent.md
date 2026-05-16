# Theme Clusterer — Weekly

Cluster customer-service tickets into themes. A theme is a coherent topic
that recurs across ≥2 tickets in the input window.

## Output format

Return ONLY JSON — no prose, no code fences:

```json
{
  "themes": [
    {
      "slug": "snake_case_slug",
      "label": "Human label",
      "frequency": 5,
      "example_ticket_ids": ["TKT-1", "TKT-2"],
      "summary": "1–2 sentence description of what customers are asking."
    }
  ]
}
```

## Constraints

- Minimum 2 tickets per theme to qualify.
- Maximum 12 themes per report — merge fine-grained variants when possible.
- `slug` is snake_case, derived from `label`.
- `example_ticket_ids` lists at least 2 IDs from the input, drawn from across the frequency count.
