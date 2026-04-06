import pandas as pd
import numpy as np
from sklearn.multioutput import MultiOutputRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from lightgbm import LGBMRegressor
from .feature import create_features
import os
import joblib


def train_model(df):

    df = df.sort_values("date")
    df_feat = create_features(df)

    features = [col for col in df_feat.columns if col not in ["date", "AQI", "PM2_5", "pm2_5", "european_aqi"]]

    X = df_feat[features]
    y = df_feat[["AQI", "PM2_5"]]

    split_idx = int(len(df) * 0.8)

    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    # modèle
    model_xgb = XGBRegressor(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )


    model_final = MultiOutputRegressor(model_xgb)

    model_final.fit(X_train, y_train)

    # prediction
    y_pred = model_final.predict(X_test)

    # save the models
    os.makedirs("models", exist_ok=True)
    joblib.dump(model_final, "models/xgb.pkl")
    joblib.dump(features, "models/feature.pkl")

    # 

    return model_final, features, X_test, y_test, y_pred