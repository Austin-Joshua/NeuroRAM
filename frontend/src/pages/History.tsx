import { useMemo, useState } from "react";
import type { DashboardPayload } from "../services/api";

type Props = { payload: DashboardPayload };

export function HistoryPage({ payload }: Props) {
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(200);
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
        <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
          <option value={100}>100 rows</option>
          <option value={200}>200 rows</option>
          <option value={300}>300 rows</option>
        </select>
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
            {filtered.slice(0, limit).map((row, idx) => (
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
