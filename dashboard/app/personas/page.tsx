import { fetchPersonas } from "@/lib/api";
import type { Persona } from "@/lib/types";

export default async function PersonasPage() {
  const { personas } = await fetchPersonas();
  const byAxis = new Map<string, Persona[]>();
  for (const p of personas) {
    if (!byAxis.has(p.axis)) byAxis.set(p.axis, []);
    byAxis.get(p.axis)!.push(p);
  }
  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Personas</h1>
      {Array.from(byAxis.entries()).map(([axis, list]) => (
        <section key={axis} className="mb-6">
          <h2 className="text-lg font-medium capitalize mb-2">{axis}</h2>
          <ul className="space-y-3">
            {list.map((p) => (
              <li key={p.slug} className="rounded border border-[var(--color-border)] bg-[var(--color-card)] p-4">
                <div className="font-medium">{p.label} <span className="text-xs text-[var(--color-muted)]">/{p.slug}</span></div>
                <div className="text-sm mt-1">{p.description}</div>
                <div className="text-xs text-[var(--color-muted)] mt-2">Signals: {p.signals.join(", ")}</div>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
