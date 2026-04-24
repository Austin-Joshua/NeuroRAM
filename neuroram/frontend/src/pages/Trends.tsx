import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import type { DashboardPayload } from "../services/api";
import { DeviceActivityChart, MemoryUsageChart, PredictionChart, StabilityChart } from "../components/charts/Charts";
import { getGraphInsight, getSpikeTimestamps } from "../utils/chartInsights";

type Props = {
  payload: DashboardPayload;
  refreshMs: number;
  showPredicted: boolean;
  showActual: boolean;
  setShowPredicted: (v: boolean) => void;
  setShowActual: (v: boolean) => void;
};

export function TrendsPage({ payload, refreshMs, showPredicted, showActual, setShowPredicted, setShowActual }: Props) {
  const [searchParams] = useSearchParams();
  const detailedReportRef = useRef<HTMLElement | null>(null);
  const [flashReport, setFlashReport] = useState(false);
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
  const shortMemoryRows = memoryRows.slice(-60);
  const shortPredictionRows = predictionRows.slice(-60);
  const [activeReport, setActiveReport] = useState<"memory" | "prediction" | "stability" | "device_activity">("memory");
  useEffect(() => {
    const focus = (searchParams.get("focus") ?? "").toLowerCase();
    if (focus === "memory" || focus === "prediction" || focus === "stability" || focus === "device_activity") {
      setActiveReport(focus);
    }
  }, [searchParams]);
  useEffect(() => {
    const focus = (searchParams.get("focus") ?? "").toLowerCase();
    if (focus && detailedReportRef.current) {
      requestAnimationFrame(() => {
        detailedReportRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
        setFlashReport(true);
        window.setTimeout(() => setFlashReport(false), 900);
      });
    }
  }, [searchParams, activeReport]);
  const activeInsight = getGraphInsight(payload, activeReport);
  const activeReportTitle = useMemo(() => {
    if (activeReport === "memory") return "Memory Trend Detailed Report";
    if (activeReport === "prediction") return "Prediction Detailed Report";
    if (activeReport === "stability") return "Stability Detailed Report";
    return "Device Impact Detailed Report";
  }, [activeReport]);
  const predictionDelta =
    payload.metrics.predicted_ram_percent == null ? null : payload.metrics.predicted_ram_percent - payload.metrics.ram_now_percent;
  const expectedTrend =
    predictionDelta == null ? "Stable" : predictionDelta > 1 ? "Increasing" : predictionDelta < -1 ? "Decreasing" : "Stable";

  return (
    <div className="page-grid">
      <section className="panel">
        <h2>Predictive Memory Trend Intelligence</h2>
        <p className="panel-copy">Correlate current memory behavior, predicted direction, stability risk, and external device impact over time.</p>
      </section>
      <section className="panel">
        <h2>Predictive Trend Controls</h2>
        <p className="panel-copy">Live refresh speed: {(refreshMs / 1000).toFixed(0)}s</p>
        <div className="switch-row">
          <label>
            <input type="checkbox" checked={showPredicted} onChange={(e) => setShowPredicted(e.target.checked)} /> Prediction line (dashed)
          </label>
          <label>
            <input type="checkbox" checked={showActual} onChange={(e) => setShowActual(e.target.checked)} /> Current usage line
          </label>
        </div>
      </section>
      <div className="two-col">
        <MemoryUsageChart
          rows={memoryRows}
          spikeTimestamps={spikes}
          insight={getGraphInsight(payload, "memory")}
          onCardClick={() => setActiveReport("memory")}
          isActive={activeReport === "memory"}
        />
        <PredictionChart
          rows={predictionRows}
          showPredicted={showPredicted}
          showActual={showActual}
          insight={getGraphInsight(payload, "prediction")}
          onCardClick={() => setActiveReport("prediction")}
          isActive={activeReport === "prediction"}
        />
      </div>
      <div className="two-col">
        <StabilityChart
          rows={stabilityRows}
          insight={getGraphInsight(payload, "stability")}
          onCardClick={() => setActiveReport("stability")}
          isActive={activeReport === "stability"}
        />
        <DeviceActivityChart
          rows={deviceRows}
          insight={getGraphInsight(payload, "device_activity")}
          onCardClick={() => setActiveReport("device_activity")}
          isActive={activeReport === "device_activity"}
        />
      </div>
      <div className="two-col">
        <MemoryUsageChart rows={shortMemoryRows} spikeTimestamps={spikes} insight={getGraphInsight(payload, "memory")} />
        <PredictionChart rows={shortPredictionRows} showPredicted={showPredicted} showActual={showActual} insight={getGraphInsight(payload, "prediction")} />
      </div>
      <section className={`panel report-flash ${flashReport ? "report-flash--active" : ""}`} ref={detailedReportRef}>
        <h2>{activeReportTitle}</h2>
        <p className="panel-copy">
          <strong>Result:</strong> {payload.metrics.risk_level} risk · Expected trend {expectedTrend}
        </p>
        <p className="panel-copy">
          <strong>What happened:</strong> {activeInsight?.what ?? "No additional graph report available yet."}
        </p>
        <p className="panel-copy">
          <strong>Why:</strong> {activeInsight?.why ?? "Awaiting more telemetry for a stronger explanation."}
        </p>
        <p className="panel-copy">
          <strong>Action:</strong> {activeInsight?.next ?? payload.recommendations.prioritized_actions[0]?.action ?? "Continue monitoring and apply listed recommendations."}
        </p>
      </section>
    </div>
  );
}
