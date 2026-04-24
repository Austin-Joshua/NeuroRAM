import type { DashboardPayload } from "../services/api";
import { MemoryUsageChart, StabilityChart } from "../components/charts/Charts";

type Props = { payload: DashboardPayload };

export function MemoryPage({ payload }: Props) {
  const memoryRows = payload.trends.memory.slice(-160).map((r) => ({ ...r, ram_percent: Number(r.ram_percent) || 0, swap_percent: Number(r.swap_percent) || 0 }));
  const stabilityRows = payload.trends.stability.slice(-160).map((r) => ({ ...r, stability_index: Number(r.stability_index) || 0 }));
  const processRows = payload.analysis.processes ?? [];
  return (
    <div className="page-grid">
      <div className="two-col">
        <MemoryUsageChart rows={memoryRows} />
        <StabilityChart rows={stabilityRows} />
      </div>
      <section className="panel">
        <h2>Process-Level Memory Breakdown</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>PID</th>
                <th>Name</th>
                <th>RSS MB</th>
                <th>Memory %</th>
                <th>Inefficiency</th>
              </tr>
            </thead>
            <tbody>
              {processRows.slice(0, 40).map((row, idx) => (
                <tr key={`${row.pid}-${idx}`}>
                  <td>{row.pid}</td>
                  <td>{row.name}</td>
                  <td>{row.rss_mb}</td>
                  <td>{row.memory_percent}</td>
                  <td>{row.inefficiency_score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
