"""
utils.py
========
Accès aux données (Parquet / SQLite) et synchronisation avec le dataset HuggingFace.
"""

import json
import logging
import os
import pathlib
import sqlite3
from datetime import datetime, timedelta, timezone

import dotenv
import pandas as pd

from src.etl.quality_air import DB_PATH, PARQUET_PATH, collect_and_refresh

dotenv.load_dotenv()

REPO_ID = os.getenv("HF_REPO_ID", "donerick/air-quality-storage")
COLLECT_INTERVAL = timedelta(days=2)              # délai minimum entre deux collectes
STAMP_FILE = pathlib.Path("data/.last_collect")   # timestamp local de la dernière collecte
STAMP_REPO_PATH = ".last_collect"                 # chemin du timestamp dans le dataset HF
DATA_FILES = [DB_PATH, PARQUET_PATH]

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _token() -> str | None:
    return os.getenv("HF_TOKEN")


# ===================== LECTURE DES DONNÉES =====================

def get_df_fast() -> pd.DataFrame:
    """Charge les données horaires (Parquet en priorité, sinon SQLite).

    Renvoie un DataFrame indexé par `date` (UTC), ou un DataFrame vide.
    """
    if PARQUET_PATH.exists():
        df = pd.read_parquet(PARQUET_PATH)
        source = "Parquet"
    elif DB_PATH.exists():
        with sqlite3.connect(str(DB_PATH)) as conn:
            df = pd.read_sql_query("SELECT * FROM hourly_air_quality ORDER BY date ASC", conn)
        source = "SQLite"
    else:
        logger.error("Aucun fichier de données trouvé (ni Parquet ni SQLite).")
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.set_index("date").sort_index()
    logger.info("Données chargées depuis %s (%d lignes)", source, len(df))
    return df


# ===================== TIMESTAMP DE COLLECTE =====================

def _read_last_collect() -> datetime | None:
    try:
        if STAMP_FILE.exists():
            return datetime.fromisoformat(json.loads(STAMP_FILE.read_text())["last_collect"])
    except Exception as e:
        logger.warning("Impossible de lire %s : %s", STAMP_FILE, e)
    return None


def _write_last_collect(dt: datetime | None = None) -> None:
    ts = (dt or datetime.now(timezone.utc)).isoformat()
    STAMP_FILE.parent.mkdir(parents=True, exist_ok=True)
    STAMP_FILE.write_text(json.dumps({"last_collect": ts}))
    logger.info("Timestamp collecte mis à jour : %s", ts)


def _needs_collect() -> bool:
    """True si la dernière collecte date de plus de COLLECT_INTERVAL."""
    last = _read_last_collect()
    if last is None:
        logger.info("Aucune collecte précédente trouvée → collecte nécessaire")
        return True
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)

    elapsed = datetime.now(timezone.utc) - last
    if elapsed >= COLLECT_INTERVAL:
        logger.info("Dernière collecte il y a %s → collecte nécessaire", elapsed)
        return True
    logger.info("Collecte récente (%s). Prochaine dans %s", elapsed, COLLECT_INTERVAL - elapsed)
    return False


# ===================== SYNCHRONISATION HUGGINGFACE =====================

def download_data_from_hf() -> bool:
    """Récupère DB, Parquet et timestamp depuis le dataset HF (écrase les fichiers locaux)."""
    if not _token():
        logger.info("HF_TOKEN absent : pas de synchronisation descendante.")
        return False
    from huggingface_hub import hf_hub_download

    ok = True
    for path in DATA_FILES:
        try:
            hf_hub_download(repo_id=REPO_ID, filename=str(path), repo_type="dataset",
                            local_dir=".", token=_token())
            logger.info("%s téléchargé depuis HF", path)
        except Exception as e:
            ok = False
            logger.warning("%s introuvable sur HF : %s", path, e)
    try:
        stamp = hf_hub_download(repo_id=REPO_ID, filename=STAMP_REPO_PATH, repo_type="dataset",
                                token=_token())
        STAMP_FILE.parent.mkdir(parents=True, exist_ok=True)
        STAMP_FILE.write_text(pathlib.Path(stamp).read_text())
    except Exception:
        logger.info("Aucun timestamp de collecte sur HF (première fois)")
    return ok


def upload_data_to_hf() -> bool:
    """Publie DB + Parquet + timestamp sur le dataset HF."""
    if not _token():
        return False
    from huggingface_hub import upload_file

    try:
        msg = f"ETL update — {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC"
        for path in DATA_FILES:
            upload_file(path_or_fileobj=str(path), path_in_repo=str(path), repo_id=REPO_ID,
                        repo_type="dataset", token=_token(), commit_message=msg)
        if STAMP_FILE.exists():
            upload_file(path_or_fileobj=str(STAMP_FILE), path_in_repo=STAMP_REPO_PATH, repo_id=REPO_ID,
                        repo_type="dataset", token=_token(), commit_message=msg)
        logger.info("Données + timestamp publiés sur HuggingFace")
        return True
    except Exception as e:
        logger.error("Erreur upload HF : %s", e)
        return False


def etl_task_if_needed() -> bool:
    """Collecte Open-Meteo si la dernière date de plus de COLLECT_INTERVAL, puis synchronise HF.

    Renvoie True si une collecte a réussi.
    """
    logger.info("=== Vérification ETL planifiée ===")
    if not _needs_collect():
        return False

    logger.info("Lancement de la collecte Open-Meteo…")
    try:
        if not collect_and_refresh():
            logger.error("Collecte échouée : timestamp non mis à jour, nouvel essai au prochain passage.")
            return False
        _write_last_collect()
        upload_data_to_hf()
        logger.info("ETL terminé avec succès.")
        return True
    except Exception as e:
        logger.error("Erreur ETL : %s", e, exc_info=True)
        return False
