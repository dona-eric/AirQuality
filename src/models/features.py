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

Features de la ligne J (uniquement des informations connues au jour J)
------------------------------------------------------------------------
- moyennes journalières des polluants, lags J-1..J-3, moyenne glissante 7 j, calendrier
- dynamique intra-journalière : niveau en fin de journée J (dernière heure, 6 dernières heures…)
- météo du jour J                                      (préfixe w_)
- météo PRÉVUE pour J+1, telle que connue au jour J    (préfixe wn_)
- évolution météo prévue J → J+1                       (préfixe wd_)

Pour la météo de J+1 :
  - jours passés (entraînement) : prévision émise la veille (`*_prev1`)
  - lendemain du dernier jour (inférence) : dernière prévision disponible
Les deux correspondent à une échéance d'environ 24-48 h, comme en production.
"""

import numpy as np
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
BASE_COLUMNS = (
    POLLUTANT_COLUMNS
    + [col for i in LAG_DAYS for col in (f"pm25_lag_{i}", f"co_lag_{i}")]
    + ["pm25_rolling_7d", "day_of_week", "month"]
)

INTRADAY_COLUMNS = [
    "pm25_last",
    "pm25_last6",
    "pm25_max",
    "pm25_std",
    "pm10_last6",
    "co_last6",
    "pm25_last6_minus_mean",
]

# Variables météo journalières (calculées à partir des variables horaires Open-Meteo)
WEATHER_VARS = ["temp", "rh", "precip", "wind", "wind_u", "wind_v", "pressure"]
WEATHER_HOURLY = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
]
PREV_SUFFIX = "_prev1"
WEATHER_COLUMNS = [f"{p}_{v}" for p in ("w", "wn", "wd") for v in WEATHER_VARS]

FEATURE_COLUMNS = BASE_COLUMNS + INTRADAY_COLUMNS + WEATHER_COLUMNS
TARGET_COLUMN = "pm25_next_delta"


class InsufficientDataError(ValueError):
    """Pas assez d'historique (ou de météo) pour construire les features."""


# ===================== QUALITÉ D'AIR =====================

def to_daily(df_hourly: pd.DataFrame) -> pd.DataFrame:
    """Agrège les mesures horaires (index DatetimeIndex) en moyennes journalières."""
    if df_hourly is None or df_hourly.empty:
        raise InsufficientDataError("Aucune donnée de qualité d'air disponible.")
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


def intraday_features(df_hourly: pd.DataFrame) -> pd.DataFrame:
    """Niveau de pollution en fin de journée : meilleur point de départ pour J+1."""
    h = df_hourly.sort_index()
    by_day = h.resample("D")
    out = pd.DataFrame({
        "pm25_last": by_day["pm2_5"].last(),
        "pm25_last6": h["pm2_5"].rolling(6, min_periods=1).mean().resample("D").last(),
        "pm25_max": by_day["pm2_5"].max(),
        "pm25_std": by_day["pm2_5"].std(),
        "pm10_last6": h["pm10"].rolling(6, min_periods=1).mean().resample("D").last(),
        "co_last6": h["carbon_monoxide"].rolling(6, min_periods=1).mean().resample("D").last(),
    })
    return out.interpolate(method="linear", limit_direction="both")


# ===================== MÉTÉO =====================

def daily_weather(weather_hourly: pd.DataFrame, suffix: str = "") -> pd.DataFrame:
    """Agrège la météo horaire (colonnes `<variable><suffix>`) en variables journalières."""
    cols = [f"{v}{suffix}" for v in WEATHER_HOURLY]
    missing = [c for c in cols if c not in weather_hourly.columns]
    if missing:
        raise ValueError(f"Colonnes météo manquantes : {missing}")
    w = weather_hourly[cols].copy()
    w.columns = WEATHER_HOURLY

    rad = np.deg2rad(w["wind_direction_10m"])
    w["wind_u"] = -w["wind_speed_10m"] * np.sin(rad)  # composante est-ouest (d'où vient le vent)
    w["wind_v"] = -w["wind_speed_10m"] * np.cos(rad)  # composante nord-sud
    by_day = w.sort_index().resample("D")
    return pd.DataFrame({
        "temp": by_day["temperature_2m"].mean(),
        "rh": by_day["relative_humidity_2m"].mean(),
        "precip": by_day["precipitation"].sum(min_count=1),
        "wind": by_day["wind_speed_10m"].mean(),
        "wind_u": by_day["wind_u"].mean(),
        "wind_v": by_day["wind_v"].mean(),
        "pressure": by_day["surface_pressure"].mean(),
    })


