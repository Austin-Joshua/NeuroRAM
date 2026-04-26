"""Cross-platform external device monitoring utilities."""

from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Tuple

import psutil

try:
    import wmi  # type: ignore

    WMI_AVAILABLE = True
except Exception:
    WMI_AVAILABLE = False

try:
    import pyudev  # type: ignore

    PYUDEV_AVAILABLE = True
except Exception:
    PYUDEV_AVAILABLE = False


@dataclass
class DeviceSnapshot:
    timestamp: str
    device_type: str
    device_name: str
    device_id: str
    mountpoint: str | None
    capacity_bytes: int | None
    used_bytes: int | None
    usage_percent: float | None
    source_os: str
    is_connected: bool = True

    def to_log_row(self, event_type: str) -> Dict[str, object]:
        row = asdict(self)
        row["event_type"] = event_type
        return row


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_device_id(value: str) -> str:
    return value.strip().replace("\\", "_").replace("/", "_").replace(" ", "_")[:220]


def _classify_device(name: str) -> str:
    text = name.lower()
    if any(k in text for k in ("usb", "pendrive", "flash", "mass storage", "removable")):
        return "usb_drive"
    if any(k in text for k in ("wifi", "wi-fi", "wireless lan", "802.11")):
        return "wifi_dongle"
    if any(k in text for k in ("keyboard", "mouse", "hid", "receiver", "dongle")):
        return "input_dongle"
    return "external_device"


def _is_external_peripheral(name: str, pnp_id: str) -> bool:
    """
    Keep only likely external peripherals (USB receivers/dongles)
    and avoid classifying built-in/internal devices as external.
    """
    lowered_name = name.lower()
    lowered_id = pnp_id.lower()
    if any(k in lowered_name for k in ("dongle", "receiver", "usb")):
        return True
    return lowered_id.startswith("usb\\") or "vid_" in lowered_id


def _collect_storage_devices() -> List[DeviceSnapshot]:
    rows: List[DeviceSnapshot] = []
    ts = _now_iso()
    source = platform.system().lower()
    seen_ids: set[str] = set()

    # Cross-platform removable partition scan
    for part in psutil.disk_partitions(all=False):
        if not part.device:
            continue
        opts = (part.opts or "").lower()
        if not (
            "removable" in opts
            or "/media" in part.mountpoint.lower()
            or "/run/media" in part.mountpoint.lower()
            or "/Volumes" in part.mountpoint
        ):
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            device_id = _normalize_device_id(f"{part.device}_{part.mountpoint}")
            if device_id in seen_ids:
                continue
            seen_ids.add(device_id)
            rows.append(
                DeviceSnapshot(
                    timestamp=ts,
                    device_type="usb_drive",
                    device_name=part.device,
                    device_id=device_id,
                    mountpoint=part.mountpoint,
                    capacity_bytes=int(usage.total),
                    used_bytes=int(usage.used),
                    usage_percent=float(usage.percent),
                    source_os=source,
                )
            )
        except Exception:
            continue

    # Windows-specific removable drive detection is more reliable with DriveType=2.
    if source == "windows" and WMI_AVAILABLE:
        try:
            client = wmi.WMI()
            for drive in client.Win32_LogicalDisk(DriveType=2):
                mountpoint = str(getattr(drive, "DeviceID", "") or "").strip()
                if not mountpoint:
                    continue
                mount_path = f"{mountpoint}\\"
                try:
                    usage = psutil.disk_usage(mount_path)
                except Exception:
                    usage = None
                device_id = _normalize_device_id(f"removable_{mountpoint}")
                if device_id in seen_ids:
                    continue
                seen_ids.add(device_id)
                rows.append(
                    DeviceSnapshot(
                        timestamp=ts,
                        device_type="usb_drive",
                        device_name=f"Removable Drive {mountpoint}",
                        device_id=device_id,
                        mountpoint=mount_path,
                        capacity_bytes=int(usage.total) if usage else None,
                        used_bytes=int(usage.used) if usage else None,
                        usage_percent=float(usage.percent) if usage else None,
                        source_os=source,
                    )
                )
        except Exception:
            pass

    return rows


def _collect_windows_pnp_devices() -> List[DeviceSnapshot]:
    if platform.system().lower() != "windows" or not WMI_AVAILABLE:
        return []
    ts = _now_iso()
    source = "windows"
    rows: List[DeviceSnapshot] = []
    try:
        client = wmi.WMI()
        for item in client.Win32_PnPEntity():
            present = getattr(item, "Present", True)
            if present is False:
                continue
            name = str(getattr(item, "Name", "") or "")
            if not name:
                continue
            dtype = _classify_device(name)
            if dtype == "external_device":
                continue
            pnp_id = str(getattr(item, "PNPDeviceID", "") or name)
            if not _is_external_peripheral(name, pnp_id):
                continue
            rows.append(
                DeviceSnapshot(
                    timestamp=ts,
                    device_type=dtype,
                    device_name=name[:160],
                    device_id=_normalize_device_id(pnp_id),
                    mountpoint=None,
                    capacity_bytes=None,
                    used_bytes=None,
                    usage_percent=None,
                    source_os=source,
                )
            )
    except Exception:
        return rows
    return rows


