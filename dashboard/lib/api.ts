import type {
  BriefSummary,
  Gap,
  KbEntry,
  Persona,
  SentimentRow,
  ThemeReport,
} from "./types";

const BASE = process.env.INTEL_ENGINE_URL || "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    cache: "no-store",
    headers: { accept: "application/json" },
  });
  if (!res.ok) {
    throw new Error(
      `Intel engine ${path} returned ${res.status}: ${await res.text()}`
    );
  }
  return (await res.json()) as T;
}

export async function fetchKb(): Promise<{ entries: KbEntry[]; count: number }> {
  return get("/kb/summary");
}
export async function fetchGaps(): Promise<{ gaps: Gap[] }> {
  return get("/gaps/list");
}
export async function fetchPersonas(): Promise<{ personas: Persona[] }> {
  return get("/personas/list");
}
export async function fetchThemes(): Promise<{ reports: ThemeReport[] }> {
  return get("/themes/list");
}
export async function fetchBriefs(): Promise<{ briefs: BriefSummary[] }> {
  return get("/briefs/list");
}
export async function fetchSentiment(): Promise<{ reports: SentimentRow[] }> {
  return get("/sentiment/list");
}
