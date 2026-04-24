from neuroram.backend.mlt.ml_engine import MLEngine


def test_ml_engine_constructs():
    engine = MLEngine()
    assert engine is not None