def _collect_linux_udev_devices() -> List[DeviceSnapshot]:
    if platform.system().lower() != "linux" or not PYUDEV_AVAILABLE:
        return []
    ts = _now_iso()
    rows: List[DeviceSnapshot] = []
    try:
        context = pyudev.Context()
        for device in context.list_devices(subsystem="usb"):
            name = str(device.get("ID_MODEL", "") or device.get("ID_MODEL_FROM_DATABASE", "") or "USB Device")
            dtype = _classify_device(name)
            if dtype == "external_device":
                continue
            devnode = str(device.device_node or device.get("DEVPATH", "") or name)
            rows.append(
                DeviceSnapshot(
                    timestamp=ts,
                    device_type=dtype,
                    device_name=name[:160],
                    device_id=_normalize_device_id(devnode),
                    mountpoint=None,
                    capacity_bytes=None,
                    used_bytes=None,
                    usage_percent=None,
                    source_os="linux",
                )
            )
    except Exception:
        return rows
    return rows


def _collect_macos_usb_devices() -> List[DeviceSnapshot]:
    if platform.system().lower() != "darwin":
        return []
    ts = _now_iso()
    rows: List[DeviceSnapshot] = []
    try:
        raw = subprocess.check_output(["system_profiler", "SPUSBDataType", "-json"], text=True, timeout=4)
        parsed = json.loads(raw)
    except Exception:
        return rows

    def walk(items: Iterable[dict]) -> Iterable[dict]:
        for item in items:
            yield item
            children = item.get("_items", []) if isinstance(item, dict) else []
            if children:
                yield from walk(children)

    for item in walk(parsed.get("SPUSBDataType", [])):
        if not isinstance(item, dict):
            continue
        name = str(item.get("_name", "") or item.get("manufacturer", "") or "")
        if not name:
            continue
        dtype = _classify_device(name)
        if dtype == "external_device":
            continue
        dev_id = str(item.get("serial_num", "") or item.get("vendor_id", "") or name)
        rows.append(
            DeviceSnapshot(
                timestamp=ts,
                device_type=dtype,
                device_name=name[:160],
                device_id=_normalize_device_id(dev_id),
                mountpoint=None,
                capacity_bytes=None,
                used_bytes=None,
                usage_percent=None,
                source_os="darwin",
            )
        )
    return rows


def collect_external_devices(include_peripheral_devices: bool = False) -> List[DeviceSnapshot]:
    """
    Collect currently connected external devices.

    By default this is strict and storage-focused (USB/removable drives).
    Set include_peripheral_devices=True to include PnP/USB peripheral heuristics.
    """
    all_devices: Dict[str, DeviceSnapshot] = {}
    for row in _collect_storage_devices():
        all_devices[row.device_id] = row
    if include_peripheral_devices:
        for row in _collect_windows_pnp_devices():
            all_devices[row.device_id] = row
        for row in _collect_linux_udev_devices():
            all_devices[row.device_id] = row
        for row in _collect_macos_usb_devices():
            all_devices[row.device_id] = row
    return list(all_devices.values())


def detect_device_events(
    current_devices: Iterable[DeviceSnapshot],
    previous_devices: Dict[str, DeviceSnapshot] | None = None,
) -> Tuple[List[Dict[str, object]], Dict[str, DeviceSnapshot]]:
    """
    Compare current and previous device states and emit connected/disconnected events.

    Returns tuple of (event_rows, current_state_map).
    """
    previous = previous_devices or {}
    current_map = {d.device_id: d for d in current_devices}
    events: List[Dict[str, object]] = []

    for dev_id, dev in current_map.items():
        if dev_id not in previous:
            events.append(dev.to_log_row("connected"))
        else:
            events.append(dev.to_log_row("snapshot"))

    for dev_id, prev_dev in previous.items():
        if dev_id not in current_map:
            disconnected = DeviceSnapshot(
                timestamp=_now_iso(),
                device_type=prev_dev.device_type,
                device_name=prev_dev.device_name,
                device_id=prev_dev.device_id,
                mountpoint=prev_dev.mountpoint,
                capacity_bytes=prev_dev.capacity_bytes,
                used_bytes=prev_dev.used_bytes,
                usage_percent=prev_dev.usage_percent,
                source_os=prev_dev.source_os,
                is_connected=False,
            )
            events.append(disconnected.to_log_row("disconnected"))

    return events, current_map
