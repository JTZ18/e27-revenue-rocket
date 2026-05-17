import { fetchGaps } from "@/lib/api";

export default async function GapsPage() {
  const { gaps } = await fetchGaps();
  const open = gaps.filter((g) => g.status === "open");
  const resolved = gaps.filter((g) => g.status !== "open");

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Gaps</h1>
      <section className="mb-8">
        <h2 className="text-lg font-medium mb-2">Open ({open.length})</h2>
        <ul className="space-y-3">
          {open.map((g) => (
            <li key={g.gap_id} className="rounded border border-[var(--color-border)] bg-[var(--color-card)] p-4">
              <div className="text-xs text-[var(--color-muted)]">{g.gap_id}</div>
              <div className="font-medium mt-1">{g.customer_question}</div>
              <div className="text-sm mt-2">
                <span className="text-[var(--color-muted)]">Missing:</span> {g.missing_info.join(", ") || "—"}
              </div>
              <div className="text-sm">
                <span className="text-[var(--color-muted)]">Themes:</span> {g.themes_detected.join(", ") || "—"}
              </div>
            </li>
          ))}
          {open.length === 0 && <li className="text-sm text-[var(--color-muted)]">No open gaps.</li>}
        </ul>
      </section>
      <section>
        <h2 className="text-lg font-medium mb-2">Resolved ({resolved.length})</h2>
        <ul className="space-y-2">
          {resolved.map((g) => (
            <li key={g.gap_id} className="rounded border border-[var(--color-border)] bg-[var(--color-card)] p-3 text-sm">
              <div className="font-medium">{g.customer_question}</div>
              <div className="text-xs text-[var(--color-muted)] mt-1">
                {g.resolved_at ?? "?"} · drafted KB: {g.drafted_kb_slug ?? "—"}
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
