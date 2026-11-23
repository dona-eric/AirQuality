import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api import main
from src.models.train import train_model
from tests.conftest import make_hourly


@pytest.fixture
def client(monkeypatch):
    df = make_hourly()
    model = train_model(df, {"n_estimators": 10, "max_depth": 2, "n_jobs": 1})[0]
    monkeypatch.setattr(main, "load_model", lambda: (model, "test"))
    monkeypatch.setattr(main, "get_df_fast", lambda: df.copy())
    monkeypatch.setenv("ENABLE_ETL_SCHEDULER", "0")
    with TestClient(main.app) as c:
        yield c, df


def test_health(client):
    c, df = client
    body = c.get("/health").json()
    assert body["model_loaded"] is True
    assert body["data_rows"] == len(df)


@pytest.mark.parametrize("method", ["get", "post"])
def test_predict(client, method):
    c, df = client
    r = getattr(c, method)("/predict")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["date_prevision"] == (df.index.max().normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    assert body["model_source"] == "test"


def test_history(client):
    c, _ = client
    body = c.get("/history").json()
    assert len(body["dates"]) == len(body["values"]) == 7


def test_data_endpoint_matches_frontend_contract(client):
    c, df = client
    body = c.get("/data", params={"days": 2}).json()
    assert body["count"] == len(body["records"]) > 0
    rec = body["records"][0]
    for col in ("date", "pm2_5", "pm10", "ozone", "nitrogen_dioxide", "european_aqi"):
        assert col in rec
    assert "id" not in rec
    assert rec["formaldehyde"] is None  # NaN sérialisé en null


def test_predict_without_model_returns_503(client):
    c, _ = client
    main.state["model"] = None
    assert c.post("/predict").status_code == 503


def test_predict_without_data_returns_503(client, monkeypatch):
    c, _ = client
    monkeypatch.setattr(main, "get_df_fast", lambda: pd.DataFrame())
    assert c.post("/predict").status_code == 503
