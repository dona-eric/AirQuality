import pytest
import xgboost as xgb

from src.models.features import FEATURE_COLUMNS
from src.models.inference import get_aqi_info, predict_next_day
from src.models.registry import _read_model, load_model, save_model
from src.models.train import load_params, train_model

FAST_PARAMS = {"n_estimators": 20, "max_depth": 2, "learning_rate": 0.1, "n_jobs": 1}


@pytest.fixture
def trained(hourly_df):
    return train_model(hourly_df, FAST_PARAMS)


def test_train_returns_metrics(trained):
    model, metrics, (X_test, y_test, y_pred) = trained
    for key in ("mae_pm25", "rmse_pm25", "mae_persistence", "skill_vs_persistence", "n_train", "n_test"):
        assert key in metrics
    assert metrics["n_test"] == len(X_test) == len(y_pred)
    assert list(model.get_booster().feature_names) == FEATURE_COLUMNS


def test_params_yaml_is_read():
    params = load_params()
    assert params["n_jobs"] == 1
    assert "max_depth" in params


def test_save_load_roundtrip(trained, hourly_df, tmp_path):
    model = trained[0]
    path = save_model(model, tmp_path / "m.json")
    loaded, source = load_model(local_path=path)
    assert source == f"local:{path}"
    assert predict_next_day(loaded, hourly_df) == predict_next_day(model, hourly_df)


def test_incompatible_model_is_rejected(hourly_df, tmp_path):
    from src.models.features import build_training_frame

    X, y = build_training_frame(hourly_df)
    X = X.assign(formaldehyde=0.0)  # ancien jeu de features
    path = tmp_path / "old.json"
    xgb.XGBRegressor(n_estimators=2).fit(X, y).save_model(str(path))
    with pytest.raises(ValueError, match="features"):
        _read_model(path)


def test_prediction_payload(trained, hourly_df):
    res = predict_next_day(trained[0], hourly_df)
    assert res["predicted_pm25"] >= 0
    assert res["delta"] == pytest.approx(res["predicted_pm25"] - res["current_pm25"], abs=0.011)
    assert res["date_prevision"] > hourly_df.index.max().strftime("%Y-%m-%d")


@pytest.mark.parametrize("value,label", [(5, "Bon"), (20, "Modéré"), (50, "Mauvais"), (80, "Très Mauvais")])
def test_aqi_labels(value, label):
    assert get_aqi_info(value)[0] == label
