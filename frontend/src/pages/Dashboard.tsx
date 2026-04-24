import type { DashboardPayload } from "../services/api";
import { KpiCards } from "../components/cards/KpiCards";
import { MemoryUsageChart, PredictionChart } from "../components/charts/Charts";
import { getGraphInsight, getSpikeTimestamps } from "../utils/chartInsights";
import { getSystemStatus } from "../utils/systemStatus";

type Props = {
  payload: DashboardPayload;
  showPredicted: boolean;
  showActual: boolean;
  setShowPredicted: (v: boolean) => void;
  setShowActual: (v: boolean) => void;
};

export function DashboardPage({ payload, showPredicted, showActual, setShowPredicted, setShowActual }: Props) {
  const memoryRows = payload.trends.memory.slice(-80).map((r) => ({ ...r, ram_percent: Number(r.ram_percent) || 0, swap_percent: Number(r.swap_percent) || 0 }));
  const predictionRows = payload.trends.prediction
    .slice(-80)
    .map((r) => ({ ...r, predicted_ram_percent: Number(r.predicted_ram_percent) || 0, actual_ram_percent: Number(r.actual_ram_percent) || 0 }));
  const spikes = getSpikeTimestamps(payload);
  const status = getSystemStatus(payload);

  return (
    <div className="page-grid">
      <section className={`panel system-status-banner system-status-banner--${status.tone}`}>
        <div className="system-status-banner__row">
          <h2 className="system-status-banner__title">{status.headline}</h2>
          <span className={`risk-badge system-status-badge ${payload.metrics.risk_level.toLowerCase()}`}>{payload.metrics.risk_level}</span>
        </div>
        <p className="system-status-banner__detail">{status.detail}</p>
      </section>
      <section className="panel">
        <h2>Command Center</h2>
        <p className="panel-copy">
          Live memory posture, forecast quality, and spike context in one place. Use chart insights below to understand what changed, why it matters, and what to watch next.
        </p>
      </section>
      <section className="panel">
        <h2>Chart Controls</h2>
        <div className="switch-row">
          <label>
            <input type="checkbox" checked={showPredicted} onChange={(e) => setShowPredicted(e.target.checked)} /> Predicted line
          </label>
          <label>
            <input type="checkbox" checked={showActual} onChange={(e) => setShowActual(e.target.checked)} /> Actual line
          </label>
        </div>
      </section>
      <KpiCards payload={payload} />
      <div className="two-col">
        <MemoryUsageChart rows={memoryRows} spikeTimestamps={spikes} insight={getGraphInsight(payload, "memory")} />
        <PredictionChart rows={predictionRows} showPredicted={showPredicted} showActual={showActual} insight={getGraphInsight(payload, "prediction")} />
      </div>
    </div>
  );
}
