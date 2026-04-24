import type { DashboardPayload } from "../services/api";

export type ChartStory = { what: string; why: string; next: string };

export function getGraphInsight(payload: DashboardPayload, key: keyof NonNullable<DashboardPayload["analysis"]["graph_insights"]>): ChartStory | null {
  const g = payload.analysis.graph_insights;
  if (!g) return null;
  const block = g[key];
  if (!block || typeof block.what !== "string") return null;
  return block as ChartStory;
}

export function getSpikeTimestamps(payload: DashboardPayload): string[] {
  const ts = payload.analysis.memory_patterns?.spike_timestamps;
  return Array.isArray(ts) ? ts.filter((t): t is string => typeof t === "string") : [];
}
