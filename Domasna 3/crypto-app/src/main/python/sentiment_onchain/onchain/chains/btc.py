import requests
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def get_btc_metrics():
    return {
        "hashRate": float(requests.get(
            "https://blockchain.info/q/hashrate").text) / 1e18,
        "difficulty": float(requests.get(
            "https://blockchain.info/q/getdifficulty").text),
        "timestamp": now(),
        "source": "blockchain.info"
    }
