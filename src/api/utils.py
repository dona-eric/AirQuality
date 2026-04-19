import dotenv
from huggingface_hub import hf_hub_download, upload_file
from src.etl.quality_air import collect_and_refresh, DB_PATH, PARQUET_PATH
import os
import logging
import xgboost as xgb
from datetime import datetime, timedelta, timezone
import json
import sqlite3
import pandas as pd
import pathlib



dotenv.load_dotenv()
REPO_ID = "donerick/air-quality-storage"
TOKEN = os.getenv("HF_TOKEN")
COLLECT_INTERVAL = timedelta(days=2)           # délai minimum entre deux collectes
STAMP_FILE = pathlib.Path(".last_collect") # fichier timestamp local

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def get_df_fast():
    """Lit les données parquet d'abord et verifier s'il existe
     dans le contraire les fichiers csv sont chargés depuis sqlite
     et retourne un DataFrame propre.
     """
    try:
        # Essayer de lire le fichier parquet en premier
        if PARQUET_PATH.exists():
            df = pd.read_parquet(PARQUET_PATH)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
            logger.info("Données chargées depuis le fichier Parquet")
            return df
        elif DB_PATH.exists():

            # Si le fichier parquet n'existe pas, lire depuis SQLite
            conn = sqlite3.connect(str(DB_PATH))
            # On récupère toutes les colonnes nécessaires
            query = "SELECT * FROM hourly_air_quality ORDER BY date ASC"
            df = pd.read_sql_query(query, conn, parse_dates=['date'])
            conn.close()
        
            
            df['date'] = pd.to_datetime(df['date'], utc=True)
            df.set_index('date', inplace=True)
            logger.info("Données chargées depuis SQLite")
            return df
        
        else:
            logger.error("Aucun fichier de données trouvé (ni Parquet ni SQLite).")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Erreur lecture SQLite : {e}")
        raise e

#===================== CONFIGURATION et CHARGEMENT DU MODÈLE ============================

def load_model_from_hf():
    try:
        model_path = hf_hub_download(
            repo_id=REPO_ID,
            filename="models/xgboost_model.json",
            repo_type="dataset",
            token=TOKEN
        )
        booster = xgb.Booster()
        booster.load_model(model_path)
        logger.info("Modèle XGBoost chargé depuis HuggingFace")
        return booster
    except Exception as e:
        logger.error(f"Erreur chargement modèle HF : {e}")
        return None
    
# ─────────────────────────────────────────────
#  GESTION DU TIMESTAMP DE COLLECTE
# ─────────────────────────────────────────────
 
def _read_last_collect() -> datetime | None:
    """Lit le timestamp de la dernière collecte réussie depuis le fichier stamp."""
    try:
        if STAMP_FILE.exists():
            data = json.loads(STAMP_FILE.read_text())
            return datetime.fromisoformat(data["last_collect"])
    except Exception as e:
        logger.warning(f"Impossible de lire {STAMP_FILE}: {e}")
    return None
 
 
def _write_last_collect(dt: datetime | None = None) -> None:
    """Écrit le timestamp de la dernière collecte réussie."""
    ts = (dt or datetime.now(timezone.utc)).isoformat()
    STAMP_FILE.write_text(json.dumps({"last_collect": ts}))
    logger.info(f"Timestamp collecte mis à jour : {ts}")
 
 
def _needs_collect() -> bool:
    """Retourne True si la dernière collecte date de plus de COLLECT_INTERVAL."""
    last = _read_last_collect()
    if last is None:
        logger.info("Aucune collecte précédente trouvée → collecte nécessaire")
        return True
 
    # Rendre last timezone-aware si ce n'est pas le cas
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
 
    elapsed = datetime.now(timezone.utc) - last
    if elapsed >= COLLECT_INTERVAL:
        logger.info(f"Dernière collecte il y a {elapsed} → collecte nécessaire")
        return True
 
    remaining = COLLECT_INTERVAL - elapsed
    logger.info(f"Collecte récente ({elapsed} écoulés). Prochaine collecte dans {remaining}")
    return False
 

 # ===================== FONCTIONS DE SYNCHRONISATION ===================================

