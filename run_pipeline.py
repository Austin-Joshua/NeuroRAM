"""Backward-compatible MLT trainer re-export."""

from neuroram.backend.mlt.trainer import *  # noqa: F403


if __name__ == "__main__":
    from neuroram.backend.mlt.trainer import collect_samples, train_models
    from neuroram.config.config import CONFIG

    collect_samples(sample_count=40, interval_sec=CONFIG.collection_interval_sec)
    train_models(train_lstm=False)
