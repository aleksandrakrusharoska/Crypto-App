from fastapi import APIRouter
from app.schemas import SentimentOnChainResponse
from app.service.sentiment import analyze_sentiment
from app.service.onchain import analyze_onchain, calculate_onchain_score

router = APIRouter(prefix="/api", tags=["analysis"])


@router.get("/health")
def health():
    return {
        "status": "ok",
        "modules": {
            "sentiment": "ACTIVE",
            "onchain": "ACTIVE"
        }
    }


@router.get("/analyze/{symbol}", response_model=SentimentOnChainResponse)
def analyze(symbol: str):
    """
    Aggregates sentiment and on-chain analysis results
    into a unified trading signal.
    """

    symbol = symbol.upper()

    sentiment_result = analyze_sentiment(symbol)
    sentiment_score = sentiment_result["score"]

    onchain_result = analyze_onchain(symbol)
    onchain_score = calculate_onchain_score(onchain_result)

    # Equal-weighted combination of sentiment and on-chain scores
    final_score = round(
        sentiment_score * 0.5 + onchain_score * 0.5,
        3
    )

    if final_score >= 0.8:
        signal = "STRONG_BUY"
    elif final_score >= 0.65:
        signal = "BUY"
    elif final_score >= 0.45:
        signal = "HOLD"
    elif final_score >= 0.3:
        signal = "SELL"
    else:
        signal = "STRONG_SELL"

    return {
        "symbol": symbol,
        "sentiment": sentiment_result,
        "onchain": onchain_result,
        "combined": {
            "finalScore": final_score,
            "signal": signal,
            "explanation": (
                f"sentimentScore × 0.5 + onchainScore × 0.5 = "
                f"{sentiment_score} × 0.5 + {onchain_score} × 0.5"
            )
        }
    }
