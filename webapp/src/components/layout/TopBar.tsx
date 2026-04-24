import { Activity, Menu, MoonStar, Sun } from "lucide-react";
import type { DashboardPayload } from "../../services/api";
import { NeuroRAMLogo } from "../brand/NeuroRAMLogo";

type Props = {
  payload: DashboardPayload | null;
  theme: "dark" | "light";
  activePage: string;
  onHomeClick: () => void;
  onMenuToggle: () => void;
  onThemeToggle: () => void;
};

export function TopBar({ payload, theme, activePage, onHomeClick, onMenuToggle, onThemeToggle }: Props) {
  const riskClass = payload?.metrics.risk_level.toLowerCase() ?? "normal";
  const showAlertDot = ["warning", "critical", "emergency"].includes(riskClass);
  const isLive = Boolean(payload?.metrics.pipeline?.running);
  const latency = payload?.metrics.pipeline?.last_cycle_duration_ms;
  const updatedAt = payload?.timestamp_utc ? new Date(payload.timestamp_utc).toLocaleTimeString() : null;

  return (
    <header className="top-shell">
      <div className="brand-block">
        <button className="menu-btn" onClick={onMenuToggle} aria-label="Toggle sidebar navigation">
          <Menu size={16} />
        </button>
        <button className="brand-home" onClick={onHomeClick} aria-label="Go to dashboard">
          <div className="logo-dot" aria-hidden>
            <NeuroRAMLogo size={34} />
          </div>
          <div className="brand-titles">
            <h1>NeuroRAM</h1>
            <p>Memory + Device Intelligence</p>
          </div>
        </button>
      </div>
      <div className="top-actions">
        <span className="pill page-pill">{activePage.toUpperCase()}</span>
        <span className={`pill ${riskClass}`}>
          {showAlertDot ? <span className="status-dot alert" /> : null}
          {payload?.ready ? payload.metrics.risk_level : "CONNECTING"}
        </span>
        <span className={`pill live-pill ${isLive ? "running" : "idle"}`}>
          <span className="status-dot live" />
          <Activity size={13} />
          {payload?.metrics.pipeline?.running ? `Live ${payload.metrics.pipeline.cycles}` : "Idle"}
          {latency != null ? <span className="pill-meta">{latency} ms</span> : null}
        </span>
        {updatedAt ? <span className="pill meta-pill">Updated {updatedAt}</span> : null}
        <button className="theme-icon-btn" onClick={onThemeToggle} aria-label="Toggle theme">
          {theme === "dark" ? <Sun size={16} /> : <MoonStar size={16} />}
        </button>
      </div>
    </header>
  );
}
