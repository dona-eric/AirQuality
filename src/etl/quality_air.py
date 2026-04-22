"""
quality_air.py
===========================
Collecteur quotidien pour l'API Open‑Meteo Air Quality.
- Stocke les relevés horaires dans SQLite
- Exporte un CSV pour le dashboard Plotly
- Tâche planifiée chaque jour à 00:05 UTC
"""

import atexit
import logging
import pathlib
import sqlite3
import time
from datetime import datetime, timedelta, timezone
import requests
import openmeteo_requests
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests_cache
from apscheduler.schedulers.background import BackgroundScheduler
from retry_requests import retry


# CONFIG

LATITUDE, LONGITUDE = 6.4969, 2.6289  # Cotonou, Bénin
INTERVAL_H=48        # Fréquence de mise à jour (heures)
BACKFILL_FROM = "2025-09-01"    # Date de début historique
DB_PATH = pathlib.Path("data/air_quality.db")
CSV_PATH = pathlib.Path("data/raw/hourly_quality_air_data.csv")
PARQUET_PATH = pathlib.Path('data/air_quality.parquet')
LOG_PATH = pathlib.Path("logs/collect.log")
API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

pathlib.Path("logs").mkdir(exist_ok=True)
pathlib.Path("data/raw").mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Client Open‑Meteo avec cache + retry
cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


# DATABASE

def init_db() -> None:
    """Crée la table si elle n'existe pas (clé unique sur la date)."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS hourly_air_quality (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TIMESTAMP UNIQUE NOT NULL,
            pm2_5 REAL,
            pm10 REAL,
            carbon_monoxide REAL,
            carbon_dioxide REAL,
            sulphur_dioxide REAL,
            ozone REAL,
            nitrogen_dioxide REAL,
            formaldehyde REAL,
            methane REAL,
            european_aqi REAL,
            european_aqi_pm2_5 REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()
    logger.info("✓ Base de données prête")


# =====================API & INGESTION==================

HOURLY_FIELDS = [
    "pm10",
    "pm2_5",
    "carbon_monoxide",
    "carbon_dioxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
    "formaldehyde",
    "methane",
    "european_aqi",
    "european_aqi_pm2_5",
]


def fetch_air_quality(start_date, end_date):
    """Récupère les données horaires via le client openmeteo_requests."""
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": HOURLY_FIELDS,
        "current": HOURLY_FIELDS[:6],  # pour suivi temps réel (non stocké ici)
        "timezone": "auto",
        "domains": "cams_global",
        "timeformat": "unixtime",
    }

    try:
        responses = openmeteo.weather_api(API_URL, params=params)
    
    except requests.RequestException as exc:
        logger.error("Erreur réseau Open-Meteo : %s", exc)
        return None
    if not responses:
        logger.error("Réponse API vide")
        return None

    response = responses[0]

        # Données horaires dans l'ordre des variables demandées
    hourly = response.Hourly()
    values = [hourly.Variables(i).ValuesAsNumpy() for i in range(len(HOURLY_FIELDS))]

    time_index = pd.date_range(
            start=pd.to_datetime(hourly.Time() + response.UtcOffsetSeconds(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd() + response.UtcOffsetSeconds(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )

    data = {"date": time_index}
    for i, field in enumerate(HOURLY_FIELDS):
        data[field] = hourly.Variables(i).ValuesAsNumpy()
 
    df = pd.DataFrame(data)
 
    if df.empty:
        logger.warning("API a retourné un DataFrame vide pour %s → %s", start_date, end_date)
        return None
 
    logger.info("Données reçues : %d lignes (%s → %s)", len(df),
                df["date"].min().date(), df["date"].max().date())
    return df 


def store_dataframe(df: pd.DataFrame) -> int:
    """Insère les lignes dans SQLite en ignorant les doublons."""
    if df is None or df.empty:
        return 0

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    rows = [
        (
            row.date.isoformat(),
            row.pm2_5,
            row.pm10,
            row.carbon_monoxide,
            row.carbon_dioxide,
            row.sulphur_dioxide,
            row.ozone,
            row.nitrogen_dioxide,
            row.formaldehyde,
            row.methane,
            row.european_aqi,
            row.european_aqi_pm2_5,
        )
        for row in df.itertuples(index=False)
    ]

    cursor.executemany(
        """
        INSERT OR IGNORE INTO hourly_air_quality (
            date, pm2_5, pm10, carbon_monoxide, carbon_dioxide,
            sulphur_dioxide, ozone, nitrogen_dioxide,
            formaldehyde, methane, european_aqi, european_aqi_pm2_5
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )

    inserted = cursor.rowcount
    conn.commit()
    conn.close()
    logger.info(f"✓ Insertion BD : {inserted} lignes (doublons ignorés)")
    return inserted


