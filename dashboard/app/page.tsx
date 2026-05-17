import { fetchBriefs, fetchGaps, fetchKb, fetchPersonas, fetchSentiment } from "@/lib/api";

type Tile = { label: string; value: string | number; href: string };

export default async function Home() {
  let kb = { count: 0 };
  let gaps = { gaps: [] as { status: string }[] };
  let personas = { personas: [] as unknown[] };
  let briefs = { briefs: [] as { month: string }[] };
  let sentiment = { reports: [] as { month: string }[] };

  try {
    [kb, gaps, personas, briefs, sentiment] = await Promise.all([
      fetchKb(),
      fetchGaps(),
      fetchPersonas(),
      fetchBriefs(),
      fetchSentiment(),
    ]);
  } catch (err) {
    return (
      <div>
        <h1 className="text-2xl font-semibold mb-4">Status</h1>
        <p className="text-[var(--color-accent)]">
          Intel engine unreachable: {(err as Error).message}
        </p>
        <p className="text-sm text-[var(--color-muted)] mt-2">
          Start the API with <code>uv run uvicorn intel_engine.api:app --port 8000</code> and reload.
        </p>
      </div>
    );
  }

  const openGaps = gaps.gaps.filter((g) => g.status === "open").length;
  const latestBrief = briefs.briefs.at(-1)?.month ?? "—";
  const latestSentiment = sentiment.reports.at(-1)?.month ?? "—";

  const tiles: Tile[] = [
    { label: "KB entries", value: kb.count, href: "/kb" },
    { label: "Open gaps", value: openGaps, href: "/gaps" },
    { label: "Personas", value: personas.personas.length, href: "/personas" },
    { label: "Latest brief", value: latestBrief, href: "/briefs" },
    { label: "Latest sentiment", value: latestSentiment, href: "/sentiment" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Status</h1>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {tiles.map((t) => (
          <a
            key={t.label}
            href={t.href}
            className="block rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-5 hover:border-[var(--color-accent)] transition"
          >
            <div className="text-xs uppercase tracking-wide text-[var(--color-muted)]">{t.label}</div>
            <div className="text-3xl font-semibold mt-1">{t.value}</div>
          </a>
        ))}
      </div>
    </div>
  );
}
