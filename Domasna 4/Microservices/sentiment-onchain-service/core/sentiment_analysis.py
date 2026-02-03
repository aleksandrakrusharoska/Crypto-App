import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import numpy as np
import requests
import torch
from cachetools import TTLCache
from dotenv import load_dotenv
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SentimentConfig:
    NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
    BERT_MODEL = "ProsusAI/finbert"
    CACHE_TTL = 300
    REQUEST_TIMEOUT = 15


sentiment_cache = TTLCache(maxsize=500, ttl=SentimentConfig.CACHE_TTL)


class FinBERTSentimentAnalyzer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        try:
            logger.info("Вчитување на FinBERT модел")
            self.tokenizer = AutoTokenizer.from_pretrained(SentimentConfig.BERT_MODEL)
            self.model = AutoModelForSequenceClassification.from_pretrained(SentimentConfig.BERT_MODEL)
            self.pipeline = pipeline(
                task="text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            self._initialized = True
            logger.info("FinBERT модел успешно вчитан")

            device_info = "GPU (CUDA)" if torch.cuda.is_available() else "CPU"
            logger.info(f"Користи: {device_info}")
        except Exception as e:
            logger.error(f"Неможе да се вчита FinBERT: {e}")
            self.pipeline = None
            self._initialized = True

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyzes sentiment of a single news headline using FinBERT.
        """

        if not self.pipeline:
            logger.warning("FinBERT не е достапен, враќа NEUTRAL")
            return {
                "label": "NEUTRAL",
                "score": 0.5,
                "confidence": 0.0
            }

        try:
            text_truncated = text[:512]

            result = self.pipeline(text_truncated)[0]

            # FinBERT outputs "positive", "negative", "neutral"
            label_mapping = {
                "positive": "POSITIVE",
                "negative": "NEGATIVE",
                "neutral": "NEUTRAL"
            }

            label = label_mapping.get(result["label"].lower(), "NEUTRAL")
            score = float(result["score"])

            return {
                "label": label,
                "score": score,
                "confidence": score
            }
        except Exception as e:
            logger.error(f"Sentiment анализа неуспешна: {e}")
            return {
                "label": "NEUTRAL",
                "score": 0.5,
                "confidence": 0.0
            }


# Singleton instance to avoid reloading the FinBERT model on each request
finbert_analyzer = FinBERTSentimentAnalyzer()


def fetch_news_articles(symbol: str, days: int = 30, max_articles: int = 100) -> Optional[list]:
    """
    Fetches recent news articles for a given crypto symbol using NewsAPI.
    """

    if not SentimentConfig.NEWSAPI_KEY:
        logger.warning("NEWSAPI_KEY не е поставен")
        return []

    try:
        end = datetime.utcnow()
        start = end - timedelta(days=days)

        params = {
            "q": symbol,
            "from": start.date().isoformat(),
            "to": end.date().isoformat(),
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": max_articles,
            "apiKey": SentimentConfig.NEWSAPI_KEY
        }

        logger.info(f"Превземање вести за {symbol}")
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params=params,
            timeout=SentimentConfig.REQUEST_TIMEOUT
        )
        r.raise_for_status()

        data = r.json()
        articles = data.get("articles", [])
        logger.info(f"Превземени {len(articles)} вести за {symbol}")

        return articles
    except Exception as e:
        logger.error(f"Грешка при превземање вести: {e}")
        return []


def analyze_sentiment_for_symbol(symbol: str, days: int = 30, max_articles: int = 100) -> Dict[str, Any]:
    """
    End-to-end sentiment analysis pipeline:
    fetches news, applies FinBERT, aggregates scores and returns interpretation.
    """

    cache_key = f"sentiment:{symbol}:{days}"

    if cache_key in sentiment_cache:
        logger.info(f"Sentiment за {symbol} е од кеш")
        return sentiment_cache[cache_key]

    articles = fetch_news_articles(symbol, days, max_articles)

    if not articles:
        logger.warning(f"Нема вести за {symbol}")
        return _default_sentiment(symbol)

    sentiments = []

    logger.info(f"Анализирање sentiment за {len(articles)} вести")
    for i, article in enumerate(articles):
        title = article.get("title", "").strip()

        if not title:
            continue

        sentiment = finbert_analyzer.analyze_text(title)

        sentiments.append({
            "title": title,
            "sentiment": sentiment["label"],
            "score": sentiment["score"],
            "source": article.get("source", {}).get("name", "Unknown"),
            "publishedAt": article.get("publishedAt")
        })

        if (i + 1) % 10 == 0:
            logger.info(f"Анализирани {i + 1}/{len(articles)}")

    if not sentiments:
        return _default_sentiment(symbol)

    positive_count = sum(1 for s in sentiments if s["sentiment"] == "POSITIVE")
    negative_count = sum(1 for s in sentiments if s["sentiment"] == "NEGATIVE")
    neutral_count = sum(1 for s in sentiments if s["sentiment"] == "NEUTRAL")

    total = len(sentiments)
    positive_ratio = positive_count / total
    negative_ratio = negative_count / total
    neutral_ratio = neutral_count / total

    average_score = float(np.mean([s["score"] for s in sentiments]))

    # Weighted sentiment score:
    # POSITIVE = +0.5, NEGATIVE = -0.5, NEUTRAL = 0
    weights = []
    for s in sentiments:
        if s["sentiment"] == "POSITIVE":
            weights.append(0.5 * s["score"])
        elif s["sentiment"] == "NEGATIVE":
            weights.append(-0.5 * s["score"])
        else:
            weights.append(0.0)

    final_sentiment_score = float(np.mean(weights)) + 0.5

    if positive_ratio >= 0.6:
        interpretation = "⭐⭐ Силно позитивно - Вестите се многу позитивни"

    elif positive_ratio >= 0.5:
        interpretation = "⭐ Позитивно - Вестите се позитивни"

    elif neutral_ratio >= 0.5:
        interpretation = "⚪ Неутрално - Вестите се претежно неутрални"

    elif negative_ratio >= 0.4:
        interpretation = "👎 Негативно - Вестите се негативни"

    else:
        interpretation = "👎👎 Силно негативно - Вестите се многу негативни"

    result = {
        "symbol": symbol.upper(),
        "timestamp": datetime.utcnow().isoformat(),
        "articles_analyzed": total,
        "positive_ratio": round(positive_ratio, 3),
        "negative_ratio": round(negative_ratio, 3),
        "neutral_ratio": round(neutral_ratio, 3),
        "average_score": round(average_score, 3),
        "final_sentiment_score": round(final_sentiment_score, 3),
        "samples": sentiments[:5],
        "interpretation": interpretation
    }

    sentiment_cache[cache_key] = result
    logger.info(f"Sentiment анализа завршена за {symbol}")

    return result


def _default_sentiment(symbol: str) -> Dict[str, Any]:
    """Fallback sentiment when no news is available."""

    return {
        "symbol": symbol.upper(),
        "timestamp": datetime.utcnow().isoformat(),
        "articles_analyzed": 0,
        "positive_ratio": 0.5,
        "negative_ratio": 0.5,
        "neutral_ratio": 0.0,
        "average_score": 0.5,
        "final_sentiment_score": 0.5,
        "samples": [],
        "interpretation": "⚠️ НЕДОСТАПНИ ВЕСТИ - Нема доволно информации"
    }


def setup_sentiment_logging():
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - sentiment - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


if __name__ == "__main__":
    setup_sentiment_logging()

    print("\n" + "=" * 70)
    print("🔍 SENTIMENT АНАЛИЗА - ТЕСТ")
    print("=" * 70)

    result = analyze_sentiment_for_symbol("BTC")
    print(json.dumps(result, indent=2, default=str))

    print("\n" + "=" * 70)

    result = analyze_sentiment_for_symbol("ETH")
    print(json.dumps(result, indent=2, default=str))
