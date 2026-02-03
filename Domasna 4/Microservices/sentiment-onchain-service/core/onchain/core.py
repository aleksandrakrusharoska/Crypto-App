import requests
from datetime import datetime, timezone

CG_URL = "https://api.coingecko.com/api/v3/coins/markets"

COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "SOL": "solana",
    "AVAX": "avalanche-2"
}


def now():
    return datetime.now(timezone.utc).isoformat()


def get_core_metrics(symbol: str):
    """
    Fetches core market metrics for a given crypto symbol from CoinGecko.
    """

    cg_id = COINGECKO_IDS.get(symbol.upper())
    if not cg_id:
        return None

    r = requests.get(
        CG_URL,
        params={
            "vs_currency": "usd",
            "ids": cg_id
        },
        timeout=15
    )
    r.raise_for_status()

    data = r.json()
    if not data:
        return None

    c = data[0]

    market_cap = c.get("market_cap")
    volume = c.get("total_volume")
    price_change = c.get("price_change_percentage_24h")

    nvt = None
    if market_cap is not None and volume is not None and volume > 0:
        nvt = round(market_cap / volume, 2)

    return {
        "marketCap": market_cap,
        "volume24h": volume,
        "priceChange24h": price_change,
        "nvt": nvt,
        "timestamp": now(),
        "source": "CoinGecko"
    }
