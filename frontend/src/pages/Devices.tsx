import type { DashboardPayload } from "../services/api";
import { DeviceActivityChart } from "../components/charts/Charts";
import { getGraphInsight } from "../utils/chartInsights";

type Props = { payload: DashboardPayload };

function storageSummary(storage: DashboardPayload["devices"]["storage"]) {
  let usedSum = 0;
  let capSum = 0;
  let files = 0;
  for (const d of storage) {
    if (d.used_gb != null) usedSum += d.used_gb;
    if (d.capacity_gb != null) capSum += d.capacity_gb;
    if (d.file_count != null) files += d.file_count;
  }
  const parts: string[] = [];
  if (capSum > 0) parts.push(`Pooled capacity ~${capSum.toFixed(1)} GB`);
  if (usedSum > 0) parts.push(`Used ~${usedSum.toFixed(1)} GB`);
  if (files > 0) parts.push(`Indexed files (sample scan) ~${files}`);
  return parts.length ? parts.join(" · ") : null;
}

export function DevicesPage({ payload }: Props) {
  const activityRows = payload.trends.device_activity.slice(-160).map((r) => ({
    ...r,
    active_devices: Number(r.active_devices) || 0,
    connected_events: Number(r.connected_events) || 0,
    disconnected_events: Number(r.disconnected_events) || 0,
  }));
  const summary = storageSummary(payload.devices.storage);
  const timeline = payload.devices.timeline.slice(0, 80);

  return (
    <div className="page-grid">
      <section className="panel">
        <h2>Device Intelligence</h2>
        <p className="panel-copy">
          Live storage and peripheral telemetry with timeline awareness. Track utilization, connection churn, and attachment behavior.
        </p>
      </section>
      {summary ? (
        <div className="device-summary-bar">
          <strong>Storage snapshot:</strong> <span>{summary}</span>
        </div>
      ) : null}
      <section className="panel">
        <h2>Connected Devices</h2>
        <div className="device-grid">
          {payload.devices.connected.length === 0 ? <p>No external devices connected.</p> : null}
          {payload.devices.connected.map((device) => (
            <article className="device-card" key={`${device.device_id}-${device.timestamp}`}>
              <h3>{device.device_name || device.device_id}</h3>
              <p>Type: {device.device_group}</p>
              <p>Status: connected</p>
              <p>Total: {device.capacity_gb == null ? "N/A" : `${device.capacity_gb} GB`}</p>
              <p>Used: {device.used_gb == null ? "N/A" : `${device.used_gb} GB`}</p>
              <p>Free: {device.free_gb == null ? "N/A" : `${device.free_gb} GB`}</p>
              <p>Usage %: {device.usage_percent == null ? "N/A" : `${device.usage_percent}%`}</p>
              <p>Files (sample): {device.file_count == null ? "N/A" : device.file_count}</p>
              <p>Folders (sample): {device.folder_count == null ? "N/A" : device.folder_count}</p>
            </article>
          ))}
        </div>
      </section>
      <DeviceActivityChart rows={activityRows} insight={getGraphInsight(payload, "device_activity")} />
      <section className="panel">
        <h2>Connection timeline</h2>
        <p className="panel-copy">Recent connect and disconnect events (newest first).</p>
        {timeline.length === 0 ? <p>No recent events.</p> : null}
        <div className="device-timeline">
          {timeline.map((row, idx) => {
            const off = String(row.event_type).toLowerCase() === "disconnected";
            return (
              <div key={`${row.device_id}-${row.timestamp}-${idx}`} className={`device-timeline-item ${off ? "is-off" : ""}`}>
                <span className="device-timeline-dot" aria-hidden />
                <div>
                  <strong>{row.timestamp}</strong>
                  <div>
                    {row.event_type} · {row.device_name || row.device_id}
                  </div>
                  <div className="panel-copy" style={{ marginTop: "0.25rem" }}>
                    {row.device_group}
                    {row.mountpoint ? ` · ${row.mountpoint}` : ""}
                    {row.usage_percent != null ? ` · usage ${row.usage_percent}%` : ""}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>
      <section className="panel">
        <h2>Event history (table)</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Event</th>
                <th>Device</th>
                <th>Type</th>
                <th>Usage %</th>
              </tr>
            </thead>
            <tbody>
              {payload.devices.timeline.slice(0, 120).map((row, idx) => (
                <tr key={`${row.device_id}-${row.timestamp}-${idx}`}>
                  <td>{row.timestamp}</td>
                  <td>{row.event_type}</td>
                  <td>{row.device_name || row.device_id}</td>
                  <td>{row.device_group}</td>
                  <td>{row.usage_percent == null ? "—" : `${row.usage_percent}%`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
