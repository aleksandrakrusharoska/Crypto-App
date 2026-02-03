from sentiment_onchain.onchain.core import get_core_metrics
from sentiment_onchain.onchain.registry import CHAIN_REGISTRY
from sentiment_onchain.onchain.chains import btc, solana, tvl
from sentiment_onchain.onchain.chains.evm import get_eth_gas_alchemy


def analyze_onchain(symbol: str):
    symbol = symbol.upper()

    # --- CORE (safe) ---
    try:
        core = get_core_metrics(symbol)
    except Exception as e:
        core = {
            "error": str(e),
            "source": "core"
        }

    # --- CHAIN SPECIFIC ---
    chain_specific = None
    info = CHAIN_REGISTRY.get(symbol)

    if info:
        try:
            if info["type"] == "BTC":
                chain_specific = btc.get_btc_metrics()

            elif info["type"] == "SOL":
                chain_specific = solana.get_solana_metrics()

            elif info["type"] == "EVM":
                chain_specific = {
                    "tvl": tvl.get_tvl(info["tvl"])
                }

                if symbol == "ETH":
                    chain_specific["gas"] = get_eth_gas_alchemy()

        except Exception as e:
            chain_specific = {
                "error": str(e),
                "source": "chainSpecific"
            }

    # --- ALWAYS RETURN ---
    return {
        "core": core,
        "chainSpecific": chain_specific
    }
