import { useMemo, useState } from "react";
import type { DashboardPayload } from "../services/api";

type Props = { payload: DashboardPayload };

export function HistoryPage({ payload }: Props) {
  const [query, setQuery] = useState("");
  const rows = useMemo(() => payload.analysis.logs_preview.slice(0, 300), [payload]);
  const filtered = useMemo(() => {
    if (!query.trim()) return rows;
    const q = query.toLowerCase();
    return rows.filter((row) => JSON.stringify(row).toLowerCase().includes(q));
  }, [rows, query]);
  const cols = filtered.length ? Object.keys(filtered[0]) : [];

  return (
    <section className="panel">
      <h2>History Logs</h2>
      <div className="filter-row">
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search logs..." />
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              {cols.map((c) => (
                <th key={c}>{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.slice(0, 200).map((row, idx) => (
              <tr key={idx}>
                {cols.map((c) => (
                  <td key={`${c}-${idx}`}>{row[c] == null ? "" : String(row[c])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
