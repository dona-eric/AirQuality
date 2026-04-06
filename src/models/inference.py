import pandas as pd
import numpy as np
import joblib # Pour sauvegarder/charger le modèle
from xgboost import XGBRegressor

def logger_info(message):
    print(f"[INFO] {message}")

class AirQualityPredictor:
    def __init__(self, model_path=None):
        self.model = None
        if model_path:
            self.model = joblib.load(model_path)
            logger_info("Modèle chargé avec succès.")

    def preprocess_new_data(self, csv_path):
        """Prépare les données les plus récentes pour la prédiction."""
        # Chargement
        df = pd.read_csv(csv_path, parse_dates=['date'])
        df['date'] = pd.to_datetime(df['date'], utc=True)
        df.set_index('date', inplace=True)
        
        # Resampling journalier
        df_daily = df.resample('D').mean().interpolate(method='linear')
        
        # On ne garde que ce qui est nécessaire pour les features (les 10 derniers jours suffisent)
        recent_data = df_daily.tail(10).copy()
        
        # Création des Features (doivent être identiques à l'entraînement)
        for i in range(1, 4):
            recent_data[f'pm25_lag_{i}'] = recent_data['pm2_5'].shift(i)
            recent_data[f'co_lag_{i}'] = recent_data['carbon_monoxide'].shift(i)
        
        recent_data['pm25_rolling_7d'] = recent_data['pm2_5'].rolling(window=7).mean()
        recent_data['day_of_week'] = recent_data.index.dayofweek
        recent_data['month'] = recent_data.index.month
        
        # On prend la toute dernière ligne (celle d'aujourd'hui) pour prédire demain
        current_state = recent_data.tail(1).drop(columns=['formaldehyde'], errors='ignore')
        
        # Récupération de la valeur brute actuelle pour le calcul final
        current_pm25 = recent_data['pm2_5'].iloc[-1]
        
        return current_state, current_pm25

    def get_aqi_label(self, value):
        """Transforme la concentration en conseil de santé."""
        if value <= 12: return "🟢 Bon (Air pur)"
        elif value <= 35: return "🟡 Modéré (Attention aux personnes sensibles)"
        elif value <= 55: return "🟠 Mauvais (Port du masque recommandé)"
        else: return "🔴 Très Mauvais (Alerte pollution - Restez à l'abri)"

    def run_prediction(self, csv_path):
        # 1. Préparation
        X_input, current_val = self.preprocess_new_data(csv_path)
        
        # 2. Prédiction du Delta (Différence)
        # On s'assure que les colonnes sont dans le bon ordre
        delta_pred = self.model.predict(X_input)[0]
        
        # 3. Calcul de la valeur finale
        final_pred = current_val + delta_pred
        
        # 4. Affichage
        print("\n" + "="*40)
        print(f"📊 RÉSULTATS POUR DEMAIN À COTONOU")
        print(f"Valeur actuelle : {current_val:.2f} µg/m³")
        print(f"Variation prévue : {'+' if delta_pred > 0 else ''}{delta_pred:.2f} µg/m³")
        print(f"PRÉVISION PM2.5 : {final_pred:.2f} µg/m³")
        print(f"INDICE : {self.get_aqi_label(final_pred)}")
        print("="*40 + "\n")

# --- UTILISATION ---
if __name__ == "__main__":
    
    predictor = AirQualityPredictor(model_path='air_quality.pkl')
    predictor.run_prediction('hourly_quality_air_data.csv')