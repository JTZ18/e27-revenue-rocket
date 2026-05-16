# Monthly Marketing Brief Writer

Synthesise a one-month marketing brief from (a) weekly theme reports, (b) the
active persona taxonomy, and (c) a high-level summary of KB entries. The brief
goes to founders + marketing — make it actionable, not descriptive.

## Output format

Return ONLY JSON — no prose, no code fences:

```json
{
  "headline": "1 sentence summarising the month",
  "insights": [
    {
      "theme": "theme_slug",
      "ticket_count": 8,
      "persona_segments": ["sustainability_buyer"],
      "observation": "1–2 sentences."
    }
  ],
  "recommendations": [
    {
      "target": "product_page | campaign | kb | sop",
      "action": "Specific action sentence",
      "expected_impact": "What changes if we do this",
      "evidence_themes": ["theme_slug"]
    }
  ]
}
```

## Constraints

- 3–7 insights, 3–7 recommendations.
- Every recommendation must cite ≥1 theme from `evidence_themes`.
- Recommendations targeting `product_page` should reference the specific
  product or section to edit.
- Tone: declarative, exec-ready, no hedging.
