import type { DashboardPayload } from "../services/api";

export type SystemStatusTone = "stable" | "warning" | "critical";

/** Product-level headline + guidance derived from risk, RAM, and stability (no new metrics). */
export function getSystemStatus(payload: DashboardPayload): {
  tone: SystemStatusTone;
  headline: string;
  detail: string;
} {
  const level = (payload.metrics.risk_level || "NORMAL").toUpperCase();
  const ram = payload.metrics.ram_now_percent;
  const stab = payload.metrics.stability_score;
  const live = payload.metrics.pipeline?.running;

  if (level === "CRITICAL" || level === "EMERGENCY") {
    return {
      tone: "critical",
      headline: "Critical state",
      detail: `Memory pressure is elevated (${ram.toFixed(1)}% RAM) with ${level} risk and stability at ${stab.toFixed(0)}/100. If sustained, interactive performance may suffer—use the Analysis page and prioritized actions to relieve pressure.`,
    };
  }
  if (level === "WARNING" || stab < 62) {
    return {
      tone: "warning",
      headline: "Warning detected",
      detail: `Signals merit attention (${level}): ${ram.toFixed(1)}% RAM, stability ${stab.toFixed(0)}/100. This is not an emergency by itself, but trends and device churn should be watched before load increases.${live ? " Live collection is running." : ""}`,
    };
  }
  return {
    tone: "stable",
    headline: "System stable",
    detail: `Memory posture looks healthy (${ram.toFixed(1)}% RAM) with stability ${stab.toFixed(0)}/100. ${live ? "Telemetry pipeline is active" : "Pipeline is idle"}—continue monitoring; no immediate action required.`,
  };
}
