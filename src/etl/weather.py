"""
weather.py
==========
Collecte des prévisions météo Open-Meteo utilisées comme features du modèle.

Deux sources, sur la même grille que les données de qualité d'air :
  - Historical Forecast API → `<variable>` : prévision à courte échéance (≈ observé),
    y compris les jours à venir (= dernière prévision disponible).
  - Previous Runs API       → `<variable>_prev1` : prévision émise la VEILLE pour
    chaque heure. Pour l'entraînement, c'est ce que l'on savait réellement de J+1 au jour J.

Convention horaire identique à quality_air.py : heure locale (Cotonou), étiquetée UTC.

Usage : python -m src.etl.weather
"""

import logging
import pathlib
from datetime import date, timedelta

import pandas as pd
import requests
from retry_requests import retry

from src.etl.quality_air import BACKFILL_FROM, LATITUDE, LONGITUDE

logger = logging.getLogger(__name__)

WEATHER_PATH = pathlib.Path("data/weather.parquet")
HIST_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
PREV_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
]
PREV_SUFFIX = "_prev1"
FORECAST_DAYS_AHEAD = 2

_session = retry(requests.Session(), retries=5, backoff_factor=0.5)


def _fetch(url: str, variables: list[str], start_date: str, end_date: str) -> pd.DataFrame:
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(variables),
        "timezone": "auto",
    }
    r = _session.get(url, params=params, timeout=90)
    r.raise_for_status()
    hourly = r.json()["hourly"]
    df = pd.DataFrame(hourly)
    df["date"] = pd.to_datetime(df.pop("time")).dt.tz_localize("UTC")
    return df.set_index("date")


def fetch_weather(start_date: str, end_date: str) -> pd.DataFrame:
    """Météo horaire : variables courantes + prévisions de la veille (`*_prev1`)."""
    current = _fetch(HIST_URL, HOURLY_VARIABLES, start_date, end_date)
    prev = _fetch(PREV_URL, [f"{v}_previous_day1" for v in HOURLY_VARIABLES], start_date, end_date)
    prev.columns = [c.replace("_previous_day1", PREV_SUFFIX) for c in prev.columns]
    return current.join(prev, how="outer")


def collect_weather() -> bool:
    """Re-télécharge toute la période (2 requêtes) et écrit data/weather.parquet."""
    start = (date.fromisoformat(BACKFILL_FROM) - timedelta(days=7)).isoformat()
    end = (date.today() + timedelta(days=FORECAST_DAYS_AHEAD)).isoformat()
    try:
        df = fetch_weather(start, end)
    except Exception as e:
        logger.error("Collecte météo échouée : %s", e)
        return False
    if df.empty:
        logger.error("Collecte météo : réponse vide")
        return False

    WEATHER_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.reset_index().to_parquet(WEATHER_PATH, index=False)
    logger.info("✓ Météo : %d heures (%s → %s) → %s", len(df), df.index.min().date(),
                df.index.max().date(), WEATHER_PATH)
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(0 if collect_weather() else 1)
