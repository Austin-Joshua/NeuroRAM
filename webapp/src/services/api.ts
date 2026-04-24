export type DeviceRow = {
  timestamp: string;
  device_id: string;
  device_name: string;
  device_type: string;
  device_group: string;
  mountpoint: string;
  capacity_gb: number | "";
  used_gb: number | "";
  free_gb: number | "";
  usage_percent: number | "";
  connection_duration_sec: number | "";
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
  predicted_ram_percent: number | "";
  actual_ram_percent: number | "";
  model_name: string;
};

export type StabilityTrendRow = {
  timestamp: string;
  stability_index: number | "";
  risk_level: string;
};

export type ProcessInsight = {
  pid: number;
  name: string;
  rss_mb: number;
  memory_percent: number;
  inefficiency_score: number;
};

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
    };
    algorithm?: string;
    reasons: string[];
    memory_patterns: {
      spike_detected: boolean;
      gradual_leak_detected: boolean;
      abnormal_pattern: boolean;
      predicted_vs_actual_mae: number | null;
      predicted_vs_actual_bias: number | null;
    };
    inefficient_processes: ProcessInsight[];
    processes?: ProcessInsight[];
    logs_preview: Array<Record<string, string | number | null>>;
    prediction_accuracy?: {
      mae: number | null;
      bias: number | null;
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
