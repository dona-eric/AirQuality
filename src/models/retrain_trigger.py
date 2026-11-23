"""
retrain_trigger.py
==================
Vérifie le monitoring et relance l'entraînement si nécessaire.

Usage : python -m src.models.retrain_trigger
"""

import logging
import os
import subprocess
import sys

from src.models.monitoring import check_monitoring

logger = logging.getLogger(__name__)


def trigger_retraining_if_needed() -> tuple[bool, str]:
    logger.info("Vérification du besoin de ré-entraînement...")
    report = check_monitoring()

    for w in report.get("warnings", []):
        logger.warning(w)

    if not report.get("needs_retraining"):
        logger.info("Pas de ré-entraînement nécessaire pour le moment.")
        return False, "Non nécessaire"

    logger.info("Ré-entraînement déclenché ! Raisons : %s", report.get("reasons"))
    try:
        env = {**os.environ, "PYTHONPATH": "."}
        result = subprocess.run(
            [sys.executable, "-m", "src.models.train"],
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.info("Ré-entraînement terminé avec succès.")
            return True, "Succès"
        logger.error("Échec de l'entraînement : %s", result.stderr)
        return False, result.stderr
    except Exception as e:
        logger.error("Erreur lors du déclenchement de l'entraînement : %s", e)
        return False, str(e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    trigger_retraining_if_needed()
