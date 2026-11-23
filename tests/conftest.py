import numpy as np
import pandas as pd
import pytest

from src.models.features import POLLUTANT_COLUMNS

# Script manuel qui se connecte à DagsHub : ne fait pas partie de la suite de tests.
collect_ignore = ["test_mlflow.py"]


def make_hourly(days: int = 60, seed: int = 0) -> pd.DataFrame:
    """Données horaires synthétiques, au format de get_df_fast()."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2026-01-01", periods=days * 24, freq="h", tz="UTC", name="date")
    t = np.arange(len(idx))
    base = 20 + 8 * np.sin(2 * np.pi * t / (24 * 14)) + rng.normal(0, 2, len(idx))
    df = pd.DataFrame({c: base * (1 + i / 10) for i, c in enumerate(POLLUTANT_COLUMNS)}, index=idx)
    df["formaldehyde"] = np.nan
    df["id"] = np.arange(len(idx))
    return df


@pytest.fixture
def hourly_df():
    return make_hourly()
