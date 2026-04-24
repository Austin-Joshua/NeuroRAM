import type { DashboardPayload } from "../services/api";
import { KpiCards } from "../components/cards/KpiCards";
import { MemoryUsageChart, PredictionChart } from "../components/charts/Charts";
import { getGraphInsight, getSpikeTimestamps } from "../utils/chartInsights";

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

  return (
    <div className="page-grid">
      <section className="panel">
        <h2>Command Center</h2>
        <p className="panel-copy">
          Real-time memory posture and device behavior in one view. Track pressure, forecast drift, and act before instability spreads.
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
