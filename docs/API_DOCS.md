# NeuroRAM API Documentation

## Base URL

- Local backend: `http://localhost:8000`

## Endpoints

### `GET /api/health`

Returns service and pipeline heartbeat status.

### `GET /api/pipeline/status`

Returns background pipeline runtime metadata.

### `GET /api/dashboard`

Primary structured payload for the React dashboard.

Top-level keys:

- `metrics`
- `devices`
- `trends`
- `analysis`
- `recommendations`

## Sample response (`/api/dashboard`)

```json
{
  "ready": true,
  "timestamp_utc": "2026-04-24T10:35:00.000000+00:00",
  "metrics": {
    "ram_now_percent": 67.2,
    "predicted_ram_percent": 69.1,
    "stability_score": 74.8,
    "risk_level": "WARNING",
    "health_category": "degrading",
    "connected_devices": 2,
    "connected_storage": 1,
    "connected_dongles": 1,
    "connected_network_adapters": 0,
    "pipeline": {
      "running": true,
      "cycles": 412,
      "last_cycle_utc": "2026-04-24T10:34:58.000000+00:00",
      "last_success_utc": "2026-04-24T10:34:58.000000+00:00",
      "last_cycle_duration_ms": 83.4,
      "last_error": null,
      "last_prediction": 69.1
    }
  },
  "devices": {
    "connected": [],
    "storage": [],
    "dongles": [],
    "network_adapters": [],
    "timeline": []
  },
  "trends": {
    "memory": [],
    "prediction": [],
    "stability": [],
    "device_activity": []
  },
  "analysis": {
    "summary": "Current RAM is 67.2%. Risk is WARNING and health category is degrading.",
    "what_why_how": {
      "what": "Memory pressure is being monitored for spikes, leak tendencies, and process inefficiency.",
      "why": "Short-term RAM jumps were detected between consecutive cycles.",
      "how_serious": "WARNING operational risk with medium pattern severity; stability score 72.0/100.",
      "impact": "Same plain-language impact line as how_serious for product UI (impact on system)."
    },
    "algorithm": "ML (RandomForest) + DAA (risk classification, stability indexing, greedy optimization)",
    "reasons": [],
    "memory_patterns": {
      "spike_detected": true,
      "gradual_leak_detected": false,
      "abnormal_pattern": false,
      "predicted_vs_actual_mae": 0.58,
      "predicted_vs_actual_bias": 0.12,
      "severity": "medium",
      "explanations": ["Short-term RAM jumps were detected between consecutive cycles."],
      "spike_timestamps": ["2026-04-24 10:12:00"]
    },
    "narrative": "Human-readable paragraph combining RAM level, risk, patterns, devices, and top reasons.",
    "graph_insights": {
      "memory": {
        "what": "RAM and swap usage moved noticeably in the recent window.",
        "why": "Sharp step changes in RAM percent were detected.",
        "next": "Near-term usage is likely to track recent levels unless workload mix changes."
      },
      "prediction": { "what": "...", "why": "...", "next": "..." },
      "stability": { "what": "...", "why": "...", "next": "..." },
      "device_activity": { "what": "...", "why": "...", "next": "..." }
    },
    "inefficient_processes": [],
    "processes": [],
    "logs_preview": []
  },
  "recommendations": {
    "category": "degrading",
    "dos": [],
    "donts": [],
    "prioritized_actions": []
  }
}
```

## Field notes

- Numeric trend fields may be `null` when values are unavailable.
- `ready=false` returns the same top-level structure with safe defaults.
- `analysis.what_why_how` is designed for human-readable UI rendering (`impact` mirrors severity for “impact on system” panels).
- `analysis.narrative` is a single reviewer-facing paragraph (may overlap summary; UI may dedupe).
- `analysis.graph_insights` supplies per-chart story blocks. Fields are `what`, `why`, and `next` (the React UI labels the third line **What it means**).
- Forecast error metrics live only under `analysis.memory_patterns` (`predicted_vs_actual_mae` / `predicted_vs_actual_bias`) to avoid duplicate keys.
- `analysis.memory_patterns.spike_timestamps` lists sample timestamps where a RAM spike was detected (for chart annotations).
- `metrics.pipeline` tracks runtime loop health and timing.

## Polling guidance

- Frontend default polling interval: 5 seconds.
- Retry interval after API error: 9 seconds.
