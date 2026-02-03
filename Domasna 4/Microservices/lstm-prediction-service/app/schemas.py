from pydantic import BaseModel
from typing import Optional

class PredictionResponse(BaseModel):
    symbol: str
    prediction_date: str
    predicted_close: float
    rmse: Optional[float]
    mae: Optional[float]
    mape: Optional[float]
    r2: Optional[float]
