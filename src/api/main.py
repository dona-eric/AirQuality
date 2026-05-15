from fastapi import FastAPI, HTTPException
import pandas as pd
import joblib
import os
import uvicorn
import pathlib
from typing import List, Dict
from src.api.utils import get_df_fast
from src.api.schemas import PredictionResponse, HistoryResponse

app = FastAPI(title="Cotonou Air Quality API", description="Prévision des PM2.5 à 24h")

# Chemins structurés
BASE_DIR = pathlib.Path(__file__).parent
MODEL_PATH = pathlib.Path("models/air_quality.pkl")

# Chargement du modèle au démarrage
if MODEL_PATH.exists():
    model = joblib.load(MODEL_PATH)
else:
    model = None

def get_aqi_info(value):
    if value <= 12: return "Bon", "L'air est pur. Idéal pour les activités extérieures."
    elif value <= 35: return "Modéré", "Qualité acceptable. Les personnes très sensibles devraient limiter les efforts prolongés."
    elif value <= 55: return "Mauvais", "Port du masque recommandé près des grands axes (Étoile Rouge, Dantokpa)."
    else: return "Très Mauvais", "Alerte pollution. Limitez les sorties non essentielles."

@app.get("/")
def home():
    return {
        "status": "online",
        "model_loaded": model is not None,
        "message": "API de prévision de la qualité de l'air à Cotonou"
    }

@app.get("/history", response_model=HistoryResponse)
def get_history():
    """Renvoie les 7 derniers jours de mesures réelles."""
    try:
        df = get_df_fast()
        df_daily = df.resample('D').mean(numeric_only=True).tail(7)
        
        return {
            "dates": [d.strftime('%Y-%m-%d') for d in df_daily.index],
            "values": [round(v, 2) for v in df_daily['pm2_5']]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict", response_model=PredictionResponse)
def predict():
    if model is None:
        raise HTTPException(status_code=500, detail="Modèle non trouvé. Vérifiez le dossier 'models/'.")

    try:
        df = get_df_fast()
        
        df_daily = df.resample('D').mean(numeric_only=True).interpolate()
        recent = df_daily.tail(10).copy()
        
        # Feature Engineering (Identique à l'entraînement)
        for i in range(1, 4):
            recent[f'pm25_lag_{i}'] = recent['pm2_5'].shift(i)
            recent[f'co_lag_{i}'] = recent['carbon_monoxide'].shift(i)
        recent['pm25_rolling_7d'] = recent['pm2_5'].rolling(window=7).mean()
        recent['day_of_week'] = recent.index.dayofweek
        recent['month'] = recent.index.month
        
        # Sélection de la ligne la plus récente pour la prédiction
        X_input = recent.tail(1).drop(columns=['formaldehyde', 'id'], errors='ignore')
        
        # Vérification des features attendues par le modèle
        if hasattr(model, 'feature_names_in_'):
            X_input = X_input[model.feature_names_in_]

        # Vérification qu'il n'y a pas de NaN (important pour XGBoost)
        if X_input.isnull().values.any():
            raise ValueError("Données historiques insuffisantes pour générer les lags.")

        current_pm25 = recent['pm2_5'].iloc[-1]
        delta_pred = float(model.predict(X_input)[0])
        final_pred = current_pm25 + delta_pred
        
        label, conseil = get_aqi_info(final_pred)
        
        return {
            "date_prevision": (recent.index[-1] + pd.Timedelta(days=1)).strftime('%Y-%m-%d'),
            "current_pm25": round(current_pm25, 2),
            "predicted_pm25": round(final_pred, 2),
            "delta": round(delta_pred, 2),
            "aqi_label": label,
            "conseil": conseil
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)