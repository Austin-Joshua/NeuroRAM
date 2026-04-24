import { Activity, Menu, MoonStar, Sun } from "lucide-react";
import type { DashboardPayload } from "../../services/api";

type Props = {
  payload: DashboardPayload | null;
  theme: "dark" | "light";
  activePage: string;
  refreshMs: number;
  onRefreshMsChange: (v: number) => void;
  onHomeClick: () => void;
  onMenuToggle: () => void;
  onThemeToggle: () => void;
};

export function TopBar({ payload, theme, activePage, refreshMs, onRefreshMsChange, onHomeClick, onMenuToggle, onThemeToggle }: Props) {
  const isLive = Boolean(payload?.metrics.pipeline?.running);
  const latency = payload?.metrics.pipeline?.last_cycle_duration_ms;
  const updatedAt = payload?.timestamp_utc ? new Date(payload.timestamp_utc).toLocaleTimeString() : null;

  return (
    <header className="top-shell">
      <div className="brand-block">
        <button className="menu-btn" onClick={onMenuToggle} aria-label="Toggle sidebar navigation">
          <Menu size={16} />
        </button>
        <button className="brand-home top-page-label" onClick={onHomeClick} aria-label="Go to dashboard">
          {activePage.toUpperCase()}
        </button>
      </div>
      <div className="top-actions">
        <span className={`pill top-pill live-pill ${isLive ? "running" : "idle"}`}>
          <span className="status-dot live" />
          <Activity size={13} />
          {payload?.metrics.pipeline?.running ? `Live ${payload.metrics.pipeline.cycles}` : "Idle"}
          {latency != null ? <span className="pill-meta">{latency} ms</span> : null}
        </span>
        {updatedAt ? <span className="pill top-pill meta-pill">Updated {updatedAt}</span> : null}
        <label className="pill top-pill meta-pill" aria-label="Set auto refresh interval">
          Refresh
          <select value={refreshMs} onChange={(e) => onRefreshMsChange(Number(e.target.value))}>
            <option value={2000}>2s</option>
            <option value={4000}>4s</option>
          </select>
        </label>
        <button className="theme-icon-btn" onClick={onThemeToggle} aria-label="Toggle theme">
          {theme === "dark" ? <Sun size={16} /> : <MoonStar size={16} />}
        </button>
      </div>
    </header>
  );
}
