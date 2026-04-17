from pydantic import BaseModel
from typing import List

class DataResponse(BaseModel):
    dates: List[str]
    pm2_5: List[float]
    pm10: List[float]
    european_aqi: List[float]

class PredictionResponse(BaseModel):
    date_prevision: str
    current_pm25: float
    predicted_pm25: float
    delta: float
    aqi_label: str
    conseil: str

class HistoryResponse(BaseModel):
    dates: List[str]
    values: List[float]