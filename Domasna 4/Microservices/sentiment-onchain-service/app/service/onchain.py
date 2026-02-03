from core.onchain.dispatcher import analyze_onchain as core_analyze_onchain


def analyze_onchain(symbol: str) -> dict:
    return core_analyze_onchain(symbol)


def calculate_onchain_score(onchain: dict | None) -> float:
    if not onchain or "error" in onchain:
        return 0.5

    core = onchain.get("core", {})
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
