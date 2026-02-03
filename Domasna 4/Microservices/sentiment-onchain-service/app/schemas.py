from pydantic import BaseModel
from typing import Optional, Dict, Any


class SentimentPart(BaseModel):
    articleCount: int
    positiveRatio: float
    neutralRatio: float
    negativeRatio: float
    score: float
    interpretation: str


class CombinedPart(BaseModel):
    finalScore: float
    signal: str
    explanation: str


class SentimentOnChainResponse(BaseModel):
    symbol: str
    sentiment: Dict[str, Any]
    onchain: Optional[Dict[str, Any]]
    combined: CombinedPart
