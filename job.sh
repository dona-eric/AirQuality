#!/bin/bash
# Tâche planifiée (cron) : collecte Open-Meteo puis ré-entraînement si le monitoring le demande.
set -u
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$APP_DIR/logs/pipeline.log"
PYTHON="${PYTHON:-$APP_DIR/.venv/bin/python}"
[ -x "$PYTHON" ] || PYTHON=python3

cd "$APP_DIR" || exit 1
mkdir -p "$APP_DIR/logs"

echo "$(date): Lancement de la collecte et du ré-entraînement..." >> "$LOG_FILE"
"$PYTHON" -c "from src.etl.quality_air import collect_and_refresh; import sys; sys.exit(0 if collect_and_refresh() else 1)" >> "$LOG_FILE" 2>&1 \
  && "$PYTHON" -m src.models.retrain_trigger >> "$LOG_FILE" 2>&1
echo "$(date): Pipeline terminé (code $?)." >> "$LOG_FILE"
