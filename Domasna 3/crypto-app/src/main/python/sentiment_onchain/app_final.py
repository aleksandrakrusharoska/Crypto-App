from flask import Flask, jsonify
from flask_cors import CORS
import logging
from datetime import datetime

from sentiment_analysis import (
    analyze_sentiment_for_symbol,
    setup_sentiment_logging
)

from onchain.dispatcher import analyze_onchain

# ===================== APP SETUP =====================

app = Flask(__name__)
CORS(app)

logger = logging.getLogger(__name__)
setup_sentiment_logging()


# ===================== HELPERS =====================

def calculate_onchain_score(onchain: dict | None) -> float:
    if not onchain or "error" in onchain:
        return 0.5

    core = onchain.get("core")
    if not isinstance(core, dict) or "error" in core:
        return 0.5

    score = 0.5

    nvt = core.get("nvt")
    price_change = core.get("priceChange24h")

    if isinstance(nvt, (int, float)):
        if nvt < 40:
            score += 0.2
        elif nvt > 80:
            score -= 0.2

    if isinstance(price_change, (int, float)):
        score += 0.15 if price_change > 0 else -0.15

    return max(0.0, min(1.0, round(score, 3)))


# ===================== ENDPOINTS =====================

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "modules": {
            "sentiment": "ACTIVE",
            "on_chain": "ACTIVE (MULTI-COIN, DEFENSIVE)"
        }
    }), 200


# ===================== COMBINED ANALYSIS =====================

@app.route("/api/analyze/<symbol>", methods=["GET"])
def analyze_combined(symbol):
    symbol = symbol.upper()

    try:
        # =====================
        # 1️⃣ SENTIMENT
        # =====================
        raw_sentiment = analyze_sentiment_for_symbol(symbol)

        sentiment_result = {
            "articleCount": raw_sentiment.get("articles_analyzed", 0),
            "positiveRatio": round(raw_sentiment.get("positive_ratio", 0), 3),
            "neutralRatio": round(raw_sentiment.get("neutral_ratio", 0), 3),
            "negativeRatio": round(raw_sentiment.get("negative_ratio", 0), 3),
            "interpretation": raw_sentiment.get(
                "interpretation",
                "Sentiment data not available."
            ),
            "score": round(raw_sentiment.get("final_sentiment_score", 0.5), 3)
        }

        sentiment_score = sentiment_result["score"]

        # =====================
        # 2️⃣ ON-CHAIN (DEFENSIVE)
        # =====================
        raw_onchain = analyze_onchain(symbol)

        print("ONCHAIN RAW:", raw_onchain)

        onchain_result = raw_onchain if isinstance(raw_onchain, dict) else None
        onchain_score = calculate_onchain_score(onchain_result)

        # =====================
        # 3️⃣ COMBINED SCORE
        # =====================
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

        combined_result = {
            "sentimentScore": sentiment_score,
            "onchainScore": onchain_score,
            "finalScore": final_score,
            "calculation": (
                f"sentimentScore × 0.5 + onchainScore × 0.5 = "
                f"({round(sentiment_score, 3)} × 0.5) + "
                f"({round(onchain_score, 3)} × 0.5) = "
                f"{round(final_score, 3)} ≈ {round(final_score, 2)}"
            ),
            "signal": signal,
            "explanation": (
                f"Combined score based on sentiment ({sentiment_score}) "
                f"and on-chain metrics ({onchain_score})."
            )
        }

        # =====================
        # 4️⃣ RESPONSE (UI SAFE)
        # =====================
        return jsonify({
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "sentiment": sentiment_result,
            "onchain": onchain_result,
            "combined": combined_result
        }), 200

    except Exception as e:
        logger.error(f"Combined analysis error for {symbol}: {e}")

        return jsonify({
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),

            # ✅ ако sentiment постои – го враќаме
            "sentiment": sentiment_result if 'sentiment_result' in locals() else None,

            # ✅ ако on-chain постои – го враќаме
            "onchain": onchain_result if 'onchain_result' in locals() else None,

            # ❌ combined паднал → но UI-friendly fallback
            "combined": {
                "signal": "N/A",
                "explanation": "Combined analysis could not be calculated for this asset."
            },

            "error": str(e)
        }), 200


# ===================== START =====================

if __name__ == "__main__":
    logger.info("🚀 Starting MULTI-COIN Crypto Analysis API")

    app.run(
        host="0.0.0.0",
        port=5002,
        debug=False,
        threaded=True
    )
