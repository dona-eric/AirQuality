from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DataResponse(BaseModel):
    count: int
    records: List[Dict[str, Any]]


class PredictionResponse(BaseModel):
    date_prevision: str
    current_pm25: float
    predicted_pm25: float
    delta: float
    aqi_label: str
    conseil: str
    data_last_update: Optional[str] = None
    model_source: Optional[str] = None


class HistoryResponse(BaseModel):
    dates: List[str]
    values: List[Optional[float]]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_source: Optional[str] = None
    data_rows: int
    data_last_update: Optional[str] = None
