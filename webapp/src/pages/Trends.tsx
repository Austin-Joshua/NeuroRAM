import type { DashboardPayload } from "../services/api";
import { DeviceActivityChart, MemoryUsageChart, PredictionChart, StabilityChart } from "../components/charts/Charts";
import { getGraphInsight, getSpikeTimestamps } from "../utils/chartInsights";

type Props = {
  payload: DashboardPayload;
  showPredicted: boolean;
  showActual: boolean;
  setShowPredicted: (v: boolean) => void;
  setShowActual: (v: boolean) => void;
};

export function TrendsPage({ payload, showPredicted, showActual, setShowPredicted, setShowActual }: Props) {
  const memoryRows = payload.trends.memory.slice(-200).map((r) => ({ ...r, ram_percent: Number(r.ram_percent) || 0, swap_percent: Number(r.swap_percent) || 0 }));
  const predictionRows = payload.trends.prediction
    .slice(-200)
    .map((r) => ({ ...r, predicted_ram_percent: Number(r.predicted_ram_percent) || 0, actual_ram_percent: Number(r.actual_ram_percent) || 0 }));
  const stabilityRows = payload.trends.stability.slice(-200).map((r) => ({ ...r, stability_index: Number(r.stability_index) || 0 }));
  const deviceRows = payload.trends.device_activity.slice(-200).map((r) => ({
    ...r,
    active_devices: Number(r.active_devices) || 0,
    connected_events: Number(r.connected_events) || 0,
    disconnected_events: Number(r.disconnected_events) || 0,
  }));
  const spikes = getSpikeTimestamps(payload);
  return (
    <div className="page-grid">
      <section className="panel">
        <h2>Trend Intelligence</h2>
        <p className="panel-copy">Correlate memory movement, forecast quality, stability behavior, and external device events over time.</p>
      </section>
      <section className="panel">
        <h2>Trend View Controls</h2>
        <div className="switch-row">
          <label>
            <input type="checkbox" checked={showPredicted} onChange={(e) => setShowPredicted(e.target.checked)} /> Predicted line
          </label>
          <label>
            <input type="checkbox" checked={showActual} onChange={(e) => setShowActual(e.target.checked)} /> Actual line
          </label>
        </div>
      </section>
      <div className="two-col">
        <MemoryUsageChart rows={memoryRows} spikeTimestamps={spikes} insight={getGraphInsight(payload, "memory")} />
        <PredictionChart rows={predictionRows} showPredicted={showPredicted} showActual={showActual} insight={getGraphInsight(payload, "prediction")} />
      </div>
      <div className="two-col">
        <StabilityChart rows={stabilityRows} insight={getGraphInsight(payload, "stability")} />
        <DeviceActivityChart rows={deviceRows} insight={getGraphInsight(payload, "device_activity")} />
      </div>
    </div>
  );
}
