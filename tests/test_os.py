from backend.OS.collector import collect_system_metrics
from backend.OS.device_monitor import collect_external_devices, detect_device_events


def test_collect_system_metrics_has_required_keys():
    row = collect_system_metrics()
    assert "ram_percent" in row
    assert "available_mb" in row


def test_device_monitor_contract():
    devices = collect_external_devices()
    events, state = detect_device_events(devices, previous_devices={})
    assert isinstance(events, list)
    assert isinstance(state, dict)
