import { useEffect, useMemo, useState } from "react";
import { Activity, Menu, MoonStar, Sun } from "lucide-react";
import type { DashboardPayload } from "../../services/api";

type Props = {
  payload: DashboardPayload | null;
  theme: "dark" | "light";
  activePage: string;
  onHomeClick: () => void;
  onMenuToggle: () => void;
  onThemeToggle: () => void;
};

export function TopBar({ payload, theme, activePage, onHomeClick, onMenuToggle, onThemeToggle }: Props) {
  const isLive = Boolean(payload?.metrics.pipeline?.running);
  const latency = payload?.metrics.pipeline?.last_cycle_duration_ms;
  const updatedAt = payload?.timestamp_utc ? new Date(payload.timestamp_utc).toLocaleTimeString() : null;
  const [nowMs, setNowMs] = useState(() => Date.now());
  const lastPayloadMs = useMemo(() => {
    if (!payload?.timestamp_utc) return null;
    const parsed = Date.parse(payload.timestamp_utc);
    return Number.isNaN(parsed) ? null : parsed;
  }, [payload?.timestamp_utc]);
  const freshnessLabel = useMemo(() => {
    if (lastPayloadMs == null) return null;
    const ageSec = Math.max(0, (nowMs - lastPayloadMs) / 1000);
    return ageSec < 10 ? `fresh: ${ageSec.toFixed(1)}s ago` : `fresh: ${Math.round(ageSec)}s ago`;
  }, [lastPayloadMs, nowMs]);

  useEffect(() => {
    const timer = window.setInterval(() => setNowMs(Date.now()), 500);
    return () => window.clearInterval(timer);
  }, []);

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
        {freshnessLabel ? <span className="pill top-pill meta-pill">{freshnessLabel}</span> : null}
        <button className="theme-icon-btn" onClick={onThemeToggle} aria-label="Toggle theme">
          {theme === "dark" ? <Sun size={16} /> : <MoonStar size={16} />}
        </button>
      </div>
    </header>
  );
}
