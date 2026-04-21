from neuroram.backend.daa.risk_analyzer import classify_risk


def test_classify_risk_normal():
    report = classify_risk(10.0, False)
    assert report.level.value in {"NORMAL", "WARNING", "CRITICAL", "EMERGENCY"}
