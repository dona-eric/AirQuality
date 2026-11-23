"""
train.py
========
Entraînement du modèle XGBoost de prévision du PM2.5 à J+1.

Usage :
    python -m src.models.train                 # entraîne, évalue, sauvegarde
    python -m src.models.train --no-tracking   # sans MLflow / DagsHub
    python -m src.models.train --no-push       # sans publication HuggingFace

Étapes :
  1. Features + cible (src/models/features.py)
  2. Split chronologique 80/20 → métriques sur la période la plus récente,
     comparées à la baseline de persistance (« demain = aujourd'hui »)
  3. Ré-entraînement sur 100 % des données → modèle de production
  4. Sauvegarde : models/xgb_model.json, models/metrics.json, models/validation_plot.png
  5. Optionnel : MLflow (si DAGSHUB_TOKEN ou MLFLOW_TRACKING_URI) et HF (si HF_TOKEN)
"""

import argparse
import json
import logging
import os
import pathlib
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import xgboost as xgb
import yaml
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.models.features import build_training_frame
from src.models.registry import LOCAL_MODEL_PATH, push_model_to_hf, save_model

logger = logging.getLogger(__name__)

PARAMS_PATH = pathlib.Path("params.yml")
METRICS_PATH = pathlib.Path("models/metrics.json")
PLOT_PATH = pathlib.Path("models/validation_plot.png")
TEST_RATIO = 0.2
MLFLOW_EXPERIMENT = "Xgboost_AirQuality_V3"
REGISTERED_MODEL_NAME = "AirQualityXGBoostModel"

# n_jobs=1 : sur ~200 lignes, le multithreading XGBoost est contre-productif
# (contention observée : 145 s au lieu de 4 s).
DEFAULT_PARAMS = {"n_estimators": 300, "learning_rate": 0.03, "max_depth": 2, "subsample": 0.8, "n_jobs": 1}


# ===================== ENTRAÎNEMENT (pur, testable) =====================

def load_params(path: pathlib.Path = PARAMS_PATH) -> dict:
    if not path.exists():
        return dict(DEFAULT_PARAMS)
    with open(path) as f:
        return {**DEFAULT_PARAMS, **(yaml.safe_load(f) or {}).get("model_params", {})}


def make_model(params: dict) -> xgb.XGBRegressor:
    return xgb.XGBRegressor(objective="reg:squarederror", random_state=42, **params)


def train_model(df_hourly: pd.DataFrame, params: dict, test_ratio: float = TEST_RATIO):
    """Renvoie (modèle_production, métriques, données_validation)."""
    X, y = build_training_frame(df_hourly)

    split_idx = int(len(X) * (1 - test_ratio))
    if split_idx < 10 or len(X) - split_idx < 2:
        raise ValueError(f"Pas assez de jours pour entraîner/évaluer ({len(X)} jours).")

    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    eval_model = make_model(params).fit(X_train, y_train)
    y_pred = eval_model.predict(X_test)

    # Erreur sur le delta == erreur sur le niveau PM2.5 (même valeur actuelle ajoutée)
    metrics = {
        "mae_pm25": float(mean_absolute_error(y_test, y_pred)),
        "rmse_pm25": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "r2_delta": float(r2_score(y_test, y_pred)),
        "mae_persistence": float(mean_absolute_error(y_test, np.zeros_like(y_pred))),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "test_start": X_test.index.min().strftime("%Y-%m-%d"),
        "test_end": X_test.index.max().strftime("%Y-%m-%d"),
    }
    metrics["skill_vs_persistence"] = (
        1 - metrics["mae_pm25"] / metrics["mae_persistence"] if metrics["mae_persistence"] else 0.0
    )

    # Modèle de production : toutes les données, y compris la période la plus récente
    final_model = make_model(params).fit(X, y)
    return final_model, metrics, (X_test, y_test, y_pred)


# ===================== ARTEFACTS =====================

def save_validation_plot(y_test: pd.Series, y_pred: np.ndarray, mae: float, path: pathlib.Path = PLOT_PATH):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(y_test.index, y_test.values, label="Réel (Δ PM2.5 J+1)")
    ax.plot(y_test.index, y_pred, label="Prédit (Δ PM2.5 J+1)", alpha=0.7)
    ax.axhline(0, color="grey", lw=0.8, ls="--")
    ax.set_title(f"Validation — MAE: {mae:.2f} µg/m³")
    ax.legend()
    fig.autofmt_xdate()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def _setup_tracking() -> bool:
    if os.getenv("DAGSHUB_TOKEN"):
        import dagshub

        dagshub.init(repo_owner="dona-eric", repo_name="air-quality", mlflow=True)
        return True
    return bool(os.getenv("MLFLOW_TRACKING_URI"))


def log_to_mlflow(model, params, metrics, X_test, y_test, version_tag):
    """Trace le run dans MLflow. Ne fait jamais échouer l'entraînement."""
    try:
        if not _setup_tracking():
            logger.info("Pas de DAGSHUB_TOKEN / MLFLOW_TRACKING_URI : tracking MLflow ignoré.")
            return
        import mlflow
        import mlflow.xgboost

        mlflow.set_experiment(MLFLOW_EXPERIMENT)
        with mlflow.start_run(run_name=f"XGBoost-{version_tag}") as run:
            mlflow.log_params(params)
            mlflow.log_metrics({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
            mlflow.log_artifact(str(PLOT_PATH))
            signature = mlflow.models.signature.infer_signature(X_test, model.predict(X_test))
            mlflow.xgboost.log_model(
                xgb_model=model,
                name="xgboost_model",
                model_format="json",
                signature=signature,
                registered_model_name=REGISTERED_MODEL_NAME,
            )
            logger.info("Run MLflow : %s", run.info.run_id)

        client = mlflow.MlflowClient()
        versions = client.search_model_versions(f"name='{REGISTERED_MODEL_NAME}'")
        if versions:
            latest = max(versions, key=lambda v: int(v.version))
            client.set_registered_model_alias(REGISTERED_MODEL_NAME, "champion", latest.version)
            client.set_model_version_tag(REGISTERED_MODEL_NAME, latest.version, "version_tag", version_tag)
            logger.info("Alias 'champion' → version %s", latest.version)
    except Exception as e:
        logger.error("Tracking MLflow échoué (le modèle local est quand même sauvegardé) : %s", e)


# ===================== ENTRYPOINT =====================

def main(argv=None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-tracking", action="store_true", help="désactive MLflow / DagsHub")
    parser.add_argument("--no-push", action="store_true", help="désactive la publication HuggingFace")
    args = parser.parse_args(argv)

    import dotenv

    from src.api.utils import get_df_fast

    dotenv.load_dotenv()

    df = get_df_fast()
    params = load_params()
    version_tag = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")

    model, metrics, (X_test, y_test, y_pred) = train_model(df, params)
    metrics.update({
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "version_tag": version_tag,
        "data_last_update": df.index.max().isoformat(),
    })

    save_model(model, LOCAL_MODEL_PATH)
    save_validation_plot(y_test, y_pred, metrics["mae_pm25"])
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))

    logger.info(
        "MAE PM2.5 J+1 = %.2f µg/m³ (persistance : %.2f, gain : %.0f %%)",
        metrics["mae_pm25"], metrics["mae_persistence"], 100 * metrics["skill_vs_persistence"],
    )

    if not args.no_tracking:
        log_to_mlflow(model, params, metrics, X_test, y_test, version_tag)
    if not args.no_push:
        push_model_to_hf(LOCAL_MODEL_PATH, version_tag)

    return metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    print(json.dumps(main(), indent=2))
