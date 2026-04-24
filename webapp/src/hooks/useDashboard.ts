import { useEffect, useState } from "react";
import { fetchDashboard } from "../services/api";
import type { DashboardPayload } from "../services/api";

const REFRESH_MS = 5000;
const RETRY_MS = 9000;

export function useDashboard() {
  const [payload, setPayload] = useState<DashboardPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    let timer: number | null = null;
    const load = async () => {
      if (document.visibilityState === "hidden") return;
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
        if (timer != null) window.clearTimeout(timer);
        timer = window.setTimeout(() => void load(), error ? RETRY_MS : REFRESH_MS);
      }
    };
    void load();
    const onVisible = () => {
      if (document.visibilityState === "visible") void load();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      mounted = false;
      if (timer != null) window.clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [error]);

  return { payload, loading, error };
}
