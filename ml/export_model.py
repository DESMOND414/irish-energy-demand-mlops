"""Export the registered model to a self-contained folder for containerized serving."""
import shutil, mlflow, mlflow.xgboost
mlflow.set_tracking_uri("sqlite:///mlflow.db")
model = mlflow.xgboost.load_model("models:/energy_demand_xgb/latest")
shutil.rmtree("models_store", ignore_errors=True)
mlflow.xgboost.save_model(model, "models_store")
print("exported model -> models_store/ ✅")
