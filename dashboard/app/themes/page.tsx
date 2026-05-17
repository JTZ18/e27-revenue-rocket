import { fetchThemes } from "@/lib/api";

export default async function ThemesPage() {
  const { reports } = await fetchThemes();
  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Weekly Theme Reports</h1>
      {reports.length === 0 && <p className="text-sm text-[var(--color-muted)]">No reports yet.</p>}
      <div className="space-y-6">
        {[...reports].reverse().map((r) => (
          <article key={r.week_end} className="rounded border border-[var(--color-border)] bg-[var(--color-card)] p-4">
            <h2 className="text-lg font-medium mb-2">Week ending {r.week_end}</h2>
            <pre className="whitespace-pre-wrap text-sm font-mono">{r.markdown}</pre>
          </article>
        ))}
      </div>
    </div>
  );
}
