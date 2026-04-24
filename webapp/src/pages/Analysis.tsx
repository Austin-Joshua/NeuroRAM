import type { DashboardPayload } from "../services/api";

type Props = { payload: DashboardPayload };

export function AnalysisPage({ payload }: Props) {
  const riskClass = payload.metrics.risk_level.toLowerCase();
  const predictionEfficiency =
    payload.analysis.memory_patterns.predicted_vs_actual_mae == null
      ? null
      : Number(Math.max(0, Math.min(100, 100 - payload.analysis.memory_patterns.predicted_vs_actual_mae * 8)).toFixed(2));
  return (
    <div className="page-grid">
      <section className="panel">
        <h2>Risk and Algorithm Summary</h2>
        <div className="analysis-top">
          <span className={`risk-badge ${riskClass}`}>{payload.metrics.risk_level}</span>
          <p>{payload.analysis.summary}</p>
        </div>
        <div className="analysis-grid">
          <article>
            <h3>Algorithm Used</h3>
            <p>ML (Random Forest) + DAA (Risk Analyzer and Stability Scoring)</p>
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
        <section className="panel do-panel">
          <h2>Do’s</h2>
          <ul>
            {payload.recommendations.dos.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
        <section className="panel dont-panel">
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
