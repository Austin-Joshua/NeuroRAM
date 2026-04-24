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
  const trendIcon = (label: string, trend: string) => {
    if (label === "Predicted Memory" && trend.includes("+")) return <TrendingUp size={14} className="kpi-trend-icon up" aria-hidden />;
    if (label === "Predicted Memory" && trend.includes("-")) return <TrendingDown size={14} className="kpi-trend-icon down" aria-hidden />;
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
      label: "Predicted Memory",
      value: payload.metrics.predicted_ram_percent == null ? "N/A" : `${payload.metrics.predicted_ram_percent.toFixed(2)}%`,
      icon: LineChart,
      hint: "Near-future usage estimate",
      trend: predictionDelta == null ? "Model warming up" : predictionDelta >= 0 ? `+${predictionDelta.toFixed(2)}% trend` : `${predictionDelta.toFixed(2)}% trend`,
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
            <p>
              <Icon size={14} /> {card.label}
            </p>
            <strong>{card.value}</strong>
            <span>{card.hint}</span>
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
