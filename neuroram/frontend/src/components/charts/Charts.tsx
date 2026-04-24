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
  ReferenceArea,
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
const CHART_GRID = "var(--line)";
const CHART_PRIMARY = "var(--green)";
const CHART_PRIMARY_SOFT = "rgba(59,130,246,.3)";

function ChartInsight({ insight }: { insight: ChartStory | null | undefined }) {
  if (!insight) return null;
  return (
    <div className="chart-insight" aria-live="polite">
      <p>
        <strong>What happened:</strong> {insight.what}
      </p>
      <p>
        <strong>What is expected:</strong> {insight.why}
      </p>
      <p>
        <strong>What to do:</strong> {insight.next}
      </p>
    </div>
  );
}

export function MemoryUsageChart({
  rows,
  spikeTimestamps = [],
  insight,
  onCardClick,
  isActive = false,
}: {
  rows: Row[];
  spikeTimestamps?: string[];
  insight?: ChartStory | null;
  onCardClick?: () => void;
  isActive?: boolean;
}) {
  return (
    <div className={`chart-box ${onCardClick ? "chart-box--interactive" : ""} ${isActive ? "chart-box--active" : ""}`} onClick={onCardClick}>
      <h3>Memory Trend and Risk Zone Graph</h3>
      <p className="chart-subtitle">Current RAM and swap behavior with highlighted spikes and high-risk memory zone.</p>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={rows} margin={{ top: 8, right: 12, left: 4, bottom: 24 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
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
          <ReferenceArea y1={80} y2={100} fill="rgba(249,115,22,0.08)" label={{ value: "High Risk Zone", position: "insideTopRight", fill: "#f97316", fontSize: 11 }} />
          {spikeTimestamps.slice(0, 6).map((ts, i) => (
            <ReferenceLine
              key={ts}
              x={ts}
              stroke="#d4af37"
              strokeDasharray="5 5"
              strokeWidth={1.5}
              label={i === 0 ? { value: "Predicted Spike", position: "top", fill: "#d4af37", fontSize: 11 } : undefined}
            />
          ))}
          <Area type="monotone" dataKey="ram_percent" name="RAM %" stroke={CHART_PRIMARY} fill={CHART_PRIMARY_SOFT} isAnimationActive animationDuration={600} />
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
  onCardClick,
  isActive = false,
}: {
  rows: Row[];
  showPredicted: boolean;
  showActual: boolean;
  insight?: ChartStory | null;
  onCardClick?: () => void;
  isActive?: boolean;
}) {
  return (
    <div className={`chart-box ${onCardClick ? "chart-box--interactive" : ""} ${isActive ? "chart-box--active" : ""}`} onClick={onCardClick}>
      <h3>Predictive Memory Analysis</h3>
      <p className="chart-subtitle">Current vs predicted memory usage for the next interval, with risk-zone context.</p>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={rows} margin={{ top: 8, right: 12, left: 4, bottom: 24 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
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
          <ReferenceArea y1={80} y2={100} fill="rgba(249,115,22,0.08)" label={{ value: "High Risk Zone", position: "insideTopRight", fill: "#f97316", fontSize: 11 }} />
          {showPredicted ? (
            <Line type="monotone" dataKey="predicted_ram_percent" name="Predicted %" stroke="#d4af37" strokeDasharray="6 4" dot={false} strokeWidth={2} isAnimationActive animationDuration={600} />
          ) : null}
          {showActual ? (
            <Line type="monotone" dataKey="actual_ram_percent" name="Actual %" stroke={CHART_PRIMARY} dot={false} strokeWidth={2} isAnimationActive animationDuration={600} />
          ) : null}
          <Brush dataKey="timestamp" height={20} stroke="#d4af37" />
        </LineChart>
      </ResponsiveContainer>
      <ChartInsight insight={insight} />
    </div>
  );
}

export function StabilityChart({
  rows,
  insight,
  onCardClick,
  isActive = false,
}: {
  rows: Row[];
  insight?: ChartStory | null;
  onCardClick?: () => void;
  isActive?: boolean;
}) {
  return (
    <div className={`chart-box ${onCardClick ? "chart-box--interactive" : ""} ${isActive ? "chart-box--active" : ""}`} onClick={onCardClick}>
      <h3>Stability index</h3>
      <p className="chart-subtitle">Composite score from RAM, swap, and risk posture (0–100).</p>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={rows} margin={{ top: 8, right: 12, left: 4, bottom: 24 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
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
          <Line type="monotone" dataKey="stability_index" name="Stability" stroke={CHART_PRIMARY} dot={false} strokeWidth={2} isAnimationActive animationDuration={600} />
          <Brush dataKey="timestamp" height={20} stroke="#d4af37" />
        </LineChart>
      </ResponsiveContainer>
      <ChartInsight insight={insight} />
    </div>
  );
}

export function DeviceActivityChart({
  rows,
  insight,
  onCardClick,
  isActive = false,
}: {
  rows: Row[];
  insight?: ChartStory | null;
  onCardClick?: () => void;
  isActive?: boolean;
}) {
  return (
    <div className={`chart-box ${onCardClick ? "chart-box--interactive" : ""} ${isActive ? "chart-box--active" : ""}`} onClick={onCardClick}>
      <h3>Device Impact on Memory Activity</h3>
      <p className="chart-subtitle">External device behavior helps explain memory changes and upcoming pressure.</p>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={rows} margin={{ top: 8, right: 12, left: 4, bottom: 24 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
          <XAxis
            dataKey="timestamp"
            minTickGap={22}
            tick={{ fontSize: 11 }}
            label={{ value: "Time", position: "insideBottom", offset: -4, fill: "var(--text-muted)", fontSize: 11 }}
          />
          <YAxis tick={{ fontSize: 11 }} label={{ value: "Count", angle: -90, position: "insideLeft", fill: "var(--text-muted)", fontSize: 11 }} />
          <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v, n) => [fmtCount(v), n]} labelStyle={{ fontWeight: 600 }} />
          <Legend />
          <Bar dataKey="active_devices" name="Active devices" fill={CHART_PRIMARY} isAnimationActive animationDuration={600} />
          <Bar dataKey="connected_events" name="Connected" fill="#d4af37" isAnimationActive animationDuration={600} />
          <Bar dataKey="disconnected_events" name="Disconnected" fill="#f97316" isAnimationActive animationDuration={600} />
          <Brush dataKey="timestamp" height={20} stroke="#d4af37" />
        </BarChart>
      </ResponsiveContainer>
      <ChartInsight insight={insight} />
    </div>
  );
}
