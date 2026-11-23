import numpy as np
import pytest

from src.models.features import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    InsufficientDataError,
    add_features,
    build_inference_row,
    build_supervised_frame,
    to_daily,
)
from tests.conftest import make_hourly


def test_target_is_next_day_delta(hourly_df):
    frame = build_supervised_frame(hourly_df)
    daily = to_daily(hourly_df)["pm2_5"]
    day = frame.index[5]
    expected = daily.loc[day + np.timedelta64(1, "D")] - daily.loc[day]
    assert frame.loc[day, TARGET_COLUMN] == pytest.approx(expected)


def test_target_not_computable_from_features(hourly_df):
    """Régression : l'ancienne cible (pm2_5 - pm25_lag_1) fuyait dans les features."""
    frame = build_supervised_frame(hourly_df)
    leaky = frame["pm2_5"] - frame["pm25_lag_1"]
    assert not np.allclose(frame[TARGET_COLUMN], leaky)


def test_features_do_not_depend_on_future(hourly_df):
    """Modifier le lendemain ne doit pas changer les features du jour."""
    feats = add_features(to_daily(hourly_df))
    day = feats.index[20]
    altered = hourly_df.copy()
    altered.loc[altered.index >= day + np.timedelta64(1, "D"), "pm2_5"] += 100
    feats_altered = add_features(to_daily(altered))
    assert feats.loc[day, FEATURE_COLUMNS].equals(feats_altered.loc[day, FEATURE_COLUMNS])


def test_last_day_excluded_from_training(hourly_df):
    frame = build_supervised_frame(hourly_df)
    assert frame.index.max() < to_daily(hourly_df).index.max()


def test_inference_row_matches_training_features(hourly_df):
    X, current, day = build_inference_row(hourly_df)
    feats = add_features(to_daily(hourly_df))
    assert list(X.columns) == FEATURE_COLUMNS
    assert day == feats.index[-1]
    assert current == pytest.approx(feats["pm2_5"].iloc[-1])
    assert X.iloc[0].equals(feats.loc[day, FEATURE_COLUMNS])


def test_formaldehyde_and_id_are_ignored(hourly_df):
    assert "formaldehyde" not in FEATURE_COLUMNS
    X, _, _ = build_inference_row(hourly_df)
    assert not X.isnull().values.any()


def test_insufficient_history_raises():
    with pytest.raises(InsufficientDataError):
        build_inference_row(make_hourly(days=3))
