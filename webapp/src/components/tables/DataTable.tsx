type Props = {
  title: string;
  rows: Array<Record<string, string | number | null>>;
  limit?: number;
};

export function DataTable({ title, rows, limit = 40 }: Props) {
  const clipped = rows.slice(0, limit);
  const columns = clipped.length ? Object.keys(clipped[0]) : [];
  return (
    <section className="panel">
      <h2>{title}</h2>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {clipped.map((row, idx) => (
              <tr key={idx}>
                {columns.map((col) => (
                  <td key={`${col}-${idx}`}>{row[col] == null ? "" : String(row[col])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
