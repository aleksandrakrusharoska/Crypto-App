from core.sentiment_analysis import analyze_sentiment_for_symbol


def analyze_sentiment(symbol: str) -> dict:
    raw = analyze_sentiment_for_symbol(symbol)

    return {
        "articleCount": raw.get("articles_analyzed", 0),
        "positiveRatio": raw.get("positive_ratio", 0),
        "neutralRatio": raw.get("neutral_ratio", 0),
        "negativeRatio": raw.get("negative_ratio", 0),
        "score": raw.get("final_sentiment_score", 0.5),
        "interpretation": raw.get("interpretation", "")
    }
