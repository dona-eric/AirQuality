"""
features.py
===========
Feature engineering partagé par l'entraînement, l'inférence et le monitoring.
C'est la SEULE source de vérité : toute modification ici s'applique partout.

Cible
-----
Variation du PM2.5 moyen entre aujourd'hui (J) et demain (J+1) :

    pm25_next_delta[J] = pm2_5[J+1] - pm2_5[J]

La prévision s'obtient par : pm2_5[J] + delta prédit.

Toutes les features de la ligne J n'utilisent que des informations connues
au jour J (valeurs du jour, lags J-1..J-3, moyenne glissante J-6..J).
"""

import pandas as pd

# Polluants (moyennes journalières) utilisés comme features.
# `formaldehyde` est exclu : trop souvent manquant dans l'API CAMS.
POLLUTANT_COLUMNS = [
    "pm2_5",
    "pm10",
    "carbon_monoxide",
    "carbon_dioxide",
    "sulphur_dioxide",
    "ozone",
    "nitrogen_dioxide",
    "methane",
    "european_aqi",
    "european_aqi_pm2_5",
]

LAG_DAYS = (1, 2, 3)
ROLLING_WINDOW = 7

FEATURE_COLUMNS = (
    POLLUTANT_COLUMNS
    + [col for i in LAG_DAYS for col in (f"pm25_lag_{i}", f"co_lag_{i}")]
    + ["pm25_rolling_7d", "day_of_week", "month"]
)

TARGET_COLUMN = "pm25_next_delta"


class InsufficientDataError(ValueError):
    """Pas assez d'historique pour construire les features."""


def to_daily(df_hourly: pd.DataFrame) -> pd.DataFrame:
    """Agrège les mesures horaires (index DatetimeIndex) en moyennes journalières."""
    if df_hourly is None or df_hourly.empty:
        raise InsufficientDataError("Aucune donnée disponible.")
    if not isinstance(df_hourly.index, pd.DatetimeIndex):
        raise ValueError("Le DataFrame doit être indexé par la date (DatetimeIndex).")

    missing = [c for c in POLLUTANT_COLUMNS if c not in df_hourly.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes dans les données : {missing}")

    daily = df_hourly[POLLUTANT_COLUMNS].sort_index().resample("D").mean()
    return daily.interpolate(method="linear", limit_direction="both")


def add_features(daily: pd.DataFrame) -> pd.DataFrame:
    """Ajoute lags, moyenne glissante et variables calendaires."""
    out = daily.copy()
    for i in LAG_DAYS:
        out[f"pm25_lag_{i}"] = out["pm2_5"].shift(i)
        out[f"co_lag_{i}"] = out["carbon_monoxide"].shift(i)
    out["pm25_rolling_7d"] = out["pm2_5"].rolling(window=ROLLING_WINDOW).mean()
    out["day_of_week"] = out.index.dayofweek
    out["month"] = out.index.month
    return out


def build_supervised_frame(df_hourly: pd.DataFrame) -> pd.DataFrame:
    """Features + cible, une ligne par jour, sans valeurs manquantes.

    Le dernier jour disponible est exclu (on ne connaît pas encore J+1).
    """
    feats = add_features(to_daily(df_hourly))
    feats[TARGET_COLUMN] = feats["pm2_5"].shift(-1) - feats["pm2_5"]
    return feats.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN])


def build_training_frame(df_hourly: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Renvoie (X, y) chronologiquement ordonnés pour l'entraînement."""
    frame = build_supervised_frame(df_hourly)
    if frame.empty:
        raise InsufficientDataError("Pas assez d'historique pour entraîner le modèle.")
    return frame[FEATURE_COLUMNS], frame[TARGET_COLUMN]


def build_inference_row(df_hourly: pd.DataFrame) -> tuple[pd.DataFrame, float, pd.Timestamp]:
    """Renvoie (X d'une ligne pour le dernier jour, PM2.5 du jour, date du jour)."""
    feats = add_features(to_daily(df_hourly))
    last = feats.tail(1)[FEATURE_COLUMNS]
    if len(feats) < ROLLING_WINDOW or last.isnull().values.any():
        raise InsufficientDataError(
            f"Historique insuffisant : au moins {ROLLING_WINDOW} jours de données sont nécessaires."
        )
    return last, float(feats["pm2_5"].iloc[-1]), feats.index[-1]
