"""
monitoring.py
=============
Contrôle qualité des données + performance récente du modèle.

Usage : python -m src.models.monitoring
"""

import json
import logging
import pathlib

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.api.utils import get_df_fast
from src.models.features import FEATURE_COLUMNS, TARGET_COLUMN, InsufficientDataError, build_supervised_frame
from src.models.registry import load_model

logger = logging.getLogger(__name__)

MONITORING_REPORT_PATH = pathlib.Path("models/monitoring_report.json")
BASELINE_METRICS_PATH = pathlib.Path("models/metrics.json")
BACKTEST_DAYS = 7
STALE_AFTER = pd.Timedelta(days=3)


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def run_data_quality_checks(df: pd.DataFrame) -> dict:
    """Contrôles de qualité sur les données horaires."""
    checks = {
        "missing_values_pct": df.isnull().mean().to_dict(),
        "total_rows": int(len(df)),
        "last_update": df.index.max().isoformat() if not df.empty else None,
    }
    if "pm2_5" in df.columns:
        checks["pm25_range_violation"] = int(((df["pm2_5"] < 0) | (df["pm2_5"] > 500)).sum())
    return checks


def calculate_recent_performance(model, df: pd.DataFrame, n_days: int = BACKTEST_DAYS) -> dict | None:
    """Backtest sur les `n_days` derniers jours dont on connaît le lendemain.

    NB : si le modèle a été ré-entraîné après ces jours, ils font partie de son
    jeu d'entraînement et l'erreur est optimiste. Le monitoring a du sens sur
    les jours collectés APRÈS le dernier entraînement.
    """
    try:
        frame = build_supervised_frame(df).tail(n_days)
    except InsufficientDataError:
        return None
    if frame.empty:
        return None

    pred_delta = model.predict(frame[FEATURE_COLUMNS])
    actual = frame["pm2_5"] + frame[TARGET_COLUMN]
    predicted = frame["pm2_5"] + pred_delta

    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "mae_persistence": float(mean_absolute_error(actual, frame["pm2_5"])),
        "n_samples": int(len(frame)),
        "period_start": frame.index.min().strftime("%Y-%m-%d"),
        "period_end": frame.index.max().strftime("%Y-%m-%d"),
    }


def check_monitoring(model=None, df: pd.DataFrame | None = None) -> dict:
    """Produit et sauvegarde le rapport de monitoring."""
    df = get_df_fast() if df is None else df
    if model is None:
        model, _ = load_model()

    dq_report = run_data_quality_checks(df)
    perf_report = calculate_recent_performance(model, df) if model is not None else None

    baseline = {}
    if BASELINE_METRICS_PATH.exists():
        baseline = json.loads(BASELINE_METRICS_PATH.read_text())

    needs_retraining = False
    reasons, warnings = [], []

    if model is None:
        needs_retraining = True
        reasons.append("Aucun modèle compatible disponible")

    if perf_report and baseline.get("mae_pm25") is not None:
        # Seuil : +50 % d'erreur par rapport à la validation, avec un plancher à 5 µg/m³
        mae_threshold = max(baseline["mae_pm25"] * 1.5, 5.0)
        if perf_report["mae"] > mae_threshold:
            needs_retraining = True
            reasons.append(f"Dégradation de la performance (MAE: {perf_report['mae']:.2f} > seuil {mae_threshold:.2f})")

    if dq_report["missing_values_pct"].get("pm2_5", 0) > 0.1:
        warnings.append("Trop de données manquantes sur PM2.5 (> 10%)")

    if not df.empty and pd.Timestamp.now(tz="UTC") - df.index.max() > STALE_AFTER:
        warnings.append(f"Données périmées : dernière mesure le {df.index.max():%Y-%m-%d}")

    report = {
        "timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
        "data_quality": dq_report,
        "performance": perf_report,
        "baseline_comparison": baseline,
        "needs_retraining": needs_retraining,
        "reasons": reasons,
        "warnings": warnings,
    }

    MONITORING_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    MONITORING_REPORT_PATH.write_text(json.dumps(report, indent=4, cls=NpEncoder))
    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(check_monitoring(), indent=4, cls=NpEncoder))
