import { fetchSentiment } from "@/lib/api";

const VERDICT_COLOUR: Record<string, string> = {
  market_wide: "text-orange-400",
  boldr_specific: "text-sky-400",
  aligned: "text-emerald-400",
  insufficient_data: "text-zinc-400",
};

export default async function SentimentPage() {
  const { reports } = await fetchSentiment();
  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">External Sentiment</h1>
      {reports.length === 0 && <p className="text-sm text-[var(--color-muted)]">No sentiment reports yet.</p>}
      <ul className="space-y-4">
        {[...reports].reverse().map((r) => (
          <li key={`${r.month}-${r.theme_slug}`} className="rounded border border-[var(--color-border)] bg-[var(--color-card)] p-4">
            <div className="flex items-baseline justify-between">
              <h2 className="text-lg font-medium">{r.theme_slug}</h2>
              <span className={`text-xs uppercase tracking-wide ${VERDICT_COLOUR[r.verdict] ?? ""}`}>{r.verdict}</span>
            </div>
            <div className="text-xs text-[var(--color-muted)] mt-1">{r.month} · ran {r.ran_at}</div>
            <div className="text-sm mt-2">{r.reasoning}</div>
            <div className="text-sm mt-2">
              <span className="text-[var(--color-muted)]">Internal:</span> {r.internal_frequency} ·{" "}
              <span className="text-[var(--color-muted)]">External:</span> {r.external_mentions}
            </div>
            <div className="text-sm mt-2">
              <span className="text-[var(--color-muted)]">Suggested action:</span> {r.suggested_action}
            </div>
            <div className="text-xs text-[var(--color-muted)] mt-2">Sources: {r.top_sources.join(", ") || "—"}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}
