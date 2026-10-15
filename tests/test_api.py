"""Smoke tests for the demand API."""
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)
SAMPLE = {"temperature_2m":8,"wind_speed_10m":15,"relative_humidity_2m":82,"hour_of_day":18,
          "day_of_week":2,"month":1,"demand_lag_1h":4200,"demand_lag_24h":4300,
          "demand_lag_168h":4250,"demand_roll_24h":3900,"demand_roll_168h":3950,
          "is_weekend":0,"is_holiday":0}

def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"

def test_predict_in_range():
    r = client.post("/predict", json=SAMPLE)
    assert r.status_code == 200
    assert 1000 < r.json()["predicted_demand_mw"] < 8000
