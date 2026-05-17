import { fetchBriefs } from "@/lib/api";

export default async function BriefsPage() {
  const { briefs } = await fetchBriefs();
  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Monthly Marketing Briefs</h1>
      {briefs.length === 0 && <p className="text-sm text-[var(--color-muted)]">No briefs yet.</p>}
      <div className="space-y-6">
        {[...briefs].reverse().map((b) => (
          <article key={b.month} className="rounded border border-[var(--color-border)] bg-[var(--color-card)] p-4">
            <h2 className="text-lg font-medium mb-2">{b.month}</h2>
            <pre className="whitespace-pre-wrap text-sm font-mono">{b.markdown}</pre>
          </article>
        ))}
      </div>
    </div>
  );
}
