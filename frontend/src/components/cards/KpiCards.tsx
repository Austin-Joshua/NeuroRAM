import { HardDrive, LineChart, MemoryStick, ShieldCheck, TrendingDown, TrendingUp } from "lucide-react";
import type { DashboardPayload } from "../../services/api";

type Props = { payload: DashboardPayload };

export function KpiCards({ payload }: Props) {
  const activeDevicePreview = payload.devices.connected
    .slice(0, 3)
    .map((d) => d.device_name || d.device_id)
    .join(", ");
  const predictionDelta =
    payload.metrics.predicted_ram_percent == null ? null : payload.metrics.predicted_ram_percent - payload.metrics.ram_now_percent;
  const predictionConfidence =
    payload.analysis.memory_patterns.predicted_vs_actual_mae == null
      ? null
      : Number(Math.max(0, Math.min(100, 100 - payload.analysis.memory_patterns.predicted_vs_actual_mae * 8)).toFixed(1));
  const expectedTrend =
    predictionDelta == null ? "Stable" : predictionDelta > 1 ? "Increasing" : predictionDelta < -1 ? "Decreasing" : "Stable";
  const trendIcon = (label: string, trend: string) => {
    if (label === "Predicted Memory Usage (Next Interval)" && trend.includes("Increasing")) return <TrendingUp size={14} className="kpi-trend-icon up" aria-hidden />;
    if (label === "Predicted Memory Usage (Next Interval)" && trend.includes("Decreasing")) return <TrendingDown size={14} className="kpi-trend-icon down" aria-hidden />;
    if (label === "RAM Usage" && trend.includes("High")) return <TrendingUp size={14} className="kpi-trend-icon up" aria-hidden />;
    if (label === "Stability Score" && trend.includes("Needs")) return <TrendingDown size={14} className="kpi-trend-icon down" aria-hidden />;
    if (label === "Active Devices" && trend.includes("activity")) return <TrendingUp size={14} className="kpi-trend-icon up" aria-hidden />;
    return null;
  };

  const cards = [
    {
      label: "RAM Usage",
      value: `${payload.metrics.ram_now_percent.toFixed(2)}%`,
      icon: MemoryStick,
      hint: "Current memory pressure",
      trend: payload.metrics.ram_now_percent >= 80 ? "High pressure" : "Within target",
    },
    {
      label: "Predicted Memory Usage (Next Interval)",
      value: payload.metrics.predicted_ram_percent == null ? "N/A" : `${payload.metrics.predicted_ram_percent.toFixed(2)}%`,
      icon: LineChart,
      hint:
        predictionConfidence == null
          ? "Near-future memory estimate for the next cycle"
          : `Next cycle forecast · confidence ${predictionConfidence.toFixed(1)}%`,
      trend:
        predictionDelta == null
          ? "Expected Trend: Stable (model warming up)"
          : `Expected Trend: ${expectedTrend} (${predictionDelta >= 0 ? "+" : ""}${predictionDelta.toFixed(2)}%)`,
    },
    {
      label: "Stability Score",
      value: `${payload.metrics.stability_score.toFixed(1)}/100`,
      icon: ShieldCheck,
      hint: "Overall memory health",
      trend: payload.metrics.stability_score >= 70 ? "Stable state" : "Needs attention",
    },
    {
      label: "Active Devices",
      value: String(payload.metrics.connected_devices),
      icon: HardDrive,
      hint: activeDevicePreview ? `Connected: ${activeDevicePreview}` : "No devices connected",
      trend: payload.metrics.connected_devices > 0 ? "Device activity detected" : "No active devices",
    },
  ];

  return (
    <section className="kpi-grid">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <article className="kpi-card" key={card.label}>
            <div className="kpi-card-head">
              <Icon size={16} className="kpi-card-icon" aria-hidden />
              <p className="kpi-card-title">{card.label}</p>
            </div>
            <strong>{card.value}</strong>
            <span className="kpi-card-hint">{card.hint}</span>
            <span className="kpi-trend">
              {trendIcon(card.label, card.trend)}
              {card.trend}
            </span>
          </article>
        );
      })}
    </section>
  );
}
