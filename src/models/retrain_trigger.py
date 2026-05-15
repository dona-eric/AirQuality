import subprocess
import logging
import os
from src.models.monitoring import check_monitoring

logger = logging.getLogger(__name__)

def trigger_retraining_if_needed():
    """
    Vérifie le monitoring et lance l'entraînement si nécessaire.
    """
    logger.info("Vérification du besoin de ré-entraînement...")
    report = check_monitoring()

    if report.get("needs_retraining"):
        logger.info(f"Ré-entraînement déclenché ! Raisons : {report.get('reasons')}")
        try:
            # On lance l'entraînement en tant que sous-processus
            # On utilise PYTHONPATH=. pour s'assurer que les imports fonctionnent
            env = os.environ.copy()
            env["PYTHONPATH"] = "."
            result = subprocess.run(["python", "src/models/train.py"],
                                    env=env,
                                    capture_output=True,
                                    text=True)

            if result.returncode == 0:
                logger.info("Ré-entraînement terminé avec succès.")
                return True, "Succès"
            else:
                logger.error(f"Échec de l'entraînement : {result.stderr}")
                return False, result.stderr
        except Exception as e:
            logger.error(f"Erreur lors du déclenchement de l'entraînement : {e}")
            return False, str(e)
    else:
        logger.info("Pas de ré-entraînement nécessaire pour le moment.")
        return False, "Non nécessaire"

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    trigger_retraining_if_needed()
