import { useEffect, useMemo, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { Sidebar } from "./components/layout/Sidebar";
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

function AppShell() {
  const { payload, loading, error } = useDashboard();
  const location = useLocation();
  const navigate = useNavigate();
  const [theme, setTheme] = useState<"dark" | "light">(getInitialTheme);
  const [collapsed, setCollapsed] = useState(getInitialCollapsed);
  const [isMobile, setIsMobile] = useState(getInitialCollapsed);
  const [showPredicted, setShowPredicted] = useState(true);
  const [showActual, setShowActual] = useState(true);
  const activePage = useMemo(() => {
    const key = location.pathname.replace("/", "").toLowerCase();
    if (!key) return "dashboard";
    return key;
  }, [location.pathname]);

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

  const handleSelectPage = (page: string) => {
    navigate(`/${page}`);
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
          activePage={activePage}
          onHomeClick={() => navigate("/dashboard")}
          onMenuToggle={() => setCollapsed((v) => !v)}
          onThemeToggle={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
        />
        {loading && !payload ? (
          <section className="panel">
            <h2 className="panel-loading-title">Loading</h2>
            <p className="panel-copy">Fetching live memory and device intelligence from the API…</p>
          </section>
        ) : null}
        {error ? (
          <section className="panel error">
            <h2 className="panel-loading-title">Connection issue</h2>
            <p className="panel-copy">Failed to fetch data: {error}</p>
          </section>
        ) : null}
        {payload && !payload.ready ? (
          <section className="panel">
            <h2 className="panel-loading-title">Warming up</h2>
            <p className="panel-copy">{payload.message ?? "No data available yet. The pipeline is collecting the first samples."}</p>
          </section>
        ) : null}
        {payload?.ready && (
          <Routes>
            <Route path="/dashboard" element={<DashboardPage payload={payload} showPredicted={showPredicted} showActual={showActual} setShowPredicted={setShowPredicted} setShowActual={setShowActual} />} />
            <Route path="/memory" element={<MemoryPage payload={payload} />} />
            <Route path="/devices" element={<DevicesPage payload={payload} />} />
            <Route path="/trends" element={<TrendsPage payload={payload} showPredicted={showPredicted} showActual={showActual} setShowPredicted={setShowPredicted} setShowActual={setShowActual} />} />
            <Route path="/analysis" element={<AnalysisPage payload={payload} />} />
            <Route path="/history" element={<HistoryPage payload={payload} />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        )}
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}

export default App;
