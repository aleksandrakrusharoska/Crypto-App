from datetime import datetime, timezone
import aiohttp
from configuration.config import CC_API_BASE
from services.api_client import fetch_json
from data_access import db


async def fetch_and_store_snapshot(session: aiohttp.ClientSession, symbol: str):
    today = datetime.now(tz=timezone.utc).date().isoformat()

    # 0) Ако веќе имаме snapshot за денес → не правиме ништо
    if db.snapshot_exists_today(symbol):
        print(f"[{symbol}] snapshot already exists for {today}")
        return

    # 1) Пробај денешни податоци од API
    url = f"{CC_API_BASE}/data/pricemultifull"
    params = {"fsyms": symbol, "tsyms": "USD"}
    data = await fetch_json(session, url, params)

    raw = None
    if data:
        try:
            raw = data["RAW"][symbol]["USD"]
        except Exception:
            raw = None

    # 2) Ако нема податоци од API → можеш или да се откажеш, или fallback
    if raw is None:
        print(f"[{symbol}] snapshot not available from API for {today}")
        return

    # 3) Ако има податоци → подготви tuple и запиши со save_snapshot_row
    row = (
        raw.get("PRICE"),
        raw.get("OPEN24HOUR"),
        raw.get("HIGH24HOUR"),
        raw.get("LOW24HOUR"),
        raw.get("VOLUME24HOUR"),
        raw.get("VOLUME24HOURTO"),
        raw.get("CHANGEPCT24HOUR"),
        raw.get("MKTCAP"),
        raw.get("SUPPLY"),
    )

    db.save_snapshot_row(symbol, today, row)
    print(f"[{symbol}] snapshot saved for {today}")
