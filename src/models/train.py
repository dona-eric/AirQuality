import mlflow.xgboost
import dagshub
import pandas as pd
import matplotlib.pyplot as plt
import logging
import xgboost as xgb
import pathlib
from src.etl.quality_air import DB_PATH, PARQUET_PATH, export_format
from src.api.utils import get_df_fast
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import dotenv
import os
import sqlite3
import numpy as np
from huggingface_hub import upload_file

#=================CONFIGURATION===========================
dagshub.init(
     repo_name="air-quality",
     repo_owner="dona-eric",
     url="https://dagshub.com/dona-eric/air-quality.mlflow",
     mlflow=True
 )
mlflow.set_experiment("Xgboost_AirQuality_V2")

mlflow.xgboost.autolog(
    log_input_examples=True,
    log_model_signatures=True,
    log_models=False,
    log_datasets=True,
    disable=False,
    model_format="json",
    extra_tags={"team": "data-science"})

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

# Chemins structurés
BASE_DIR = pathlib.Path(__file__).parent
REPO_ID = "donerick/air-quality-storage"
TOKEN = os.getenv("HF_TOKEN")

#==================TRAINING===============================

def train():
    """
    Train an XGBoost model and log the results to MLflow.

    Args:
        data (pd.DataFrame): The input data for training.
        target (str): The name of the target variable.
        params (dict): Hyperparameters for the XGBoost model.
        test_size (float): The proportion of the dataset to include in the test split.
        random_state (int): Controls the randomness of the train-test split.

    Returns:
        xgb.Booster: The trained XGBoost model.
    """
    df = get_df_fast()

    df_daily = df.resample("D").mean(numeric_only=True)

    if df_daily["formaldehyde"].isnull().mean() >0.5:
        df_daily = df_daily.drop(columns=["formaldehyde"])
    else:
        df_daily["formaldehyde"] = df_daily["formaldehyde"].interpolate()


    df_daily = df_daily.interpolate(method='linear')

    df_daily['pm25_diff'] = df_daily['pm2_5'].diff()

    # Features de retard (Lags)
    for i in range(1, 4):
        df_daily[f'pm25_lag_{i}'] = df_daily['pm2_5'].shift(i)
        df_daily[f'co_lag_{i}'] = df_daily['carbon_monoxide'].shift(i)

    # Tendance hebdomadaire
    df_daily['pm25_rolling_7d'] = df_daily['pm2_5'].rolling(window=7).mean()

    # Variables temporelles
    df_daily['day_of_week'] = df_daily.index.dayofweek
    df_daily['month'] = df_daily.index.month

    # On supprime les lignes vides créées par les décalages (les premières et la dernière)
    df_model = df_daily.dropna()

    # Split into training and testing sets
    #Split chronologique (80% train, 20% test)
    split_idx = int(len(df_model) * 0.8)
    train = df_model.iloc[:split_idx]
    test = df_model.iloc[split_idx:]

    X_train = train.drop(columns=['pm25_diff', 'id'], errors='ignore')
    y_train = train['pm25_diff']
    X_test = test.drop(columns=['pm25_diff','id'], errors='ignore')
    y_test = test['pm25_diff']
    
    # Create DMatrix for XGBoost
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)

    params = {
        "learning_rate": 0.05,
        "max_depth": 5,
        "subsample": 0.8,
        "objective": 'reg:squarederror'
    }
    num_boost_round = 500
    # Train the model

    with mlflow.start_run(run_name="XGBoostPipeline") as run:
        mlflow.log_params(params)
        model = xgb.train(
            params=params, 
            dtrain=dtrain,
            num_boost_round=num_boost_round,
            evals=[(dtrain, "train"), (dtest, "test")],
            verbose_eval=False
            )

        # Make predictions
        y_pred = model.predict(dtest)

        # Evaluate the model
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mse)

        mlflow.log_metric("mse", mse)
        mlflow.log_metric("r2", r2)
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("rmse", rmse)



        # --- FIG: Réel vs Prédiction ---
        plt.figure(figsize=(10, 5))
        plt.plot(y_test.values, label="Réel (Delta)")
        plt.plot(y_pred, label="Prédit (Delta)", alpha=0.7)
        plt.title(f"Validation - MAE: {mae:.2f}")
        plt.legend()
        plt.savefig("val_plot.png")
        mlflow.log_artifact("val_plot.png")

        # Log the model
        # signature 
        signature = mlflow.models.signature.infer_signature(X_train, y_pred)
        model_info = mlflow.xgboost.log_model(
            xgb_model=model,
            name="xgboost_model",
            model_format="json",
            signature=signature,
            registered_model_name="AirQualityXGBoostModel"
            )
        
        logging.info(f"Run terminé. ID: {run.info.run_id}")


        logging.info(f"======================= SHAP EXPLAINER =======================")
        eval_data = X_test.copy()
        eval_data["target"] = y_test.values
        results = mlflow.models.evaluate(
            model=model_info.model_uri,
            data=eval_data,
            targets="target",
            model_type="regressor",
            evaluator_config={
                "log_explainer": True,
                "explainer_type": "exact",
                "max_error_examples":100,
                "log_model_explanation": True
            }
        )

        logging.info(f"Evaluation terminée. Metrics: {results.metrics.items()}")
    client = mlflow.MlflowClient()

    versions = client.search_model_versions(f"name='AirQualityXGBoostModel'")
    if not versions:
        logger.warning("Aucune version du modèle trouvée, alias non défini.")
    else:
        model_version = sorted(versions, key=lambda v: int(v.version))[-1]
        
    client.set_registered_model_alias(
        name="AirQualityXGBoostModel",
        alias="champion",
        version=model_version.version,
    )
    client.set_model_version_tag(
        name="AirQualityXGBoostModel",
        version=model_version.version,
        key="validation_status",
        value="approved",
    )
    client.set_model_version_tag(
        name="AirQualityXGBoostModel",
        version=model_version.version,
        key="shap_explainer_type",
        value="gain",
    )
    logger.info(f"Alias 'champion' → version {model_version.version}")
    
    model.save_model("model.json")

    # Upload as latest and as version v2
    paths = ["models/xgboost_model.json", "models/v2/xgboost_model.json"]
    for path in paths:
        try:
            upload_file(
                path_or_fileobj="model.json",
                path_in_repo=path,
                repo_id=REPO_ID,
                repo_type="dataset",
                token=TOKEN
            )
            logger.info(f"Modèle uploadé sur HuggingFace à {path} ✓")
        except Exception as e:
            logger.error(f"Erreur lors de l'upload vers {path} : {e}")
if __name__=="__main__":
    train()