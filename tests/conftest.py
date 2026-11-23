import numpy as np
import pandas as pd
import pytest

from src.models.features import POLLUTANT_COLUMNS, PREV_SUFFIX, WEATHER_HOURLY

# Script manuel qui se connecte à DagsHub : ne fait pas partie de la suite de tests.
collect_ignore = ["test_mlflow.py"]

START = "2026-01-01"


def make_hourly(days: int = 60, seed: int = 0) -> pd.DataFrame:
    """Données horaires synthétiques de qualité d'air, au format de get_df_fast()."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range(START, periods=days * 24, freq="h", tz="UTC", name="date")
    t = np.arange(len(idx))
    base = 20 + 8 * np.sin(2 * np.pi * t / (24 * 14)) + rng.normal(0, 2, len(idx))
    df = pd.DataFrame({c: base * (1 + i / 10) for i, c in enumerate(POLLUTANT_COLUMNS)}, index=idx)
    df["formaldehyde"] = np.nan
    df["id"] = np.arange(len(idx))
    return df


def make_weather(days: int = 60, extra_days: int = 2, seed: int = 1) -> pd.DataFrame:
    """Météo horaire synthétique au format de get_weather_df() (+ `extra_days` de prévision)."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range(pd.Timestamp(START, tz="UTC") - pd.Timedelta(days=7),
                        periods=(days + 7 + extra_days) * 24, freq="h", name="date")
    df = pd.DataFrame({v: rng.uniform(0, 100, len(idx)) for v in WEATHER_HOURLY}, index=idx)
    df["wind_direction_10m"] = rng.uniform(0, 360, len(idx))
    for v in WEATHER_HOURLY:  # prévision de la veille = valeur bruitée
        df[f"{v}{PREV_SUFFIX}"] = df[v] + rng.normal(0, 1, len(idx))
    return df


@pytest.fixture
def hourly_df():
    return make_hourly()


@pytest.fixture
def weather_df():
    return make_weather()
