import { useEffect, useState } from "react";
import { Sidebar } from "./components/layout/Sidebar";
import type { AppPage } from "./components/layout/Sidebar";
import { TopBar } from "./components/layout/TopBar";
import { useDashboard } from "./hooks/useDashboard";
import { DashboardPage } from "./pages/Dashboard";
import { MemoryPage } from "./pages/Memory";
import { DevicesPage } from "./pages/Devices";
import { TrendsPage } from "./pages/Trends";
import { AnalysisPage } from "./pages/Analysis";
import { HistoryPage } from "./pages/History";

const THEME_KEY = "neuroram-theme";

const getInitialTheme = (): "dark" | "light" => {
  if (typeof window === "undefined") return "dark";
  const stored = window.localStorage.getItem(THEME_KEY);
  return stored === "light" ? "light" : "dark";
};

const getInitialCollapsed = (): boolean => {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(max-width: 960px)").matches;
};

function App() {
  const { payload, loading, error } = useDashboard();
  const [theme, setTheme] = useState<"dark" | "light">(getInitialTheme);
  const [activePage, setActivePage] = useState<AppPage>("Dashboard");
  const [collapsed, setCollapsed] = useState(getInitialCollapsed);
  const [isMobile, setIsMobile] = useState(getInitialCollapsed);
  const [showPredicted, setShowPredicted] = useState(true);
  const [showActual, setShowActual] = useState(true);

  useEffect(() => {
    document.body.dataset.theme = theme;
    window.localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 960px)");
    const syncSidebar = (event: MediaQueryListEvent | MediaQueryList) => {
      setIsMobile(event.matches);
      setCollapsed(event.matches);
    };
    syncSidebar(media);
    const onChange = (event: MediaQueryListEvent) => syncSidebar(event);
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, []);

  const handleSelectPage = (page: AppPage) => {
    setActivePage(page);
    if (window.matchMedia("(max-width: 960px)").matches) {
      setCollapsed(true);
    }
  };

  return (
    <div className="shell">
      <Sidebar collapsed={collapsed} activePage={activePage} onToggle={() => setCollapsed((v) => !v)} onSelect={handleSelectPage} />
      {!collapsed && isMobile ? <button className="side-backdrop" aria-label="Close navigation" onClick={() => setCollapsed(true)} /> : null}
      <main className="main-shell">
        <TopBar
          payload={payload}
          theme={theme}
          onHomeClick={() => setActivePage("Dashboard")}
          onMenuToggle={() => setCollapsed((v) => !v)}
          onThemeToggle={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
        />
        {loading && !payload ? <section className="panel">Loading dashboard...</section> : null}
        {error ? <section className="panel error">Failed to fetch data: {error}</section> : null}
        {payload && !payload.ready ? <section className="panel">{payload.message ?? "No data available yet."}</section> : null}
        {payload?.ready && (
          <>
            {activePage === "Dashboard" ? <DashboardPage payload={payload} showPredicted={showPredicted} showActual={showActual} setShowPredicted={setShowPredicted} setShowActual={setShowActual} /> : null}
            {activePage === "Memory" ? <MemoryPage payload={payload} /> : null}
            {activePage === "Devices" ? <DevicesPage payload={payload} /> : null}
            {activePage === "Trends" ? <TrendsPage payload={payload} showPredicted={showPredicted} showActual={showActual} setShowPredicted={setShowPredicted} setShowActual={setShowActual} /> : null}
            {activePage === "Analysis" ? <AnalysisPage payload={payload} /> : null}
            {activePage === "History" ? <HistoryPage payload={payload} /> : null}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
