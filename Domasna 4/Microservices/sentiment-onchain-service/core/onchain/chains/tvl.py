import requests

LLAMA_TIMEOUT = 8
COINGECKO_TIMEOUT = 8


def get_tvl(chain: str):
    """
    Attempts to fetch chain-level TVL from DefiLlama.
    If unavailable, falls back to CoinGecko DeFi market indicators.
    """

    try:
        r = requests.get(
            f"https://api.llama.fi/tvl/{chain}",
            timeout=LLAMA_TIMEOUT
        )

        if r.status_code == 200 and r.text:
            return {
                "tvl": r.json(),
                "source": "DefiLlama"
            }

    except Exception:
        pass

    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/global/decentralized_finance_defi",
            timeout=COINGECKO_TIMEOUT
        )

        if r.status_code != 200 or not r.text:
            raise ValueError("Bad response from CoinGecko")

        data = r.json().get("data", {})

        return {
            "defiMarketCap": data.get("defi_market_cap"),
            "defiVolume24h": data.get("defi_volume_24h"),
            "defiDominance": data.get("defi_dominance"),
            "source": "CoinGecko (DeFi proxy)"
        }

    except Exception as e:
        return {
            "error": str(e),
            "source": "TVL unavailable"
        }
