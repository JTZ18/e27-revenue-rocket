export type KbEntry = {
  path: string;
  domain: string;
  title: string;
  excerpt: string;
};

export type Gap = {
  gap_id: string;
  source_event_id: string;
  customer_question: string;
  missing_info: string[];
  themes_detected: string[];
  persona_hints: string[];
  status: "open" | "resolved" | "dismissed";
  drafted_kb_slug: string | null;
  resolved_at: string | null;
};

export type Theme = {
  slug: string;
  label: string;
  frequency: number;
  example_ticket_ids: string[];
  summary: string;
};

export type ThemeReport = {
  week_end: string;
  markdown: string;
};

export type Persona = {
  axis: "lifecycle" | "interest" | "behaviour";
  slug: string;
  label: string;
  description: string;
  signals: string[];
  status: "active" | "stale" | "draft";
};

export type BriefSummary = {
  month: string;
  path: string;
  markdown: string;
};

export type SentimentRow = {
  month: string;
  theme_slug: string;
  topic: string;
  external_mentions: number;
  internal_frequency: number;
  verdict: "boldr_specific" | "market_wide" | "aligned" | "insufficient_data";
  reasoning: string;
  suggested_action: string;
  top_sources: string[];
  ran_at: string;
};
