import { Menu, LayoutDashboard, MemoryStick, Usb, ChartSpline, ShieldAlert, History } from "lucide-react";

export type AppPage = "Dashboard" | "Memory" | "Devices" | "Trends" | "Analysis" | "History";

const PAGE_META: Array<{ id: AppPage; icon: typeof LayoutDashboard }> = [
  { id: "Dashboard", icon: LayoutDashboard },
  { id: "Memory", icon: MemoryStick },
  { id: "Devices", icon: Usb },
  { id: "Trends", icon: ChartSpline },
  { id: "Analysis", icon: ShieldAlert },
  { id: "History", icon: History },
];

type Props = {
  collapsed: boolean;
  activePage: AppPage;
  onToggle: () => void;
  onSelect: (page: AppPage) => void;
};

export function Sidebar({ collapsed, activePage, onToggle, onSelect }: Props) {
  return (
    <aside className={`side-shell ${collapsed ? "collapsed" : ""}`}>
      <button className="hamburger-btn" onClick={onToggle} aria-label="Toggle sidebar">
        <Menu size={16} />
      </button>
      <div className="side-links">
        {PAGE_META.map(({ id, icon: Icon }) => (
          <button key={id} className={`side-link ${activePage === id ? "active" : ""}`} onClick={() => onSelect(id)}>
            <Icon size={15} />
            {!collapsed ? <span>{id}</span> : null}
          </button>
        ))}
      </div>
    </aside>
  );
}