def export_format() -> None:
    """Exporte toute la table SQLite vers CSV.
    Le dashboard Plotly/Dash lit ce CSV.
    Appelé automatiquement après chaque collecte.
    """
    conn = sqlite3.connect(str(DB_PATH))
    try:
        df = pd.read_sql_query(
            "SELECT date, pm2_5, pm10, carbon_monoxide, carbon_dioxide, sulphur_dioxide,"
            " ozone, nitrogen_dioxide, formaldehyde, methane, european_aqi, european_aqi_pm2_5"
            " FROM hourly_air_quality ORDER BY date ASC",
            conn,
            parse_dates=["date"],
        )

        # 1- Export CSV
        df.to_csv(CSV_PATH, index=False)
        logger.info(f"✓ Export CSV : {CSV_PATH}")

        # 2- Export Parquet
        df.to_parquet(PARQUET_PATH, index=False, engine='pyarrow', compression='snappy')
        logger.info(f"✓ Export Parquet : {PARQUET_PATH}")

        return CSV_PATH
    except Exception as e:
        logger.error(f"Erreur export CSV : {e}", exc_info=True)
    finally:
        conn.close()


# SCHEDULER

def _next_start_date() -> datetime.date:
    """Renvoie la date de début pour la prochaine collecte.
    - Si la table est vide : 2025-11-30
    - Sinon : jour suivant la dernière date enregistrée
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(date) FROM hourly_air_quality")
    last = cursor.fetchone()[0]
    conn.close()
 
    if last is None:
        logger.info("Base vide → backfill depuis %s", BACKFILL_FROM)
        return BACKFILL_FROM

    last_date = datetime.fromisoformat(last).date()
    next_date = (last_date + timedelta(days=1)).isoformat()
    logger.info("Dernière date en base : %s → collecte depuis %s", last_date, next_date)
    return next_date



def collect_and_refresh() -> None:
    """
    Fonction principale appelée :
      - une fois au démarrage (backfill)
      - puis toutes les 48h par le scheduler
 
    Étapes :
      1. Calcule la date de début (incrémental)
      2. Appelle l'API
      3. Stocke dans SQLite
      4. Exporte le CSV frais pour le dashboard
    """
    start_date = _next_start_date()
    end_date   = datetime.now(timezone.utc).date().isoformat()
 
    if start_date > end_date:
        logger.info("Données déjà à jour (start=%s > end=%s) — rien à faire", start_date, end_date)
        if not PARQUET_PATH.exists() or not CSV_PATH.exists():
            export_format()  # assure l'export si jamais absent
        return
 
    logger.info("=== Collecte %s → %s ===", start_date, end_date)
 
    df = fetch_air_quality(start_date, end_date)
 
    if df is not None:
        store_dataframe(df)
        export_format()
        logger.info("=== Collecte terminée ===")
    else:
        logger.error("Collecte échouée — aucune donnée reçue de l'API")
 



def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        func=collect_and_refresh,     # fonction à appeler
        trigger="interval",           # type de déclencheur : intervalle fixe
        hours=INTERVAL_H,             # toutes les 48 heures
        id="air_quality_refresh",     # identifiant unique (utile pour déboguer)
        max_instances=1,              # empêche deux collectes simultanées
        coalesce=True,                # si le programme était éteint, ne rattrape qu'une seule fois
        next_run_time=datetime.now(timezone.utc) + timedelta(hours=INTERVAL_H),
        
    )
    
    scheduler.start()
    # Arrêt propre si CTRL+C ou fin du programme
    atexit.register(lambda: scheduler.shutdown(wait=False))
 
    next_run = scheduler.get_job("air_quality_refresh").next_run_time
    logger.info("Scheduler démarré — prochaine collecte : %s", next_run)
    return scheduler
 


# ENTRYPOINT

if __name__ == "__main__":


    logger.info("╔══════════════════════════════════════╗")
    logger.info("║  Collecteur Qualité d'Air — Cotonou  ║")
    logger.info("╚══════════════════════════════════════╝")

    # Étape 1 : prépare la base de données

    init_db()

    # Étape 2 : collecte immédiate (backfill depuis 30 nov 2025 ou suite)
    collect_and_refresh()

    # Lancer la collecte quotidienne en arrière-plan
    scheduler = start_scheduler()

    print("\n Collecte qualité d'air active. CTRL+C pour arrêter.\n")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Arrêt demandé: shutdown propre")
        scheduler.shutdown(wait=False)