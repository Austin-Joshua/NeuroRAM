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
const TOOLTIP_STYLE = { borderRadius: 12, border: "1px solid rgba(196, 160, 77, 0.35)", backgroundColor: "rgba(14, 31, 22, 0.92)" };

export function MemoryUsageChart({ rows }: { rows: Row[] }) {
  return (
    <div className="chart-box">
      <h3>Live RAM Usage</h3>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" minTickGap={22} tick={{ fontSize: 11 }} />
          <YAxis domain={[0, 100]} />
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Legend />
          <Area type="monotone" dataKey="ram_percent" name="RAM %" stroke="#1f7a4d" fill="rgba(31,122,77,.32)" />
          <Area type="monotone" dataKey="swap_percent" name="Swap %" stroke="#d4af37" fill="rgba(212,175,55,.2)" />
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
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Legend />
          {showPredicted ? <Line type="monotone" dataKey="predicted_ram_percent" name="Predicted %" stroke="#d4af37" dot={false} strokeWidth={2} /> : null}
          {showActual ? <Line type="monotone" dataKey="actual_ram_percent" name="Actual %" stroke="#1f7a4d" dot={false} strokeWidth={2} /> : null}
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
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Legend />
          <Line type="monotone" dataKey="stability_index" name="Stability Index" stroke="#1f7a4d" dot={false} strokeWidth={2} />
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
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Legend />
          <Bar dataKey="active_devices" name="Active Devices" fill="#1f7a4d" />
          <Bar dataKey="connected_events" name="Connected Events" fill="#d4af37" />
          <Bar dataKey="disconnected_events" name="Disconnected Events" fill="#f97316" />
          <Brush dataKey="timestamp" height={20} stroke="#d4af37" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
