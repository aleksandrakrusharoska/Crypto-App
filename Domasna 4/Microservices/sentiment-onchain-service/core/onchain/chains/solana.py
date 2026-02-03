import requests
from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc).isoformat()


def get_solana_metrics():
    """
    Fetches basic Solana network performance metrics using Solana RPC.
    """

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getRecentPerformanceSamples",
        "params": [1]
    }
    r = requests.post("https://api.mainnet-beta.solana.com", json=payload)
    tps = r.json()["result"][0]["numTransactions"]

    return {
        "tps": tps,
        "timestamp": now(),
        "source": "Solana RPC"
    }
