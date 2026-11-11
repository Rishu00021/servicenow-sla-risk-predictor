"""Smoke tests for the ServiceNow SLA Risk Predictor."""
import json
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def test_tickets_csv_exists_and_has_rows():
    df = pd.read_csv(ROOT / "data" / "tickets.csv")
    assert len(df) >= 1000
    assert {"ticket_id", "short_description", "priority", "sla_breach"} <= set(df.columns)
    assert df["sla_breach"].isin([0, 1]).all()
    assert 0.05 < df["sla_breach"].mean() < 0.6


def test_metrics_json_present_and_sane():
    metrics = json.loads((ROOT / "results" / "metrics.json").read_text())
    assert metrics["roc_auc"] > 0.60, metrics
    assert metrics["f1"] > 0.30, metrics
    assert metrics["n_tickets"] >= 1000


def test_model_file_exists():
    assert (ROOT / "models" / "sla_breach_model.joblib").exists()


def test_db_loaded():
    db = ROOT / "data" / "tickets.db"
    assert db.exists()
    conn = sqlite3.connect(db)
    n = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    assert n >= 1000
    views = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='view'")}
    assert "vw_mttr_by_group" in views
    assert "vw_breach_rate_by_priority" in views
    conn.close()


def test_charts_exist():
    assert (ROOT / "docs" / "breach_rate_by_priority.png").exists()
    assert (ROOT / "docs" / "feature_importance.png").exists()


def test_app_imports():
    import importlib.util
    spec = importlib.util.spec_from_file_location("app", ROOT / "app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "load_data")
