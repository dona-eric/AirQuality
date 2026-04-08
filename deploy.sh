#!/bin/bash

# --- CONFIGURATION ---
APP_DIR=$(pwd)
LOG_DIR="$APP_DIR/logs"
mkdir -p "$LOG_DIR"
mkdir -p "$APP_DIR/models"
mkdir -p "$APP_DIR/data/raw"

echo "🚀 Démarrage du déploiement du système Air Quality Cotonou..."

# 1. Installation des dépendances si nécessaire
# pip install -r requirements.txt

# 2. Lancement de l'API FastAPI en arrière-plan
echo "Starting FastAPI server..."
nohup uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/api.log" 2>&1 &
API_PID=$!
echo "✅ API lancée avec le PID: $API_PID"

# 3. Lancement du Frontend Streamlit en arrière-plan
echo "Starting Streamlit UI..."
nohup streamlit run frontend/app_ui.py --server.port 8501 > "$LOG_DIR/frontend.log" 2>&1 &
STR_PID=$!
echo "✅ Frontend lancé avec le PID: $STR_PID"

# 4. Configuration de la collecte et entraînement (Toutes les 48h)
# On utilise Crontab pour automatiser le script de collecte/entraînement
# On crée un script intermédiaire 'job.sh'

#!/bin/bash
cd $APP_DIR
echo "\$(date): Lancement de la collecte et du ré-entraînement..." >> $LOG_DIR/pipeline.log

python src/etl/quality_air.py >> $LOG_DIR/pipeline.log 2>&1
python src/models/inference.py >> $LOG_DIR/pipeline.log 2>&1
echo "\$(date): Pipeline terminé." >> $LOG_DIR/pipeline.log


chmod +x job.sh

# Ajout à la crontab (s'il n'existe pas déjà)
# '0 0 */2 * *' signifie à minuit tous les 2 jours
(crontab -l 2>/dev/null | grep -v "job.sh"; echo "0 0 */2 * * $APP_DIR/job.sh") | crontab -

echo "---"
echo "✅ Système opérationnel !"
echo "L'API est sur le port 8000, le Frontend sur le port 8501."
echo "La collecte et l'entraînement sont planifiés tous les 2 jours."
echo "Consultez les logs dans le dossier /logs pour le suivi."