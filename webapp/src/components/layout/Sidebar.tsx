import { Menu, LayoutDashboard, MemoryStick, Usb, ChartSpline, ShieldAlert, History } from "lucide-react";

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
  onToggle: () => void;
  onSelect: (page: string) => void;
};

export function Sidebar({ collapsed, activePage, onToggle, onSelect }: Props) {
  return (
    <aside className={`side-shell ${collapsed ? "collapsed" : ""}`}>
      <button className="hamburger-btn" onClick={onToggle} aria-label="Toggle sidebar">
        <Menu size={16} />
      </button>
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
