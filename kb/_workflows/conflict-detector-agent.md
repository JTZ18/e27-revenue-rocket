# KB Conflict Detector — Weekly

Scan the KB for entries that disagree on the same fact within the same
domain. Propose which entry should be canonical based on the domain hierarchy
in `kb/_schema.md`:

| Fact type | Canonical domain |
|---|---|
| Service prices | `pricing` (rate cards) |
| Process / escalation | `policy` (SOP) |
| Product specs / materials | `spec` (product reference) |
| Consumer-facing answers | `faq` |

## Output format

Return ONLY JSON — no prose, no code fences:

```json
{
  "conflicts": [
    {
      "domain": "pricing | policy | spec | faq",
      "fact_topic": "1-line description of the disputed fact",
      "entries": ["kb/path/a.md", "kb/path/b.md"],
      "canonical_proposal": "kb/path/that_should_win.md",
      "reasoning": "Why this entry should win (cite the domain hierarchy)."
    }
  ]
}
```

## Constraints

- Only flag genuine factual disagreements (not paraphrasing differences).
- Cross-domain conflicts ARE in scope and follow the hierarchy above.
- Same-domain conflicts go to humans for resolution.
- If no conflicts found, return `{"conflicts": []}`.
