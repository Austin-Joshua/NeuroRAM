import type { DashboardPayload } from "../services/api";

type Props = { payload: DashboardPayload };

function buildSignalNarrative(mp: DashboardPayload["analysis"]["memory_patterns"]): string {
  const parts: string[] = [];
  if (mp.spike_detected) {
    parts.push("Short-lived RAM spikes appeared in the recent window—often tied to bursty workloads, startup phases, or removable storage activity.");
  }
  if (mp.gradual_leak_detected) {
    parts.push("A gradual upward drift suggests possible leak-like growth; validate with a longer window and top process contributors.");
  }
  if (mp.abnormal_pattern) {
    parts.push("Variability is higher than a calm baseline—correlate with apps, devices, and swap pressure before load increases.");
  }
  if (parts.length === 0) {
    return "No strong anomaly signature in the current pattern slice—treat this as a steady snapshot unless risk or swap pressure escalates.";
  }
  return parts.join(" ");
}

export function AnalysisPage({ payload }: Props) {
  const riskClass = payload.metrics.risk_level.toLowerCase();
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

  return (
    <div className="page-grid">
      <section className="panel">
        <h2>Intelligent analysis</h2>
        <p className="panel-copy analysis-lead">
          Structured reading of memory intelligence: what the system sees, why it matters, and how it could affect responsiveness. Numbers below map to the same pipeline
          (OS → DB → ML → DAA → API) you run in production.
        </p>
        <div className="analysis-top">
          <span className={`risk-badge risk-badge--large ${riskClass}`}>Risk · {payload.metrics.risk_level}</span>
          <p className="analysis-narrative">{narrative}</p>
          {narrative.trim() !== payload.analysis.summary.trim() ? <p className="panel-copy">{payload.analysis.summary}</p> : null}
        </div>
        <div className="analysis-brief">
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
        </div>
        <div className="analysis-grid">
          <article>
            <h3>Algorithms in use</h3>
            <p>{payload.analysis.algorithm ?? "ML (Random Forest) + DAA (Risk Analyzer and Stability Scoring)"}</p>
          </article>
          <article>
            <h3>Prediction efficiency</h3>
            <p>
              Mean absolute error (MAE) between forecast and observed RAM:{" "}
              <strong>{payload.analysis.memory_patterns.predicted_vs_actual_mae ?? "N/A"}</strong> percentage points.
            </p>
            <p>
              Signed bias (over vs under forecast):{" "}
              <strong>{payload.analysis.memory_patterns.predicted_vs_actual_bias ?? "N/A"}</strong>.
            </p>
            <p>
              Composite efficiency score (higher is tighter tracking):{" "}
              <strong>{predictionEfficiency == null ? "N/A" : `${predictionEfficiency}%`}</strong>.
            </p>
          </article>
          <article>
            <h3>Pattern signals</h3>
            <p className="panel-copy">{buildSignalNarrative(payload.analysis.memory_patterns)}</p>
            <p className="pattern-flags" aria-label="Pattern flags">
              <span className={payload.analysis.memory_patterns.spike_detected ? "pattern-flag pattern-flag--on" : "pattern-flag"}>Spike</span>
              <span className={payload.analysis.memory_patterns.gradual_leak_detected ? "pattern-flag pattern-flag--on" : "pattern-flag"}>Drift</span>
              <span className={payload.analysis.memory_patterns.abnormal_pattern ? "pattern-flag pattern-flag--on" : "pattern-flag"}>Volatile</span>
            </p>
          </article>
        </div>
      </section>
      <div className="two-col">
        <section className="panel do-panel card-accent-green">
          <h2>Recommended actions</h2>
          <ul>
            {dosList.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
        <section className="panel dont-panel card-accent-red">
          <h2>Actions to avoid</h2>
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
