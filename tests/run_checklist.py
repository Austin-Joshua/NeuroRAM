from neuroram.backend.os.collector import collect_process_metrics, collect_system_metrics
from neuroram.backend.dbms.database import DatabaseManager
from neuroram.backend.mlt.ml_engine import MLEngine
from neuroram.backend.mlt.predictor import predict_next_ram
from neuroram.backend.daa.risk_analyzer import classify_risk, detect_memory_leak
from neuroram.backend.daa.optimizer import greedy_optimization_strategy
from neuroram.backend.daa.stability_index import compute_stability_index
import pandas as pd


def main() -> None:
    db = DatabaseManager()
    system_row = collect_system_metrics()
    process_rows = collect_process_metrics(limit=10)
    db.insert_system_metric(system_row)
    db.insert_process_metrics(process_rows)

    hist = db.fetch_system_metrics(limit=800)
    pred_hist = db.fetch_predictions(limit=200)

    ml = MLEngine()
    train_status = "skipped"
    pred = None
    err = None
    if len(hist) >= 40:
        try:
            train = ml.train_random_forest(hist)
            train_status = f"ok mae={train['mae']} rmse={train['rmse']} r2={train['r2']}"
            pred = predict_next_ram(hist, "rf")
            db.insert_prediction(system_row["timestamp"], "rf", pred, system_row["ram_percent"])
        except Exception as exc:
            err = str(exc)

    leak = detect_memory_leak(hist)
    effective = max(float(system_row["ram_percent"]), float(pred if pred is not None else system_row["ram_percent"]))
    risk = classify_risk(effective, leak)
    stability = compute_stability_index(
        float(system_row["ram_percent"]),
        float(system_row["swap_percent"]),
        risk.level,
    )
    recs = greedy_optimization_strategy(pd.DataFrame(process_rows), risk.level)
    db.insert_alert(system_row["timestamp"], risk.level.value, " | ".join(risk.reasons), stability)

    print("CHECKLIST_OK")
    print("system_ram", round(system_row["ram_percent"], 2), "proc_count", len(process_rows))
    print("db_system_rows", len(hist), "db_pred_rows", len(pred_hist))
    print("ml_train", train_status)
    print("ml_pred", "none" if pred is None else round(pred, 2), "ml_err", err)
    print("risk", risk.level.value, "leak", leak, "stability", stability, "recs", len(recs))
    print("top_rec", recs[0].process_name if recs else "none")


if __name__ == "__main__":
    main()