def download_db_from_hf():
    """Télécharge la DB du Dataset au démarrage"""
    if not TOKEN:
        logger.error("HF_TOKEN manquant dans les secrets !")
        return
    
    files = [str(DB_PATH), str(PARQUET_PATH)]
    for filename in files:
        try:
            hf_hub_download(repo_id=REPO_ID, 
                            filename=filename, 
                            repo_type="dataset", 
                            local_dir=".",
                            token=TOKEN
                            )
            logger.info(f"{filename} téléchargé depuis HF")
        except Exception as e:
            logger.warning(f"{filename} introuvable sur HF : {e}")


def download_stamp_from_hf() -> bool:
    """Télécharge le fichier timestamp depuis HF pour connaître la dernière collecte."""
    if not TOKEN:
        return False
    
    files = [str(DB_PATH), str(PARQUET_PATH)]

    try:

        for filename in files:
            hf_hub_download(
                repo_id=REPO_ID, 
                filename=filename, 
                repo_type="dataset", 
                local_dir=".",
                token=TOKEN
            )
            logger.info(f"{filename} téléchargé depuis HF")
        
        if STAMP_FILE.exists():
            hf_hub_download(
                repo_id=REPO_ID,
                filename=STAMP_FILE.name,
                repo_type="dataset",
                local_dir=".",
                token=TOKEN,
            )
            logger.info("Timestamp collecte téléchargé depuis HF")
        return True
    except Exception:
        logger.info("Aucun timestamp collecte sur HF (première fois)")
        return False
    

def upload_db_to_hf() -> bool:
    """Upload DB + timestamp vers HF après une collecte réussie. Retourne True si réussi."""
    if not TOKEN:
        return False
    files = [str(DB_PATH), str(PARQUET_PATH)]

    try:
        for file_path in files:
            upload_file(
                path_or_fileobj=file_path,
                path_in_repo=file_path,
                repo_id=REPO_ID,
                repo_type="dataset",
                token=TOKEN,
                commit_message=f"ETL update — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC",
        )
        # Upload timestamp
        if STAMP_FILE.exists():
            upload_file(
                path_or_fileobj=str(STAMP_FILE),
                path_in_repo=STAMP_FILE.name,
                repo_id=REPO_ID,
                repo_type="dataset",
                token=TOKEN,
            )
        logger.info("DB + timestamp uploadés sur HuggingFace")
        return True
    except Exception as e:
        logger.error(f"Erreur upload HF : {e}")
        return False
    
def etl_task_if_needed() -> None:
    """
    Tâche planifiée toutes les 12h.
    La collecte réelle n'a lieu que si la dernière date de plus de 2 jours.
    L'API ne déclenche JAMAIS cette fonction — elle lit seulement la DB.
    """
    logger.info("=== Vérification ETL planifiée ===")
 
    if not _needs_collect():
        logger.info("Collecte ignorée — données encore fraîches.")
        return
 
    logger.info("Lancement de la collecte Open-Meteo…")
    try:
        collect_and_refresh()               # ← appel unique à l'API externe
        _write_last_collect()               # marque la collecte comme réussie
        upload_db_to_hf()                   # synchronise avec HF
        logger.info("ETL terminé avec succès.")
    except Exception as e:
        logger.error(f"Erreur ETL : {e}", exc_info=True)


def get_aqi_info(value):
    if value <= 12: return "Bon", "L'air est pur. Idéal pour les activités extérieures."
    elif value <= 35: return "Modéré", "Qualité acceptable. Les personnes très sensibles devraient limiter les efforts prolongés."
    elif value <= 55: return "Mauvais", "Port du masque recommandé près des grands axes (Étoile Rouge, Dantokpa)."
    else: return "Très Mauvais", "Alerte pollution. Limitez les sorties non essentielles."