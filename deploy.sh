#!/bin/bash
# Déploiement local (sans Docker) : API + frontend Streamlit + cron de collecte/ré-entraînement.

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$APP_DIR/logs"
API_PORT="${API_PORT:-7860}"
UI_PORT="${UI_PORT:-8501}"
mkdir -p "$LOG_DIR" "$APP_DIR/models" "$APP_DIR/data/raw"
cd "$APP_DIR" || exit 1

echo "🚀 Démarrage du déploiement du système Air Quality Cotonou..."

# 1. Installation des dépendances si nécessaire
# pip install -r requirements.txt

# 2. Modèle : entraînement si aucun modèle local
if [ ! -f models/xgb_model.json ]; then
    echo "Aucun modèle local → entraînement..."
    python -m src.models.train --no-push >> "$LOG_DIR/pipeline.log" 2>&1
fi

# 3. API FastAPI en arrière-plan
export MODEL_VERSION="${MODEL_VERSION:-latest}"
echo "Starting FastAPI server (MODEL_VERSION=$MODEL_VERSION) on port $API_PORT"
nohup uvicorn src.api.main:app --host 0.0.0.0 --port "$API_PORT" > "$LOG_DIR/api.log" 2>&1 &
echo "✅ API lancée avec le PID: $!"

# 4. Frontend Streamlit en arrière-plan, branché sur l'API locale
echo "Starting Streamlit UI on port $UI_PORT"
API_URL="http://localhost:$API_PORT" nohup streamlit run frontend/app_ui.py --server.port "$UI_PORT" > "$LOG_DIR/frontend.log" 2>&1 &
echo "✅ Frontend lancé avec le PID: $!"

# 5. Collecte + ré-entraînement conditionnel tous les 2 jours (minuit) via job.sh
chmod +x "$APP_DIR/job.sh"
(crontab -l 2>/dev/null | grep -v "job.sh"; echo "0 0 */2 * * \"$APP_DIR/job.sh\"") | crontab -

echo "---"
echo "✅ Système opérationnel !"
echo "API : http://localhost:$API_PORT/docs — Frontend : http://localhost:$UI_PORT"
echo "Collecte et ré-entraînement planifiés tous les 2 jours. Logs dans $LOG_DIR"
