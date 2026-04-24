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
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartStory } from "../../utils/chartInsights";

type Row = Record<string, string | number | null>;

const fmtPct = (v: unknown) => (typeof v === "number" && !Number.isNaN(v) ? `${v.toFixed(1)}%` : "—");
const fmtScore = (v: unknown) => (typeof v === "number" && !Number.isNaN(v) ? `${v.toFixed(1)} / 100` : "—");
const fmtCount = (v: unknown) => (typeof v === "number" && !Number.isNaN(v) ? `${Math.round(v)}` : "—");

const TOOLTIP_STYLE = {
  borderRadius: 12,
  border: "1px solid var(--tooltip-border)",
  backgroundColor: "var(--tooltip-bg)",
  color: "var(--tooltip-fg)",
  boxShadow: "var(--shadow-md)",
};

function ChartInsight({ insight }: { insight: ChartStory | null | undefined }) {
  if (!insight) return null;
  return (
    <div className="chart-insight" aria-live="polite">
      <p>
        <strong>What happened:</strong> {insight.what}
      </p>
      <p>
        <strong>Why it happened:</strong> {insight.why}
      </p>
      <p>
        <strong>What it means:</strong> {insight.next}
      </p>
    </div>
  );
}

export function MemoryUsageChart({
  rows,
  spikeTimestamps = [],
  insight,
}: {
  rows: Row[];
  spikeTimestamps?: string[];
  insight?: ChartStory | null;
}) {
  return (
    <div className="chart-box">
      <h3>Live RAM and swap</h3>
      <p className="chart-subtitle">Percent of system memory and swap in use over time.</p>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={rows} margin={{ top: 8, right: 12, left: 4, bottom: 24 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(31,122,77,0.15)" />
          <XAxis
            dataKey="timestamp"
            minTickGap={22}
            tick={{ fontSize: 11 }}
            label={{ value: "Time", position: "insideBottom", offset: -4, fill: "var(--text-muted)", fontSize: 11 }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 11 }}
            label={{ value: "Percent (%)", angle: -90, position: "insideLeft", fill: "var(--text-muted)", fontSize: 11 }}
          />
          <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v, n) => [fmtPct(v), n]} labelStyle={{ fontWeight: 600 }} />
          <Legend />
          {spikeTimestamps.slice(0, 6).map((ts, i) => (
            <ReferenceLine
              key={ts}
              x={ts}
              stroke="#d4af37"
              strokeDasharray="5 5"
              strokeWidth={1.5}
              label={i === 0 ? { value: "Spike", position: "top", fill: "#d4af37", fontSize: 11 } : undefined}
            />
          ))}
          <Area type="monotone" dataKey="ram_percent" name="RAM %" stroke="#1f7a4d" fill="rgba(31,122,77,.32)" isAnimationActive animationDuration={600} />
          <Area type="monotone" dataKey="swap_percent" name="Swap %" stroke="#d4af37" fill="rgba(212,175,55,.2)" isAnimationActive animationDuration={600} />
          <Brush dataKey="timestamp" height={20} stroke="#d4af37" />
        </AreaChart>
      </ResponsiveContainer>
      <ChartInsight insight={insight} />
    </div>
  );
}

export function PredictionChart({
  rows,
  showPredicted,
  showActual,
  insight,
}: {
  rows: Row[];
  showPredicted: boolean;
  showActual: boolean;
  insight?: ChartStory | null;
}) {
  return (
    <div className="chart-box">
      <h3>Prediction vs actual RAM</h3>
      <p className="chart-subtitle">Model forecast compared to observed memory pressure.</p>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={rows} margin={{ top: 8, right: 12, left: 4, bottom: 24 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(31,122,77,0.15)" />
          <XAxis
            dataKey="timestamp"
            minTickGap={22}
            tick={{ fontSize: 11 }}
            label={{ value: "Time", position: "insideBottom", offset: -4, fill: "var(--text-muted)", fontSize: 11 }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 11 }}
            label={{ value: "Percent (%)", angle: -90, position: "insideLeft", fill: "var(--text-muted)", fontSize: 11 }}
          />
          <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v, n) => [fmtPct(v), n]} labelStyle={{ fontWeight: 600 }} />
          <Legend />
          {showPredicted ? (
            <Line type="monotone" dataKey="predicted_ram_percent" name="Predicted %" stroke="#d4af37" dot={false} strokeWidth={2} isAnimationActive animationDuration={600} />
          ) : null}
          {showActual ? (
            <Line type="monotone" dataKey="actual_ram_percent" name="Actual %" stroke="#1f7a4d" dot={false} strokeWidth={2} isAnimationActive animationDuration={600} />
          ) : null}
          <Brush dataKey="timestamp" height={20} stroke="#d4af37" />
        </LineChart>
      </ResponsiveContainer>
      <ChartInsight insight={insight} />
    </div>
  );
}

export function StabilityChart({ rows, insight }: { rows: Row[]; insight?: ChartStory | null }) {
  return (
    <div className="chart-box">
      <h3>Stability index</h3>
      <p className="chart-subtitle">Composite score from RAM, swap, and risk posture (0–100).</p>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={rows} margin={{ top: 8, right: 12, left: 4, bottom: 24 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(31,122,77,0.15)" />
          <XAxis
            dataKey="timestamp"
            minTickGap={22}
            tick={{ fontSize: 11 }}
            label={{ value: "Time", position: "insideBottom", offset: -4, fill: "var(--text-muted)", fontSize: 11 }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 11 }}
            label={{ value: "Stability", angle: -90, position: "insideLeft", fill: "var(--text-muted)", fontSize: 11 }}
          />
          <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v, n) => [fmtScore(v), n]} labelStyle={{ fontWeight: 600 }} />
          <Legend />
          <Line type="monotone" dataKey="stability_index" name="Stability" stroke="#1f7a4d" dot={false} strokeWidth={2} isAnimationActive animationDuration={600} />
          <Brush dataKey="timestamp" height={20} stroke="#d4af37" />
        </LineChart>
      </ResponsiveContainer>
      <ChartInsight insight={insight} />
    </div>
  );
}

export function DeviceActivityChart({ rows, insight }: { rows: Row[]; insight?: ChartStory | null }) {
  return (
    <div className="chart-box">
      <h3>Device activity</h3>
      <p className="chart-subtitle">Active devices and connect/disconnect events per sampled bucket.</p>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={rows} margin={{ top: 8, right: 12, left: 4, bottom: 24 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(31,122,77,0.15)" />
          <XAxis
            dataKey="timestamp"
            minTickGap={22}
            tick={{ fontSize: 11 }}
            label={{ value: "Time", position: "insideBottom", offset: -4, fill: "var(--text-muted)", fontSize: 11 }}
          />
          <YAxis tick={{ fontSize: 11 }} label={{ value: "Count", angle: -90, position: "insideLeft", fill: "var(--text-muted)", fontSize: 11 }} />
          <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v, n) => [fmtCount(v), n]} labelStyle={{ fontWeight: 600 }} />
          <Legend />
          <Bar dataKey="active_devices" name="Active devices" fill="#1f7a4d" isAnimationActive animationDuration={600} />
          <Bar dataKey="connected_events" name="Connected" fill="#d4af37" isAnimationActive animationDuration={600} />
          <Bar dataKey="disconnected_events" name="Disconnected" fill="#f97316" isAnimationActive animationDuration={600} />
          <Brush dataKey="timestamp" height={20} stroke="#d4af37" />
        </BarChart>
      </ResponsiveContainer>
      <ChartInsight insight={insight} />
    </div>
  );
}
