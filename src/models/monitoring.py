import pandas as pd
import json
import pathlib
import logging
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np
import joblib
from src.api.utils import get_df_fast

logger = logging.getLogger(__name__)

MONITORING_REPORT_PATH = pathlib.Path("models/monitoring_report.json")
BASELINE_METRICS_PATH = pathlib.Path("models/metrics.json")
MODEL_PATH = pathlib.Path("models/air_quality.pkl")

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

def run_data_quality_checks(df):
    """Effectue des contrôles de qualité sur les données les plus récentes."""
    checks = {
        "missing_values_pct": df.isnull().mean().to_dict(),
        "total_rows": int(len(df)),
        "last_update": df.index.max().isoformat() if not df.empty else None,
        "anomalies_detected": 0
    }

    if "pm2_5" in df.columns:
        checks["pm25_range_violation"] = int(((df["pm2_5"] < 0) | (df["pm2_5"] > 500)).sum())

    return checks

def calculate_recent_performance():
    """
    Calcule la performance du modèle sur les données récentes en faisant un backtest.
    On essaie de prédire le PM2.5 de demain à partir des données d'aujourd'hui.
    """
    try:
        df = get_df_fast()
        if df.empty:
            return None

        model = joblib.load(MODEL_PATH)

        # Préparation des données journalières
        df_daily = df.resample('D').mean(numeric_only=True).interpolate()

        # On prend les 14 derniers jours pour tester les 7 derniers jours (besoin de lags)
        # On veut prédire les jours T-6 à T (7 jours)
        # Pour prédire T, on a besoin de T-1, T-2, T-3, T-7 (rolling)

        results = []
        # On parcourt les 7 derniers jours disponibles en tant que "cible"
        for i in range(0, 7):
            # Cible est à l'index -1-i
            target_idx = len(df_daily) - 1 - i
            if target_idx < 7: break

            # Données d'entrée (jusqu'à la veille de la cible)
            input_data_end_idx = target_idx # .iloc[:target_idx] s'arrête à target_idx-1
            subset = df_daily.iloc[:input_data_end_idx].copy()

            # Feature Engineering
            for lag in range(1, 4):
                subset[f'pm25_lag_{lag}'] = subset['pm2_5'].shift(lag)
                subset[f'co_lag_{lag}'] = subset['carbon_monoxide'].shift(lag)
            subset['pm25_rolling_7d'] = subset['pm2_5'].rolling(window=7).mean()
            subset['day_of_week'] = subset.index.dayofweek
            subset['month'] = subset.index.month

            X_input = subset.tail(1).drop(columns=['formaldehyde', 'id', 'pm25_diff'], errors='ignore')

            if hasattr(model, 'feature_names_in_'):
                # S'assurer que toutes les colonnes requises sont présentes
                missing_cols = set(model.feature_names_in_) - set(X_input.columns)
                for c in missing_cols:
                    X_input[c] = np.nan
                X_input = X_input[model.feature_names_in_]

            if X_input.isnull().values.any():
                continue

            current_pm25 = subset['pm2_5'].iloc[-1]
            actual_pm25_target_day = df_daily['pm2_5'].iloc[target_idx]

            pred_delta = model.predict(X_input)[0]
            predicted_pm25 = current_pm25 + pred_delta

            results.append({
                "actual_pm25": actual_pm25_target_day,
                "predicted_pm25": predicted_pm25
            })

        if not results:
            return None

        res_df = pd.DataFrame(results)
        metrics = {
            "mae": float(mean_absolute_error(res_df["actual_pm25"], res_df["predicted_pm25"])),
            "rmse": float(np.sqrt(mean_squared_error(res_df["actual_pm25"], res_df["predicted_pm25"]))),
            "n_samples": len(results)
        }
        return metrics
    except Exception as e:
        logger.error(f"Erreur calcul performance : {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def check_monitoring():
    """Fonction principale de monitoring."""
    df = get_df_fast()

    dq_report = run_data_quality_checks(df)
    perf_report = calculate_recent_performance()

    baseline = {}
    if BASELINE_METRICS_PATH.exists():
        with open(BASELINE_METRICS_PATH, "r") as f:
            baseline = json.load(f)

    # Décision de ré-entraînement
    needs_retraining = False
    reasons = []

    if perf_report and baseline:
        # Seuil de tolérance : 50% d'augmentation de l'erreur ou MAE > 5
        mae_threshold = max(baseline.get("mae_pm25", 2.0) * 1.5, 5.0)
        if perf_report["mae"] > mae_threshold:
            needs_retraining = True
            reasons.append(f"Dégradation de la performance (MAE: {perf_report['mae']:.2f} > seuil {mae_threshold:.2f})")

    if dq_report["missing_values_pct"].get("pm2_5", 0) > 0.1:
        reasons.append("Trop de données manquantes sur PM2.5 (> 10%)")

    report = {
        "timestamp": pd.Timestamp.now(tz='UTC').isoformat(),
        "data_quality": dq_report,
        "performance": perf_report,
        "baseline_comparison": baseline,
        "needs_retraining": needs_retraining,
        "reasons": reasons
    }

    # S'assurer que le dossier parent existe
    MONITORING_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(MONITORING_REPORT_PATH, "w") as f:
        json.dump(report, f, indent=4, cls=NpEncoder)

    return report

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(check_monitoring(), indent=4, cls=NpEncoder))
