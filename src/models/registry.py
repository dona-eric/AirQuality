"""
registry.py
===========
Chargement / sauvegarde du modèle XGBoost (local + HuggingFace).

Format unique : XGBRegressor sérialisé en JSON (`models/xgb_model.json`).

Résolution du modèle (variable d'environnement MODEL_VERSION) :
  - "latest" (défaut) : fichier local s'il existe, sinon HF `models/xgboost_model.json`
  - "<tag>"           : HF `models/<tag>/xgboost_model.json`
"""

import logging
import os
import pathlib

import xgboost as xgb

from src.models.features import FEATURE_COLUMNS

logger = logging.getLogger(__name__)

LOCAL_MODEL_PATH = pathlib.Path("models/xgb_model.json")
HF_REPO_ID = os.getenv("HF_REPO_ID", "donerick/air-quality-storage")
HF_LATEST_FILENAME = "models/xgboost_model.json"


def hf_model_filename(version: str) -> str:
    if version in (None, "", "latest"):
        return HF_LATEST_FILENAME
    return f"models/{version}/xgboost_model.json"


def _read_model(path: pathlib.Path | str) -> xgb.XGBRegressor:
    model = xgb.XGBRegressor()
    model.load_model(str(path))
    features = list(model.get_booster().feature_names or [])
    if features != FEATURE_COLUMNS:
        raise ValueError(
            "Le modèle n'a pas été entraîné avec les features actuelles. "
            f"Attendu {FEATURE_COLUMNS}, trouvé {features}. Ré-entraînez-le."
        )
    return model


def save_model(model: xgb.XGBRegressor, path: pathlib.Path = LOCAL_MODEL_PATH) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(path))
    logger.info("Modèle sauvegardé : %s", path)
    return path


def load_model(version: str | None = None, local_path: pathlib.Path = LOCAL_MODEL_PATH):
    """Renvoie (modèle, source) ou (None, None) si aucun modèle utilisable."""
    version = version or os.getenv("MODEL_VERSION", "latest")

    if version == "latest" and local_path.exists():
        try:
            return _read_model(local_path), f"local:{local_path}"
        except Exception as e:
            logger.error("Modèle local inutilisable (%s) : %s", local_path, e)

    filename = hf_model_filename(version)
    try:
        from huggingface_hub import hf_hub_download

        path = hf_hub_download(
            repo_id=HF_REPO_ID,
            filename=filename,
            repo_type="dataset",
            token=os.getenv("HF_TOKEN"),
        )
        return _read_model(path), f"hf:{HF_REPO_ID}/{filename}"
    except Exception as e:
        logger.error("Chargement HF impossible (%s) : %s", filename, e)

    return None, None


def push_model_to_hf(path: pathlib.Path, version_tag: str) -> bool:
    """Publie le modèle sur HF comme `latest` et sous `models/<version_tag>/`."""
    token = os.getenv("HF_TOKEN")
    if not token:
        logger.info("HF_TOKEN absent : publication HF ignorée.")
        return False

    from huggingface_hub import upload_file

    ok = True
    for target in (HF_LATEST_FILENAME, hf_model_filename(version_tag)):
        try:
            upload_file(
                path_or_fileobj=str(path),
                path_in_repo=target,
                repo_id=HF_REPO_ID,
                repo_type="dataset",
                token=token,
                commit_message=f"Model update ({version_tag})",
            )
            logger.info("Modèle publié sur HF : %s", target)
        except Exception as e:
            ok = False
            logger.error("Échec publication HF %s : %s", target, e)
    return ok
