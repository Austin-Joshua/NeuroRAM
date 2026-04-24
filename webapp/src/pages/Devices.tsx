import type { DashboardPayload } from "../services/api";
import { DeviceActivityChart } from "../components/charts/Charts";

type Props = { payload: DashboardPayload };

export function DevicesPage({ payload }: Props) {
  const activityRows = payload.trends.device_activity.slice(-160).map((r) => ({
    ...r,
    active_devices: Number(r.active_devices) || 0,
    connected_events: Number(r.connected_events) || 0,
    disconnected_events: Number(r.disconnected_events) || 0,
  }));
  return (
    <div className="page-grid">
      <section className="panel">
        <h2>Device Intelligence</h2>
        <p className="panel-copy">
          Live storage and peripheral telemetry with timeline awareness. Track utilization, connection churn, and attachment behavior.
        </p>
      </section>
      <section className="panel">
        <h2>Connected Devices</h2>
        <div className="device-grid">
          {payload.devices.connected.length === 0 ? <p>No external devices connected.</p> : null}
          {payload.devices.connected.map((device) => (
            <article className="device-card" key={`${device.device_id}-${device.timestamp}`}>
              <h3>{device.device_name || device.device_id}</h3>
              <p>Type: {device.device_group}</p>
              <p>Status: connected</p>
              <p>Total: {device.capacity_gb === "" ? "N/A" : `${device.capacity_gb} GB`}</p>
              <p>Used: {device.used_gb === "" ? "N/A" : `${device.used_gb} GB`}</p>
              <p>Free: {device.free_gb === "" ? "N/A" : `${device.free_gb} GB`}</p>
              <p>Usage %: {device.usage_percent === "" ? "N/A" : `${device.usage_percent}%`}</p>
              <p>Files: {device.file_count == null ? "N/A" : device.file_count}</p>
              <p>Folders: {device.folder_count == null ? "N/A" : device.folder_count}</p>
            </article>
          ))}
        </div>
      </section>
      <DeviceActivityChart rows={activityRows} />
      <section className="panel">
        <h2>Connection Timeline</h2>
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
                  <td>{String((row as unknown as Record<string, string | number>)["usage_percent"] ?? "-")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
