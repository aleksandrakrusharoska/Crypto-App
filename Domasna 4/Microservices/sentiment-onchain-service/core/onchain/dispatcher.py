from core.onchain.core import get_core_metrics
from core.onchain.registry import CHAIN_REGISTRY
from core.onchain.chains import btc, solana, tvl
from core.onchain.chains.evm import get_eth_gas


def analyze_onchain(symbol: str):
    """
    Aggregates core and chain-specific on-chain metrics for a given symbol.
    """

    symbol = symbol.upper()

    try:
        core = get_core_metrics(symbol)
    except Exception as e:
        core = {
            "error": str(e),
            "source": "core"
        }

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
                    chain_specific["gas"] = get_eth_gas()

        except Exception as e:
            chain_specific = {
                "error": str(e),
                "source": "chainSpecific"
            }

    return {
        "core": core,
        "chainSpecific": chain_specific
    }
