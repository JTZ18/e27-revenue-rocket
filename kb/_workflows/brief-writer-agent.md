# Monthly Marketing Brief Writer

Synthesise a one-month marketing brief from (a) weekly theme reports,
(b) the active persona taxonomy, (c) external sentiment verdicts produced
by last30days for the month's top themes, and (d) a high-level summary of
KB entries. The brief goes to founders + marketing — make it actionable,
not descriptive.

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
      "observation": "1–2 sentences. If external sentiment exists for this theme, mention the verdict (market_wide / boldr_specific / aligned)."
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
- A theme with verdict `market_wide` should be prioritised in
  recommendations (capitalise on broader market signal); a theme with
  verdict `boldr_specific` should be addressed via KB/SOP rather than a
  campaign.
- Tone: declarative, exec-ready, no hedging.
