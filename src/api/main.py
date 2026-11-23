"""
main.py
=======
API FastAPI — prévision du PM2.5 à J+1 à Cotonou.

Lancement : uvicorn src.api.main:app --host 0.0.0.0 --port 7860

Variables d'environnement :
  MODEL_VERSION         "latest" (défaut) ou tag HF (voir src/models/registry.py)
  ENABLE_ETL_SCHEDULER  "1" pour synchroniser HF + collecter Open-Meteo toutes les 12 h
  HF_TOKEN              accès au dataset HF (données + modèle)
"""

import json
import logging
import os
import pathlib
import threading
from contextlib import asynccontextmanager

import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException, Query

from src.api.schemas import DataResponse, HealthResponse, HistoryResponse, PredictionResponse
from src.api.utils import download_data_from_hf, etl_task_if_needed, get_df_fast
from src.models.features import InsufficientDataError
from src.models.inference import predict_next_day
from src.models.registry import load_model

logger = logging.getLogger(__name__)

MONITORING_REPORT_PATH = pathlib.Path("models/monitoring_report.json")
ETL_CHECK_HOURS = 12

# État partagé, rempli au démarrage (lifespan) — modifiable dans les tests
state = {"model": None, "model_source": None, "scheduler": None}


def _start_etl_scheduler():
    from apscheduler.schedulers.background import BackgroundScheduler

    def bootstrap():
        download_data_from_hf()
        etl_task_if_needed()

    # Premier passage en arrière-plan pour ne pas bloquer le démarrage
    threading.Thread(target=bootstrap, daemon=True).start()

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(etl_task_if_needed, "interval", hours=ETL_CHECK_HOURS,
                      id="etl", max_instances=1, coalesce=True)
    scheduler.start()
    logger.info("Scheduler ETL démarré (vérification toutes les %d h)", ETL_CHECK_HOURS)
    return scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    state["model"], state["model_source"] = load_model()
    if state["model"] is None:
        logger.error("Aucun modèle chargé : /predict renverra 503.")
    else:
        logger.info("Modèle chargé (%s)", state["model_source"])

    if os.getenv("ENABLE_ETL_SCHEDULER", "0").lower() in ("1", "true", "yes"):
        state["scheduler"] = _start_etl_scheduler()
    yield
    if state["scheduler"]:
        state["scheduler"].shutdown(wait=False)


app = FastAPI(
    title="Cotonou Air Quality API",
    description="Prévision du PM2.5 moyen à J+1",
    lifespan=lifespan,
)


def _load_data():
    df = get_df_fast()
    if df.empty:
        raise HTTPException(status_code=503, detail="Aucune donnée disponible. Lancez l'ETL.")
    return df


@app.get("/")
def home():
    return {
        "status": "online",
        "model_loaded": state["model"] is not None,
        "message": "API de prévision de la qualité de l'air à Cotonou",
    }


@app.get("/health", response_model=HealthResponse)
def health():
    df = get_df_fast()
    return {
        "status": "ok",
        "model_loaded": state["model"] is not None,
        "model_source": state["model_source"],
        "data_rows": int(len(df)),
        "data_last_update": df.index.max().isoformat() if not df.empty else None,
    }


@app.get("/data", response_model=DataResponse)
def get_data(days: int | None = Query(None, ge=1, description="Limiter aux N derniers jours")):
    """Mesures horaires brutes (utilisées par le frontend Streamlit)."""
    df = _load_data()
    if days:
        df = df[df.index >= df.index.max() - np.timedelta64(days, "D")]
    out = df.drop(columns=["id", "created_at"], errors="ignore").reset_index()
    out["date"] = out["date"].map(lambda d: d.isoformat())
    out = out.astype(object).where(out.notna(), None)
    return {"count": len(out), "records": out.to_dict(orient="records")}


@app.get("/history", response_model=HistoryResponse)
def get_history():
    """Moyenne journalière du PM2.5 sur les 7 derniers jours."""
    df = _load_data()
    daily = df["pm2_5"].resample("D").mean().tail(7)
    return {
        "dates": [d.strftime("%Y-%m-%d") for d in daily.index],
        "values": [None if np.isnan(v) else round(float(v), 2) for v in daily],
    }


@app.api_route("/predict", methods=["GET", "POST"], response_model=PredictionResponse)
def predict():
    if state["model"] is None:
        raise HTTPException(status_code=503, detail="Modèle non disponible. Entraînez-le : python -m src.models.train")
    df = _load_data()
    try:
        result = predict_next_day(state["model"], df)
    except InsufficientDataError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Erreur de prédiction")
        raise HTTPException(status_code=500, detail=str(e))
    return {**result, "model_source": state["model_source"]}


@app.get("/monitoring")
def get_monitoring(refresh: bool = False):
    """Dernier rapport de monitoring (recalculé si absent ou si refresh=true)."""
    if refresh or not MONITORING_REPORT_PATH.exists():
        from src.models.monitoring import NpEncoder, check_monitoring

        return json.loads(json.dumps(check_monitoring(model=state["model"]), cls=NpEncoder))
    return json.loads(MONITORING_REPORT_PATH.read_text())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