def day_ahead_weather(weather_hourly: pd.DataFrame, last_day: pd.Timestamp) -> pd.DataFrame:
    """Météo de chaque jour D telle qu'elle était prévue la veille (D-1).

    - D <= last_day : prévision émise la veille (`*_prev1`)
    - D == last_day + 1 : dernière prévision disponible (émise au jour last_day)
    """
    prev = daily_weather(weather_hourly, PREV_SUFFIX)
    current = daily_weather(weather_hourly)
    out = prev[prev.index <= last_day]
    tomorrow = last_day + pd.Timedelta(days=1)
    if tomorrow in current.index:
        out = pd.concat([out, current.loc[[tomorrow]]])
    return out


def weather_features(weather_hourly: pd.DataFrame, days: pd.DatetimeIndex) -> pd.DataFrame:
    """Colonnes w_*, wn_*, wd_* pour chaque jour de `days`."""
    if weather_hourly is None or weather_hourly.empty:
        raise InsufficientDataError("Aucune donnée météo disponible. Lancez : python -m src.etl.weather")
    current = daily_weather(weather_hourly).reindex(days)
    ahead = day_ahead_weather(weather_hourly, days.max())
    next_day = ahead.reindex(days + pd.Timedelta(days=1))
    next_day.index = days
    return pd.concat(
        [current.add_prefix("w_"), next_day.add_prefix("wn_"), (next_day - current).add_prefix("wd_")],
        axis=1,
    )


# ===================== ASSEMBLAGE =====================

def build_feature_frame(df_hourly: pd.DataFrame, weather_hourly: pd.DataFrame) -> pd.DataFrame:
    """Toutes les features, une ligne par jour de données de qualité d'air."""
    feats = add_features(to_daily(df_hourly))
    intra = intraday_features(df_hourly).reindex(feats.index)
    intra["pm25_last6_minus_mean"] = intra["pm25_last6"] - feats["pm2_5"]
    return pd.concat([feats, intra, weather_features(weather_hourly, feats.index)], axis=1)


def build_supervised_frame(df_hourly: pd.DataFrame, weather_hourly: pd.DataFrame) -> pd.DataFrame:
    """Features + cible, sans valeurs manquantes. Le dernier jour (J+1 inconnu) est exclu."""
    feats = build_feature_frame(df_hourly, weather_hourly)
    feats[TARGET_COLUMN] = feats["pm2_5"].shift(-1) - feats["pm2_5"]
    return feats.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN])


def build_training_frame(df_hourly, weather_hourly) -> tuple[pd.DataFrame, pd.Series]:
    """Renvoie (X, y) chronologiquement ordonnés pour l'entraînement."""
    frame = build_supervised_frame(df_hourly, weather_hourly)
    if frame.empty:
        raise InsufficientDataError("Pas assez d'historique pour entraîner le modèle.")
    return frame[FEATURE_COLUMNS], frame[TARGET_COLUMN]


def build_inference_row(df_hourly, weather_hourly) -> tuple[pd.DataFrame, float, pd.Timestamp]:
    """Renvoie (X d'une ligne pour le dernier jour, PM2.5 du jour, date du jour)."""
    feats = build_feature_frame(df_hourly, weather_hourly)
    last = feats.tail(1)[FEATURE_COLUMNS]
    if len(feats) < ROLLING_WINDOW or last[BASE_COLUMNS + INTRADAY_COLUMNS].isnull().values.any():
        raise InsufficientDataError(
            f"Historique insuffisant : au moins {ROLLING_WINDOW} jours de données sont nécessaires."
        )
    if last[WEATHER_COLUMNS].isnull().values.any():
        raise InsufficientDataError(
            f"Prévision météo manquante pour le {feats.index[-1] + pd.Timedelta(days=1):%Y-%m-%d}. "
            "Relancez la collecte : python -m src.etl.weather"
        )
    return last, float(feats["pm2_5"].iloc[-1]), feats.index[-1]
