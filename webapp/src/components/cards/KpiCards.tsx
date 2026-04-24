import { HardDrive, LineChart, MemoryStick, ShieldCheck } from "lucide-react";
import type { DashboardPayload } from "../../services/api";

type Props = { payload: DashboardPayload };

export function KpiCards({ payload }: Props) {
  const activeDevicePreview = payload.devices.connected
    .slice(0, 3)
    .map((d) => d.device_name || d.device_id)
    .join(", ");
  const cards = [
    {
      label: "RAM Usage",
      value: `${payload.metrics.ram_now_percent.toFixed(2)}%`,
      icon: MemoryStick,
      hint: "Current memory pressure",
    },
    {
      label: "Predicted Memory",
      value: payload.metrics.predicted_ram_percent == null ? "N/A" : `${payload.metrics.predicted_ram_percent.toFixed(2)}%`,
      icon: LineChart,
      hint: "Near-future usage estimate",
    },
    {
      label: "Stability Score",
      value: `${payload.metrics.stability_score.toFixed(1)}/100`,
      icon: ShieldCheck,
      hint: "Overall memory health",
    },
    {
      label: "Active Devices",
      value: String(payload.metrics.connected_devices),
      icon: HardDrive,
      hint: activeDevicePreview ? `Connected: ${activeDevicePreview}` : "No devices connected",
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
          </article>
        );
      })}
    </section>
  );
}
