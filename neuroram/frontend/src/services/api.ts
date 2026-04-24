export type DeviceRow = {
  timestamp: string;
  device_id: string;
  device_name: string;
  device_type: string;
  device_group: string;
  mountpoint: string;
  capacity_gb: number | null;
  used_gb: number | null;
  free_gb: number | null;
  usage_percent: number | null;
  connection_duration_sec: number | null;
  source_os: string;
  buffer_state?: string;
  file_count?: number | null;
  folder_count?: number | null;
};

export type DeviceEventRow = {
  timestamp: string;
  event_type: string;
  device_id: string;
  device_name: string;
  device_group: string;
  device_type?: string | null;
  mountpoint?: string | null;
  usage_percent?: number | null;
};

export type MemoryTrendRow = {
  timestamp: string;
  ram_percent: number;
  swap_percent: number;
  ram_used_mb?: number;
  available_mb?: number;
};

export type PredictionTrendRow = {
  timestamp: string;
  predicted_ram_percent: number | null;
  actual_ram_percent: number | null;
  model_name: string;
};

export type StabilityTrendRow = {
  timestamp: string;
  stability_index: number | null;
  risk_level: string;
};

export type ProcessInsight = {
  pid: number | null;
  name: string | null;
  rss_mb: number | null;
  memory_percent: number | null;
  inefficiency_score: number | null;
};

export type ChartInsightBlock = { what: string; why: string; next: string };

export type DashboardPayload = {
  ready: boolean;
  timestamp_utc: string;
  message?: string;
  metrics: {
    ram_now_percent: number;
    predicted_ram_percent: number | null;
    stability_score: number;
    risk_level: string;
    health_category: string;
    connected_devices: number;
    connected_storage: number;
    connected_dongles: number;
    connected_network_adapters: number;
    pipeline?: {
      running: boolean;
      cycles: number;
      last_cycle_utc: string | null;
      last_error: string | null;
      last_prediction: number | null;
      last_success_utc?: string | null;
      last_cycle_duration_ms?: number | null;
    };
  };
  devices: {
    connected: DeviceRow[];
    storage: DeviceRow[];
    dongles: DeviceRow[];
    network_adapters: DeviceRow[];
    timeline: DeviceEventRow[];
  };
  trends: {
    memory: MemoryTrendRow[];
    prediction: PredictionTrendRow[];
    stability: StabilityTrendRow[];
    device_activity: Array<Record<string, string | number | null>>;
  };
  analysis: {
    summary: string;
    what_why_how?: {
      what: string;
      why: string;
      how_serious: string;
      /** Plain-language system impact (mirrors how_serious when provided by API). */
      impact?: string;
    };
    algorithm?: string;
    reasons: string[];
    memory_patterns: {
      spike_detected: boolean;
      gradual_leak_detected: boolean;
      abnormal_pattern: boolean;
      predicted_vs_actual_mae: number | null;
      predicted_vs_actual_bias: number | null;
      severity?: string;
      explanations?: string[];
      spike_timestamps?: string[];
    };
    inefficient_processes: ProcessInsight[];
    processes?: ProcessInsight[];
    logs_preview: Array<Record<string, string | number | null>>;
    narrative?: string;
    graph_insights?: {
      memory: ChartInsightBlock;
      prediction: ChartInsightBlock;
      stability: ChartInsightBlock;
      device_activity: ChartInsightBlock;
    };
  };
  recommendations: {
    category: string;
    dos: string[];
    donts: string[];
    prioritized_actions: Array<{ priority: string; action: string; why: string }>;
  };
};

export async function fetchDashboard(): Promise<DashboardPayload> {
  const res = await fetch("/api/dashboard");
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return (await res.json()) as DashboardPayload;
}
