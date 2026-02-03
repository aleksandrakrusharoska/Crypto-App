import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")


def now():
    return datetime.now(timezone.utc).isoformat()


def get_eth_gas():
    """
    Fetches the current Ethereum gas price using the Alchemy JSON-RPC API.
    """

    try:
        if not ALCHEMY_API_KEY:
            raise ValueError("Missing ALCHEMY_API_KEY")

        payload = {
            "jsonrpc": "2.0",
            "method": "eth_gasPrice",
            "params": [],
            "id": 1
        }

        resp = requests.post(
            f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}",
            json=payload,
            timeout=10
        )

        if resp.status_code != 200:
            raise ValueError(f"Alchemy bad response ({resp.status_code})")

        data = resp.json()

        gas_price_wei = int(data["result"], 16)
        gas_price_gwei = round(gas_price_wei / 1e9, 2)

        return {
            "gasPrice": gas_price_gwei,
            "unit": "gwei",
            "timestamp": now(),
            "source": "Alchemy"
        }

    except Exception as e:
        return {
            "error": str(e),
            "timestamp": now(),
            "source": "Alchemy"
        }
