import type { DashboardPayload } from "../services/api";
import { KpiCards } from "../components/cards/KpiCards";
import { MemoryUsageChart, PredictionChart } from "../components/charts/Charts";

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

  return (
    <div className="page-grid">
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
        <MemoryUsageChart rows={memoryRows} />
        <PredictionChart rows={predictionRows} showPredicted={showPredicted} showActual={showActual} />
      </div>
    </div>
  );
}
