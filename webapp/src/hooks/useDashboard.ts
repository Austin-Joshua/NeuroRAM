import { useEffect, useState } from "react";
import { fetchDashboard } from "../services/api";
import type { DashboardPayload } from "../services/api";

const REFRESH_MS = 5000;

export function useDashboard() {
  const [payload, setPayload] = useState<DashboardPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const data = await fetchDashboard();
        if (!mounted) return;
        setPayload(data);
        setError(null);
      } catch (err) {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : "Failed to load dashboard");
      } finally {
        if (mounted) setLoading(false);
      }
    };
    void load();
    const timer = window.setInterval(() => void load(), REFRESH_MS);
    return () => {
      mounted = false;
      window.clearInterval(timer);
    };
  }, []);

  return { payload, loading, error };
}
