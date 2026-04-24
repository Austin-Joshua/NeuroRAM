import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { DashboardPayload } from "../services/api";
import { KpiCards, type KpiCardKey } from "../components/cards/KpiCards";
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

export function DashboardPage({ payload, refreshMs, showPredicted, showActual, setShowPredicted, setShowActual }: Props) {
  const navigate = useNavigate();
  const [windowSize, setWindowSize] = useState(80);
  const memoryRows = payload.trends.memory.slice(-windowSize).map((r) => ({ ...r, ram_percent: Number(r.ram_percent) || 0, swap_percent: Number(r.swap_percent) || 0 }));
  const predictionRows = payload.trends.prediction
    .slice(-windowSize)
    .map((r) => ({ ...r, predicted_ram_percent: Number(r.predicted_ram_percent) || 0, actual_ram_percent: Number(r.actual_ram_percent) || 0 }));
  const stabilityRows = payload.trends.stability.slice(-windowSize).map((r) => ({ ...r, stability_index: Number(r.stability_index) || 0 }));
  const deviceRows = payload.trends.device_activity.slice(-windowSize).map((r) => ({
    ...r,
    active_devices: Number(r.active_devices) || 0,
    connected_events: Number(r.connected_events) || 0,
    disconnected_events: Number(r.disconnected_events) || 0,
  }));
  const spikes = getSpikeTimestamps(payload);
  const [activeReport, setActiveReport] = useState<"memory" | "prediction" | "stability" | "device_activity" | "kpi">("memory");
  const [activeKpi, setActiveKpi] = useState<KpiCardKey>("ram");
  const predictionDelta =
    payload.metrics.predicted_ram_percent == null ? null : payload.metrics.predicted_ram_percent - payload.metrics.ram_now_percent;
  const expectedTrend =
    predictionDelta == null ? "Stable" : predictionDelta > 1 ? "Increasing" : predictionDelta < -1 ? "Decreasing" : "Stable";
  const activeInsight = getGraphInsight(payload, activeReport === "kpi" ? "memory" : activeReport);
  const kpiReport = useMemo(() => {
    const topProcesses = (payload.analysis.processes ?? payload.analysis.inefficient_processes ?? [])
      .filter((p) => p && p.name)
      .slice(0, 4)
      .map((p) => `${p.name} (${p.memory_percent ?? "n/a"}%)`)
      .join(", ");
    const connectedDevices = payload.devices.connected.slice(0, 4).map((d) => d.device_name || d.device_id).join(", ");
    if (activeKpi === "ram") {
      return {
        title: "RAM Usage Detailed Report",
        what: `Current RAM usage is ${payload.metrics.ram_now_percent.toFixed(2)}%.`,
        why:
          topProcesses.length > 0
            ? `Highest RAM-consuming processes: ${topProcesses}.`
            : payload.analysis.reasons[0] ?? "Based on live telemetry from the memory pipeline.",
        action: payload.recommendations.prioritized_actions[0]?.action ?? "Close unused heavy apps if usage remains high.",
      };
    }
    if (activeKpi === "predicted") {
      return {
        title: "Predicted Memory Detailed Report",
        what:
          payload.metrics.predicted_ram_percent == null
            ? "Prediction model is warming up and collecting enough history."
            : `Predicted memory for next interval is ${payload.metrics.predicted_ram_percent.toFixed(2)}%.`,
        why: `Expected trend is ${expectedTrend}${predictionDelta == null ? "" : ` (${predictionDelta >= 0 ? "+" : ""}${predictionDelta.toFixed(2)}%).`}`,
        action: payload.recommendations.prioritized_actions[0]?.action ?? "Use predicted trend to prevent memory spikes early.",
      };
    }
    if (activeKpi === "stability") {
      return {
        title: "Stability Score Detailed Report",
        what: `Current stability score is ${payload.metrics.stability_score.toFixed(1)}/100.`,
        why: `Risk level is ${payload.metrics.risk_level}; score combines RAM behavior, swap pressure, and anomaly signals.`,
        action: payload.recommendations.prioritized_actions[1]?.action ?? payload.recommendations.prioritized_actions[0]?.action ?? "Keep pressure low to improve stability over time.",
      };
    }
    return {
      title: "Device Activity Detailed Report",
      what: `${payload.metrics.connected_devices} device(s) are currently connected.`,
      why:
        connectedDevices.length > 0
          ? `Connected devices: ${connectedDevices}. Recent connect/disconnect events can influence memory pressure patterns.`
          : payload.devices.timeline.length > 0
          ? "Recent connect/disconnect events can influence memory pressure patterns."
          : "No recent device event churn detected.",
      action: "Safely eject unused external devices and monitor event churn during high-memory tasks.",
    };
  }, [activeKpi, payload, expectedTrend, predictionDelta]);
  const activeReportTitle = useMemo(() => {
    if (activeReport === "kpi") return kpiReport.title;
    if (activeReport === "memory") return "Memory Trend Detailed Report";
    if (activeReport === "prediction") return "Prediction Detailed Report";
    if (activeReport === "stability") return "Stability Detailed Report";
    return "Device Impact Detailed Report";
  }, [activeReport, kpiReport.title]);

  return (
    <div className="page-grid">
      <section className="panel">
        <h2>Chart Controls</h2>
        <p className="panel-copy">Live refresh speed: {(refreshMs / 1000).toFixed(0)}s</p>
        <div className="switch-row">
          <label>
            <input type="checkbox" checked={showPredicted} onChange={(e) => setShowPredicted(e.target.checked)} /> Prediction line (dashed)
          </label>
          <label>
            <input type="checkbox" checked={showActual} onChange={(e) => setShowActual(e.target.checked)} /> Current usage line
          </label>
          <label>
            Live window:
            <select value={windowSize} onChange={(e) => setWindowSize(Number(e.target.value))}>
              <option value={60}>60</option>
              <option value={120}>120</option>
              <option value={200}>200</option>
            </select>
          </label>
        </div>
      </section>
      <KpiCards
        payload={payload}
        activeCard={activeKpi}
        onCardClick={(card) => {
          setActiveKpi(card);
          setActiveReport("kpi");
          navigate(`/analysis?focus=${card}`);
        }}
      />
      <div className="two-col">
        <MemoryUsageChart
          rows={memoryRows}
          spikeTimestamps={spikes}
          insight={getGraphInsight(payload, "memory")}
          onCardClick={() => {
            setActiveReport("memory");
            navigate("/trends?focus=memory");
          }}
          isActive={activeReport === "memory"}
        />
        <PredictionChart
          rows={predictionRows}
          showPredicted={showPredicted}
          showActual={showActual}
          insight={getGraphInsight(payload, "prediction")}
          onCardClick={() => {
            setActiveReport("prediction");
            navigate("/trends?focus=prediction");
          }}
          isActive={activeReport === "prediction"}
        />
      </div>
      <div className="two-col">
        <StabilityChart
          rows={stabilityRows}
          insight={getGraphInsight(payload, "stability")}
          onCardClick={() => {
            setActiveReport("stability");
            navigate("/trends?focus=stability");
          }}
          isActive={activeReport === "stability"}
        />
        <DeviceActivityChart
          rows={deviceRows}
          insight={getGraphInsight(payload, "device_activity")}
          onCardClick={() => {
            setActiveReport("device_activity");
            navigate("/trends?focus=device_activity");
          }}
          isActive={activeReport === "device_activity"}
        />
      </div>
      <section className="panel">
        <h2>{activeReportTitle}</h2>
        <p className="panel-copy">
          <strong>Result:</strong>{" "}
          {activeReport === "kpi" ? `Risk ${payload.metrics.risk_level} · Expected trend ${expectedTrend}` : `${payload.metrics.risk_level} risk · Expected trend ${expectedTrend}`}
        </p>
        <p className="panel-copy">
          <strong>What happened:</strong> {activeReport === "kpi" ? kpiReport.what : activeInsight?.what ?? "No additional graph report available yet."}
        </p>
        <p className="panel-copy">
          <strong>Why:</strong> {activeReport === "kpi" ? kpiReport.why : activeInsight?.why ?? "Awaiting more telemetry for a stronger explanation."}
        </p>
        <p className="panel-copy">
          <strong>Action:</strong>{" "}
          {activeReport === "kpi"
            ? kpiReport.action
            : activeInsight?.next ?? payload.recommendations.prioritized_actions[0]?.action ?? "Continue monitoring and apply listed recommendations."}
        </p>
      </section>
      <section className="panel">
        <h2>Device Impact Detailed Report</h2>
        <p className="panel-copy">
          <strong>Result:</strong> {payload.metrics.connected_devices} connected device(s), latest bucket active devices{" "}
          {deviceRows.length ? String(deviceRows[deviceRows.length - 1].active_devices ?? 0) : "0"}.
        </p>
        <p className="panel-copy">
          <strong>What happened:</strong> Recent connected/disconnected activity is captured continuously and correlated with memory trends.
        </p>
        <p className="panel-copy">
          <strong>Why:</strong>{" "}
          {payload.devices.timeline.length > 0
            ? "Device churn and removable media usage can increase memory pressure and instability risk."
            : "No recent external-device churn is visible in the current observation window."}
        </p>
        <p className="panel-copy">
          <strong>Action:</strong> Keep only required devices connected during high-memory tasks and monitor trend graphs for pressure jumps.
        </p>
      </section>
    </div>
  );
}
