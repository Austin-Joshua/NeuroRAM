from neuroram.backend.dbms.database import DatabaseManager


def test_db_initializes():
    db = DatabaseManager()
    status = db.get_index_status()
    assert isinstance(status, dict)
    assert "idx_device_logs_timestamp" in status


def test_db_extended_insert_fetch_paths():
    db = DatabaseManager()
    ts = "2026-01-01T00:00:00+00:00"
    db.insert_memory_log(ts, 64.2, 8048.0, 12.4, 3024.0)
    db.insert_device_logs(
        [
            {
                "timestamp": ts,
                "event_type": "connected",
                "device_type": "usb_drive",
                "device_name": "DemoUSB",
                "device_id": "demo_usb_1",
                "mountpoint": "E:/",
                "capacity_bytes": 64_000_000_000,
                "used_bytes": 10_000_000_000,
                "usage_percent": 15.6,
                "source_os": "windows",
                "is_connected": True,
            }
        ]
    )
    db.insert_prediction_log(ts, "rf", 66.1, 64.2)
    db.insert_analysis_result(ts, "WARNING", "Cause", "Do", "Dont", "RF", 77.7, 55.5)
    assert not db.fetch_memory_logs(limit=1).empty
    assert not db.fetch_device_logs(limit=1).empty
    assert not db.fetch_prediction_logs(limit=1).empty
    assert not db.fetch_analysis_results(limit=1).empty
