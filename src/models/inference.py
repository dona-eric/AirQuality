"""
inference.py
============
Prévision du PM2.5 moyen de J+1 — utilisée par l'API et en ligne de commande.

Usage CLI : python -m src.models.inference
"""

import logging

import pandas as pd

from src.models.features import build_inference_row


def get_aqi_info(value: float) -> tuple[str, str]:
    """Transforme une concentration PM2.5 (µg/m³) en niveau + conseil santé."""
    if value <= 12:
        return "Bon", "L'air est pur. Idéal pour les activités extérieures."
    elif value <= 35:
        return "Modéré", "Qualité acceptable. Les personnes très sensibles devraient limiter les efforts prolongés."
    elif value <= 55:
        return "Mauvais", "Port du masque recommandé près des grands axes (Étoile Rouge, Dantokpa)."
    else:
        return "Très Mauvais", "Alerte pollution. Limitez les sorties non essentielles."


def predict_next_day(model, df_hourly: pd.DataFrame) -> dict:
    """Prévoit le PM2.5 moyen du lendemain du dernier jour présent dans les données."""
    X, current_pm25, last_day = build_inference_row(df_hourly)

    delta = float(model.predict(X)[0])
    predicted = max(current_pm25 + delta, 0.0)  # une concentration ne peut pas être négative
    label, conseil = get_aqi_info(predicted)

    return {
        "date_prevision": (last_day + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
        "current_pm25": round(current_pm25, 2),
        "predicted_pm25": round(predicted, 2),
        "delta": round(predicted - current_pm25, 2),
        "aqi_label": label,
        "conseil": conseil,
        "data_last_update": df_hourly.index.max().isoformat(),
    }


if __name__ == "__main__":
    from src.api.utils import get_df_fast
    from src.models.registry import load_model

    logging.basicConfig(level=logging.INFO)
    model, source = load_model()
    if model is None:
        raise SystemExit("Aucun modèle disponible. Lancez d'abord : python -m src.models.train")

    res = predict_next_day(model, get_df_fast())
    print("\n" + "=" * 40)
    print(f"RÉSULTATS POUR LE {res['date_prevision']} À COTONOU  (modèle {source})")
    print(f"Valeur actuelle  : {res['current_pm25']:.2f} µg/m³")
    print(f"Variation prévue : {res['delta']:+.2f} µg/m³")
    print(f"PRÉVISION PM2.5  : {res['predicted_pm25']:.2f} µg/m³")
    print(f"INDICE           : {res['aqi_label']} — {res['conseil']}")
    print(f"Données jusqu'au : {res['data_last_update']}")
    print("=" * 40 + "\n")
