import { LayoutDashboard, MemoryStick, Usb, ChartSpline, ShieldAlert, History } from "lucide-react";
import { NeuroRAMLogo } from "../brand/NeuroRAMLogo";

const PAGE_META: Array<{ id: string; label: string; icon: typeof LayoutDashboard }> = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "memory", label: "Memory", icon: MemoryStick },
  { id: "devices", label: "Devices", icon: Usb },
  { id: "trends", label: "Trends", icon: ChartSpline },
  { id: "analysis", label: "Analysis", icon: ShieldAlert },
  { id: "history", label: "History", icon: History },
];

type Props = {
  collapsed: boolean;
  activePage: string;
  onSelect: (page: string) => void;
};

export function Sidebar({ collapsed, activePage, onSelect }: Props) {
  return (
    <aside className={`side-shell ${collapsed ? "collapsed" : ""}`}>
      {!collapsed ? (
        <button className="side-brand" onClick={() => onSelect("dashboard")} aria-label="Go to dashboard">
          <div className="logo-dot" aria-hidden>
            <NeuroRAMLogo size={30} />
          </div>
          <span className="side-brand-title">NeuroRAM</span>
        </button>
      ) : null}
      {!collapsed ? (
        <div className="side-search">
          <input type="text" placeholder="Search" aria-label="Search navigation" />
        </div>
      ) : null}
      <div className="side-links">
        {PAGE_META.map(({ id, label, icon: Icon }) => (
          <button key={id} className={`side-link ${activePage === id ? "active" : ""}`} onClick={() => onSelect(id)}>
            <Icon size={15} />
            {!collapsed ? <span>{label}</span> : null}
          </button>
        ))}
      </div>
    </aside>
  );
}
