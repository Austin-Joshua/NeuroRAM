from neuroram.backend.os.collector import collect_system_metrics


def test_collect_system_metrics_has_required_keys():
    row = collect_system_metrics()
    assert "ram_percent" in row
    assert "cpu_percent" in row
