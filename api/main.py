"""FastAPI service: serves the registered XGBoost demand model from the MLflow registry."""
import mlflow, mlflow.pyfunc, pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

mlflow.set_tracking_uri("sqlite:///mlflow.db")
MODEL_URI = "models:/energy_demand_xgb/latest"
model = mlflow.pyfunc.load_model(MODEL_URI)

FEATURES = ["temperature_2m","wind_speed_10m","relative_humidity_2m","hour_of_day",
            "day_of_week","month","demand_lag_1h","demand_lag_24h","demand_lag_168h",
            "demand_roll_24h","demand_roll_168h","is_weekend","is_holiday"]
# Columns the model expects as integers (matches the MLflow signature)
INT_COLS = ["relative_humidity_2m","hour_of_day","day_of_week","month","is_weekend","is_holiday"]

class Features(BaseModel):
    temperature_2m: float
    wind_speed_10m: float
    relative_humidity_2m: float
    hour_of_day: int
    day_of_week: int
    month: int
    demand_lag_1h: float
    demand_lag_24h: float
    demand_lag_168h: float
    demand_roll_24h: float
    demand_roll_168h: float
    is_weekend: int
    is_holiday: int

app = FastAPI(title="Irish Energy Demand Forecast API")

@app.get("/health")
def health():
    return {"status": "ok", "model": "energy_demand_xgb"}

@app.post("/predict")
def predict(f: Features):
    X = pd.DataFrame([f.model_dump()])[FEATURES]
    X[INT_COLS] = X[INT_COLS].round().astype("int64")   # match the model's schema (int cols)
    pred = float(model.predict(X)[0])
    return {"predicted_demand_mw": round(pred, 1)}
