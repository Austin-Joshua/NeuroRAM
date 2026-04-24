import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Brush,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Row = Record<string, string | number | null>;

export function MemoryUsageChart({ rows }: { rows: Row[] }) {
  return (
    <div className="chart-box">
      <h3>Live RAM Usage</h3>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" minTickGap={22} tick={{ fontSize: 11 }} />
          <YAxis domain={[0, 100]} />
          <Tooltip />
          <Legend />
          <Area type="monotone" dataKey="ram_percent" stroke="#16a34a" fill="rgba(22,163,74,.28)" />
          <Area type="monotone" dataKey="swap_percent" stroke="#d4af37" fill="rgba(212,175,55,.2)" />
          <Brush dataKey="timestamp" height={20} stroke="#d4af37" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function PredictionChart({ rows, showPredicted, showActual }: { rows: Row[]; showPredicted: boolean; showActual: boolean }) {
  return (
    <div className="chart-box">
      <h3>Prediction vs Actual</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" minTickGap={22} tick={{ fontSize: 11 }} />
          <YAxis domain={[0, 100]} />
          <Tooltip />
          <Legend />
          {showPredicted ? <Line type="monotone" dataKey="predicted_ram_percent" stroke="#d4af37" dot={false} /> : null}
          {showActual ? <Line type="monotone" dataKey="actual_ram_percent" stroke="#16a34a" dot={false} /> : null}
          <Brush dataKey="timestamp" height={20} stroke="#d4af37" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function StabilityChart({ rows }: { rows: Row[] }) {
  return (
    <div className="chart-box">
      <h3>Stability Trend</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" minTickGap={22} tick={{ fontSize: 11 }} />
          <YAxis domain={[0, 100]} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="stability_index" stroke="#16a34a" dot={false} />
          <Brush dataKey="timestamp" height={20} stroke="#d4af37" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function DeviceActivityChart({ rows }: { rows: Row[] }) {
  return (
    <div className="chart-box">
      <h3>Device Activity</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" minTickGap={22} tick={{ fontSize: 11 }} />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="active_devices" fill="#16a34a" />
          <Bar dataKey="connected_events" fill="#d4af37" />
          <Bar dataKey="disconnected_events" fill="#f97316" />
          <Brush dataKey="timestamp" height={20} stroke="#d4af37" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
