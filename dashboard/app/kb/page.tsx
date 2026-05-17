import { fetchKb } from "@/lib/api";
import type { KbEntry } from "@/lib/types";

export default async function KBPage() {
  const { entries } = await fetchKb();
  const byDomain = new Map<string, KbEntry[]>();
  for (const e of entries) {
    if (!byDomain.has(e.domain)) byDomain.set(e.domain, []);
    byDomain.get(e.domain)!.push(e);
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Knowledge Base</h1>
      <p className="text-sm text-[var(--color-muted)] mb-6">{entries.length} active entries.</p>
      <div className="space-y-6">
        {Array.from(byDomain.entries()).map(([domain, list]) => (
          <section key={domain}>
            <h2 className="text-lg font-medium capitalize mb-2">{domain} ({list.length})</h2>
            <ul className="space-y-2">
              {list.map((e) => (
                <li key={e.path} className="rounded border border-[var(--color-border)] bg-[var(--color-card)] p-3">
                  <div className="font-medium">{e.title}</div>
                  <div className="text-xs text-[var(--color-muted)]">{e.path}</div>
                  <div className="text-sm mt-2 line-clamp-3">{e.excerpt}</div>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}
