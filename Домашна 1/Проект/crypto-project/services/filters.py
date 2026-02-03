from datetime import datetime, timedelta
from typing import Optional

import aiohttp
from configuration.config import CC_API_BASE, START_DATE, LAST_DATE
from services.api_client import fetch_json
from data_access import db
from services.historical import download_history_range
from services.snapshots import fetch_and_store_snapshot


async def filter1_has_recent_history(session: aiohttp.ClientSession, symbol: str) -> bool:
    """
    Филтер 1:
    - Провери дали симболот воопшто има свежи историски податоци на API.
    - Ако /histoday врати само нули → skip.
    """
    url = f"{CC_API_BASE}/data/v2/histoday"
    params = {"fsym": symbol, "tsym": "USD", "limit": 2}
    data = await fetch_json(session, url, params)
    if not data or data.get("Response") != "Success":
        return False
    arr = data["Data"]["Data"]
    if not arr:
        return False
    for rec in arr:
        if (rec.get("close") or 0) > 0 or (rec.get("high") or 0) > 0:
            return True
    return False


def filter2_get_missing_from(symbol: str) -> Optional[datetime.date]:
    """
    Филтер 2:
    - Проверува до кој датум имаме историски податоци.
    - Ако нема податоци → враќа None (што значи: full dump).
    - Ако имаме податоци до вчера → враќа None (сме ажурни).
    - Ако ни недостигаат денови → враќа од кој датум треба да почне пополнувањето.
    """

    last_date_str = db.get_last_historical_date(symbol)

    # Нема историски податоци за симболот → None = преземи 10 години
    if not last_date_str:
        return START_DATE

    last_date = datetime.fromisoformat(last_date_str).date()

    # Ако имаме податоци до вчера → нема недостигачки податоци
    if last_date >= LAST_DATE:
        return None

    # Недостигаат денови: (last_date+1) ... вчера
    missing_from = last_date + timedelta(days=1)
    return missing_from

async def filter3_fill_missing_and_snapshot(session, symbol: str, missing_from):
    """
    Филтер 3:
    - Ако missing_from е None → нема историски за преземање → само snapshot
    - Ако missing_from постои → преземи ги деновите missing_from ... yesterday
    """

    # 1) Нема недостиг → само snapshot
    if missing_from is None:
        print(f"[{symbol}] no missing history – only snapshot")
        await fetch_and_store_snapshot(session, symbol)
        return

    # 2) Има недостиг → симни опсег
    print(f"[{symbol}] downloading history from {missing_from} to {LAST_DATE}")
    await download_history_range(session, symbol, missing_from)

    # 3) После пополнување → snapshot за денес
    await fetch_and_store_snapshot(session, symbol)


