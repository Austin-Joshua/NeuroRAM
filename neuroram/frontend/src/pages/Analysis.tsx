import { type CSSProperties, useEffect, useRef, useState } from "react";
import type { DashboardPayload } from "../services/api";
import { DeviceActivityChart, MemoryUsageChart, PredictionChart, StabilityChart } from "../components/charts/Charts";
import { getGraphInsight, getSpikeTimestamps } from "../utils/chartInsights";
import { useSearchParams } from "react-router-dom";

type Props = { payload: DashboardPayload };

function buildSignalNarrative(mp: DashboardPayload["analysis"]["memory_patterns"]): string {
  const flags: string[] = [];
  if (mp.spike_detected) flags.push("Spike detected");
  if (mp.gradual_leak_detected) flags.push("Drift detected");
  if (mp.abnormal_pattern) flags.push("Volatility detected");
  return flags.length ? flags.join(" • ") : "No anomaly signals detected";
}

export function AnalysisPage({ payload }: Props) {
  const [searchParams] = useSearchParams();
  const focus = (searchParams.get("focus") ?? "").toLowerCase();
  const focusedReportRef = useRef<HTMLElement | null>(null);
  const [flashReport, setFlashReport] = useState(false);
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    overview: true,
    quality: true,
    signals: true,
  });
  const riskClass = payload.metrics.risk_level.toLowerCase();
  const riskScore = Number(
    (
      payload.metrics.risk_level === "EMERGENCY"
        ? 95
        : payload.metrics.risk_level === "CRITICAL"
        ? 80
        : payload.metrics.risk_level === "WARNING"
        ? 58
        : 28
    ).toFixed(1),
  );
  const predictionEfficiency =
    payload.analysis.memory_patterns.predicted_vs_actual_mae == null
      ? null
      : Number(Math.max(0, Math.min(100, 100 - payload.analysis.memory_patterns.predicted_vs_actual_mae * 8)).toFixed(2));
  const narrative = payload.analysis.narrative ?? payload.analysis.summary;
  const dosList =
    payload.recommendations.dos.length > 0
      ? payload.recommendations.dos
      : ["Keep the telemetry service running so forecasts and risk scores stay grounded in fresh samples."];
  const dontsList =
    payload.recommendations.donts.length > 0
      ? payload.recommendations.donts
      : ["Avoid ignoring repeated warnings if RAM climbs into higher bands or swap use grows."];
  const topRecommendedAction = payload.recommendations.prioritized_actions?.[0];
  const memoryRows = payload.trends.memory.slice(-140).map((r) => ({ ...r, ram_percent: Number(r.ram_percent) || 0, swap_percent: Number(r.swap_percent) || 0 }));
  const predictionRows = payload.trends.prediction
    .slice(-140)
    .map((r) => ({ ...r, predicted_ram_percent: Number(r.predicted_ram_percent) || 0, actual_ram_percent: Number(r.actual_ram_percent) || 0 }));
  const stabilityRows = payload.trends.stability.slice(-140).map((r) => ({ ...r, stability_index: Number(r.stability_index) || 0 }));
  const deviceRows = payload.trends.device_activity.slice(-140).map((r) => ({
    ...r,
    active_devices: Number(r.active_devices) || 0,
    connected_events: Number(r.connected_events) || 0,
    disconnected_events: Number(r.disconnected_events) || 0,
  }));
  const spikes = getSpikeTimestamps(payload);
  const focusedMemoryRows = memoryRows.slice(-80);
  const focusedPredictionRows = predictionRows.slice(-80);
  const focusedStabilityRows = stabilityRows.slice(-80);
  const focusedDeviceRows = deviceRows.slice(-80);
  const focusedKpiReport =
    focus === "ram"
      ? {
          title: "RAM Usage Focused Report",
          what: `Current RAM usage is ${payload.metrics.ram_now_percent.toFixed(2)}%.`,
          why:
            (payload.analysis.processes ?? payload.analysis.inefficient_processes ?? [])
              .filter((p) => p && p.name)
              .slice(0, 4)
              .map((p) => `${p.name} (${p.memory_percent ?? "n/a"}%)`)
              .join(", ") || "Process-level usage data is still warming up.",
          action: payload.recommendations.prioritized_actions[0]?.action ?? "Close unused high-memory apps.",
        }
      : focus === "predicted"
      ? {
          title: "Predicted Memory Focused Report",
          what:
            payload.metrics.predicted_ram_percent == null
              ? "Prediction is warming up."
              : `Predicted memory in next interval: ${payload.metrics.predicted_ram_percent.toFixed(2)}%.`,
          why: payload.analysis.reasons[0] ?? "Derived from rolling RAM trend and model forecast.",
          action: payload.recommendations.prioritized_actions[0]?.action ?? "Take preventive action before spikes.",
        }
      : focus === "stability"
      ? {
          title: "Stability Focused Report",
          what: `Stability score is ${payload.metrics.stability_score.toFixed(1)}/100 with risk ${payload.metrics.risk_level}.`,
          why: payload.analysis.what_why_how?.impact ?? "Score blends trend volatility and risk posture.",
          action: payload.recommendations.prioritized_actions[1]?.action ?? payload.recommendations.prioritized_actions[0]?.action ?? "Reduce load and monitor trend recovery.",
        }
      : focus === "devices"
      ? {
          title: "Active Devices Focused Report",
          what: `${payload.metrics.connected_devices} active device(s) detected.`,
          why:
            payload.devices.connected.slice(0, 4).map((d) => d.device_name || d.device_id).join(", ") ||
            "No devices listed in current window.",
          action: "Disconnect unused devices and watch device-impact graph for stabilization.",
        }
      : null;
  useEffect(() => {
    if (focusedKpiReport && focusedReportRef.current) {
      requestAnimationFrame(() => {
        focusedReportRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
        setFlashReport(true);
        window.setTimeout(() => setFlashReport(false), 900);
      });
    }
  }, [focusedKpiReport]);
  const toggleSection = (id: string) => {
    setOpenSections((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="page-grid">
      <section className="panel">
        <h2>Predictive Analysis</h2>
        <div className="analysis-top">
          <span className={`risk-badge risk-badge--large ${riskClass}`}>Risk · {payload.metrics.risk_level}</span>
          <p className="analysis-narrative">{narrative}</p>
        </div>
        <div className="risk-meter-grid">
          <article className="risk-meter-card">
            <h3>Risk meter</h3>
            <div
              className="risk-meter-ring"
              style={
                {
                  "--risk-value": `${riskScore}%`,
                } as CSSProperties
              }
            >
              <div className="risk-meter-inner">
                <strong>{riskScore.toFixed(0)}%</strong>
                <span>{payload.metrics.risk_level}</span>
              </div>
            </div>
          </article>
          <article className="risk-meter-card">
            <h3>Stability meter</h3>
            <div
              className="risk-meter-ring risk-meter-ring--stable"
              style={
                {
                  "--risk-value": `${Math.max(0, Math.min(100, payload.metrics.stability_score)).toFixed(1)}%`,
                } as CSSProperties
              }
            >
              <div className="risk-meter-inner">
                <strong>{payload.metrics.stability_score.toFixed(0)}</strong>
                <span>/100</span>
              </div>
            </div>
          </article>
        </div>
        <div className="analysis-collapsible-list">
          <article className="analysis-collapsible">
            <button className="analysis-collapsible-toggle" onClick={() => toggleSection("overview")} aria-expanded={openSections.overview}>
              <h3>Overview</h3>
              <span>{openSections.overview ? "−" : "+"}</span>
            </button>
            {openSections.overview ? (
              <div className="analysis-collapsible-body analysis-brief">
                <article>
                  <h3>What is happening</h3>
                  <p>{payload.analysis.what_why_how?.what ?? (payload.analysis.memory_patterns.spike_detected ? "Short-term memory spikes are present." : "No severe short-term spikes detected.")}</p>
                </article>
                <article>
                  <h3>Why it is happening</h3>
                  <p>{payload.analysis.what_why_how?.why ?? payload.analysis.reasons[0] ?? "Memory behavior is currently stable."}</p>
                </article>
                <article>
                  <h3>Impact on the system</h3>
                  <p>
                    {payload.analysis.what_why_how?.impact ??
                      payload.analysis.what_why_how?.how_serious ??
                      `Risk level is ${payload.metrics.risk_level} with stability score ${payload.metrics.stability_score.toFixed(1)}.`}
                  </p>
                </article>
                <article>
                  <h3>Recommended action</h3>
                  <p>
                    {topRecommendedAction
                      ? `${topRecommendedAction.action} (${topRecommendedAction.priority})`
                      : dosList[0] ?? "No immediate action required. Keep telemetry active and monitor trend direction."}
                  </p>
                </article>
              </div>
            ) : null}
          </article>

          <article className="analysis-collapsible">
            <button className="analysis-collapsible-toggle" onClick={() => toggleSection("quality")} aria-expanded={openSections.quality}>
              <h3>Forecast quality</h3>
              <span>{openSections.quality ? "−" : "+"}</span>
            </button>
            {openSections.quality ? (
              <div className="analysis-collapsible-body analysis-grid">
                <article>
                  <h3>Model accuracy</h3>
                  <p>
                    MAE: <strong>{payload.analysis.memory_patterns.predicted_vs_actual_mae ?? "N/A"}</strong> · Bias:{" "}
                    <strong>{payload.analysis.memory_patterns.predicted_vs_actual_bias ?? "N/A"}</strong>
                  </p>
                  <p>
                    Efficiency: <strong>{predictionEfficiency == null ? "N/A" : `${predictionEfficiency}%`}</strong>
                  </p>
                </article>
              </div>
            ) : null}
          </article>

          <article className="analysis-collapsible">
            <button className="analysis-collapsible-toggle" onClick={() => toggleSection("signals")} aria-expanded={openSections.signals}>
              <h3>Pattern signals</h3>
              <span>{openSections.signals ? "−" : "+"}</span>
            </button>
            {openSections.signals ? (
              <div className="analysis-collapsible-body analysis-grid">
                <article>
                  <h3>Signal summary</h3>
                  <p className="panel-copy">{buildSignalNarrative(payload.analysis.memory_patterns)}</p>
                  <p className="pattern-flags" aria-label="Pattern flags">
                    <span className={payload.analysis.memory_patterns.spike_detected ? "pattern-flag pattern-flag--on" : "pattern-flag"}>Spike</span>
                    <span className={payload.analysis.memory_patterns.gradual_leak_detected ? "pattern-flag pattern-flag--on" : "pattern-flag"}>Drift</span>
                    <span className={payload.analysis.memory_patterns.abnormal_pattern ? "pattern-flag pattern-flag--on" : "pattern-flag"}>Volatile</span>
                  </p>
                </article>
              </div>
            ) : null}
          </article>
        </div>
      </section>
      {focusedKpiReport ? (
        <section className={`panel report-flash ${flashReport ? "report-flash--active" : ""}`} ref={focusedReportRef}>
          <h2>{focusedKpiReport.title}</h2>
          <p className="panel-copy">
            <strong>What:</strong> {focusedKpiReport.what}
          </p>
          <p className="panel-copy">
            <strong>Why:</strong> {focusedKpiReport.why}
          </p>
          <p className="panel-copy">
            <strong>Action:</strong> {focusedKpiReport.action}
          </p>
        </section>
      ) : null}
      {focus ? (
        <div className="two-col">
          {focus === "ram" ? (
            <>
              <MemoryUsageChart rows={focusedMemoryRows} spikeTimestamps={spikes} insight={getGraphInsight(payload, "memory")} />
              <PredictionChart rows={focusedPredictionRows} showPredicted showActual insight={getGraphInsight(payload, "prediction")} />
            </>
          ) : null}
          {focus === "predicted" ? (
            <>
              <PredictionChart rows={focusedPredictionRows} showPredicted showActual insight={getGraphInsight(payload, "prediction")} />
              <MemoryUsageChart rows={focusedMemoryRows} spikeTimestamps={spikes} insight={getGraphInsight(payload, "memory")} />
            </>
          ) : null}
          {focus === "stability" ? (
            <>
              <StabilityChart rows={focusedStabilityRows} insight={getGraphInsight(payload, "stability")} />
              <PredictionChart rows={focusedPredictionRows} showPredicted showActual insight={getGraphInsight(payload, "prediction")} />
            </>
          ) : null}
          {focus === "devices" ? (
            <>
              <DeviceActivityChart rows={focusedDeviceRows} insight={getGraphInsight(payload, "device_activity")} />
              <MemoryUsageChart rows={focusedMemoryRows} spikeTimestamps={spikes} insight={getGraphInsight(payload, "memory")} />
            </>
          ) : null}
        </div>
      ) : null}
      <div className="two-col">
        <MemoryUsageChart rows={memoryRows} spikeTimestamps={spikes} insight={getGraphInsight(payload, "memory")} />
        <PredictionChart rows={predictionRows} showPredicted showActual insight={getGraphInsight(payload, "prediction")} />
      </div>
      <div className="two-col">
        <StabilityChart rows={stabilityRows} insight={getGraphInsight(payload, "stability")} />
        <DeviceActivityChart rows={deviceRows} insight={getGraphInsight(payload, "device_activity")} />
      </div>
      <div className="two-col">
        <section className="panel do-panel card-accent-green">
          <h2>Predictive Recommended Actions</h2>
          <ul>
            {dosList.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
        <section className="panel dont-panel card-accent-red">
          <h2>Predictive Actions to Avoid</h2>
          <ul>
            {dontsList.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
