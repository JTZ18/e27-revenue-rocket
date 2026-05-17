# Sentiment Query Planner

Given one weekly theme (slug + label + summary + example ticket snippets), produce
a JSON query plan that `last30days` will execute to measure how much the broader
web is talking about the same thing in the last 30 days.

## Output format

Return ONLY JSON — no prose, no code fences:

```json
{
  "topic": "Concise topic string used as the last30days search topic",
  "search_terms": ["term 1", "term 2", "term 3"],
  "subreddits": ["AskScience", "watches"],
  "related_handles": [],
  "notes": "1 sentence: why these terms/subs are the right read for this theme."
}
```

## Constraints

- `topic` ≤ 80 chars, no quotes, no trailing punctuation.
- 3–6 `search_terms`. Prefer the customer's actual phrasing, then a more technical alias.
- 0–6 `subreddits`. Skip if you cannot name a plausibly relevant subreddit.
- `related_handles` only if a known public expert/brand X handle is genuinely
  relevant to the theme. Default empty.
- Tone of `notes`: declarative, brand-team-facing.
