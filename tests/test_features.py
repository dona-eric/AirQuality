import numpy as np
import pandas as pd
import pytest

from src.models.features import (
    FEATURE_COLUMNS,
    PREV_SUFFIX,
    TARGET_COLUMN,
    InsufficientDataError,
    build_feature_frame,
    build_inference_row,
    build_supervised_frame,
    daily_weather,
    to_daily,
)
from tests.conftest import make_hourly, make_weather

ONE_DAY = pd.Timedelta(days=1)


def test_target_is_next_day_delta(hourly_df, weather_df):
    frame = build_supervised_frame(hourly_df, weather_df)
    daily = to_daily(hourly_df)["pm2_5"]
    day = frame.index[5]
    assert frame.loc[day, TARGET_COLUMN] == pytest.approx(daily.loc[day + ONE_DAY] - daily.loc[day])


def test_target_not_computable_from_features(hourly_df, weather_df):
    """Régression : l'ancienne cible (pm2_5 - pm25_lag_1) fuyait dans les features."""
    frame = build_supervised_frame(hourly_df, weather_df)
    assert not np.allclose(frame[TARGET_COLUMN], frame["pm2_5"] - frame["pm25_lag_1"])


def test_features_do_not_depend_on_future_air_quality(hourly_df, weather_df):
    """Modifier la qualité d'air du lendemain ne doit pas changer les features du jour."""
    feats = build_feature_frame(hourly_df, weather_df)
    day = feats.index[20]
    altered = hourly_df.copy()
    altered.loc[altered.index >= day + ONE_DAY, ["pm2_5", "pm10", "carbon_monoxide"]] += 100
    pd.testing.assert_series_equal(feats.loc[day, FEATURE_COLUMNS],
                                   build_feature_frame(altered, weather_df).loc[day, FEATURE_COLUMNS])


def test_training_uses_day_before_forecast_for_next_day(hourly_df, weather_df):
    """Pour les jours passés, la météo J+1 doit venir de la prévision émise la veille."""
    feats = build_feature_frame(hourly_df, weather_df)
    day = feats.index[20]
    prev = daily_weather(weather_df, PREV_SUFFIX)
    current = daily_weather(weather_df)
    assert feats.loc[day, "wn_temp"] == pytest.approx(prev.loc[day + ONE_DAY, "temp"])
    assert feats.loc[day, "w_temp"] == pytest.approx(current.loc[day, "temp"])
    assert feats.loc[day, "wd_temp"] == pytest.approx(prev.loc[day + ONE_DAY, "temp"] - current.loc[day, "temp"])


def test_inference_uses_latest_forecast_for_tomorrow(hourly_df, weather_df):
    X, _, day = build_inference_row(hourly_df, weather_df)
    assert X.loc[day, "wn_temp"] == pytest.approx(daily_weather(weather_df).loc[day + ONE_DAY, "temp"])


def test_last_day_excluded_from_training(hourly_df, weather_df):
    frame = build_supervised_frame(hourly_df, weather_df)
    assert frame.index.max() < to_daily(hourly_df).index.max()


def test_inference_row_matches_training_features(hourly_df, weather_df):
    X, current, day = build_inference_row(hourly_df, weather_df)
    assert list(X.columns) == FEATURE_COLUMNS
    assert current == pytest.approx(to_daily(hourly_df)["pm2_5"].iloc[-1])
    assert not X.isnull().values.any()


def test_missing_tomorrow_forecast_raises(hourly_df):
    with pytest.raises(InsufficientDataError, match="météo"):
        build_inference_row(hourly_df, make_weather(extra_days=0))


def test_no_weather_raises(hourly_df):
    with pytest.raises(InsufficientDataError):
        build_inference_row(hourly_df, pd.DataFrame())


def test_insufficient_history_raises():
    with pytest.raises(InsufficientDataError):
        build_inference_row(make_hourly(days=3), make_weather(days=3))


def test_formaldehyde_is_ignored():
    assert "formaldehyde" not in FEATURE_COLUMNS
