"""Train demand forecaster: seasonal-naive baseline vs XGBoost, tracked in MLflow + registry."""
import os, numpy as np, pandas as pd
import xgboost as xgb
import mlflow, mlflow.xgboost
from sklearn.metrics import mean_absolute_error, mean_squared_error

df = pd.read_parquet("data/features/feature_matrix.parquet").sort_values("ts_hour")
TARGET = "demand_mw"
FEATURES = [c for c in df.columns if c not in ["ts_hour", TARGET]]

cutoff = df["ts_hour"].max() - pd.Timedelta(days=30)
train, test = df[df.ts_hour <= cutoff], df[df.ts_hour > cutoff]
X_train, y_train = train[FEATURES], train[TARGET]
X_test,  y_test  = test[FEATURES],  test[TARGET]
print(f"train={len(train)}  test={len(test)}  features={len(FEATURES)}")

def metrics(y, p):
    return {"mae": mean_absolute_error(y, p),
            "rmse": mean_squared_error(y, p) ** 0.5,
            "mape": (np.abs((y - p) / y)).mean() * 100}

# Env-configurable so it works both locally and inside the Airflow container
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
EXP = os.getenv("MLFLOW_EXPERIMENT", "irish-energy-demand")
if mlflow.get_experiment_by_name(EXP) is None:
    mlflow.create_experiment(EXP, artifact_location=os.getenv("MLFLOW_ARTIFACT_LOCATION", "./mlruns"))
mlflow.set_experiment(EXP)

with mlflow.start_run(run_name="baseline_seasonal_naive"):
    m = metrics(y_test, test["demand_lag_168h"])
    mlflow.log_param("model", "seasonal_naive_168h"); mlflow.log_metrics(m)
    print(f"baseline  MAE={m['mae']:.0f}  RMSE={m['rmse']:.0f}  MAPE={m['mape']:.2f}%")

with mlflow.start_run(run_name="xgboost"):
    params = dict(n_estimators=400, max_depth=6, learning_rate=0.05,
                  subsample=0.9, colsample_bytree=0.9, random_state=42)
    model = xgb.XGBRegressor(**params); model.fit(X_train, y_train)
    m = metrics(y_test, model.predict(X_test))
    mlflow.log_params(params); mlflow.log_metrics(m)
    mlflow.xgboost.log_model(model, name="model",
                             input_example=X_test.iloc[:3],
                             registered_model_name="energy_demand_xgb")
    print(f"xgboost   MAE={m['mae']:.0f}  RMSE={m['rmse']:.0f}  MAPE={m['mape']:.2f}%")
print("Done.")
