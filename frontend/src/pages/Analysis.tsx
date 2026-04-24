import type { DashboardPayload } from "../services/api";

type Props = { payload: DashboardPayload };

export function AnalysisPage({ payload }: Props) {
  const riskClass = payload.metrics.risk_level.toLowerCase();
  const predictionEfficiency =
    payload.analysis.memory_patterns.predicted_vs_actual_mae == null
      ? null
      : Number(Math.max(0, Math.min(100, 100 - payload.analysis.memory_patterns.predicted_vs_actual_mae * 8)).toFixed(2));
  const narrative = payload.analysis.narrative ?? payload.analysis.summary;

  return (
    <div className="page-grid">
      <section className="panel">
        <h2>Risk and Algorithm Summary</h2>
        <div className="analysis-top">
          <span className={`risk-badge ${riskClass}`}>{payload.metrics.risk_level}</span>
          <p className="analysis-narrative">{narrative}</p>
          {narrative.trim() !== payload.analysis.summary.trim() ? <p className="panel-copy">{payload.analysis.summary}</p> : null}
        </div>
        <div className="analysis-brief">
          <article>
            <h3>What</h3>
            <p>{payload.analysis.what_why_how?.what ?? (payload.analysis.memory_patterns.spike_detected ? "Short-term memory spikes are present." : "No severe short-term spikes detected.")}</p>
          </article>
          <article>
            <h3>Why</h3>
            <p>{payload.analysis.what_why_how?.why ?? payload.analysis.reasons[0] ?? "Memory behavior is currently stable."}</p>
          </article>
          <article>
            <h3>How Serious</h3>
            <p>{payload.analysis.what_why_how?.how_serious ?? `Risk level is ${payload.metrics.risk_level} with stability score ${payload.metrics.stability_score.toFixed(1)}.`}</p>
          </article>
        </div>
        <div className="analysis-grid">
          <article>
            <h3>Algorithm Used</h3>
            <p>{payload.analysis.algorithm ?? "ML (Random Forest) + DAA (Risk Analyzer and Stability Scoring)"}</p>
          </article>
          <article>
            <h3>Prediction Efficiency</h3>
            <p>MAE: {payload.analysis.memory_patterns.predicted_vs_actual_mae ?? "N/A"}</p>
            <p>Bias: {payload.analysis.memory_patterns.predicted_vs_actual_bias ?? "N/A"}</p>
            <p>Score: {predictionEfficiency == null ? "N/A" : `${predictionEfficiency}%`}</p>
          </article>
          <article>
            <h3>Memory Depletion Logic</h3>
            <p>Spike detected: {payload.analysis.memory_patterns.spike_detected ? "Yes" : "No"}</p>
            <p>Leak detected: {payload.analysis.memory_patterns.gradual_leak_detected ? "Yes" : "No"}</p>
            <p>Abnormal pattern: {payload.analysis.memory_patterns.abnormal_pattern ? "Yes" : "No"}</p>
          </article>
        </div>
      </section>
      <div className="two-col">
        <section className="panel do-panel card-accent-green">
          <h2>Do’s</h2>
          <ul>
            {payload.recommendations.dos.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
        <section className="panel dont-panel card-accent-red">
          <h2>Don’ts</h2>
          <ul>
            {payload.recommendations.donts.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
