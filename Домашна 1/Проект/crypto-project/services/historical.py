from datetime import datetime, timezone
import asyncio
from configuration.config import (
    CC_API_BASE,
    START_DATE,
    DAYS_PER_CHUNK,
    REQUEST_DELAY, LAST_DATE,
)
from services.api_client import fetch_json
from data_access import db


async def fetch_histoday_chunk(session, symbol: str, to_ts: int, limit: int = 2000):
    url = f"{CC_API_BASE}/data/v2/histoday"
    params = {"fsym": symbol, "tsym": "USD", "toTs": to_ts, "limit": limit}
    data = await fetch_json(session, url, params)
    if data and data.get("Response") == "Success":
        return data["Data"]["Data"]
    else:
        print(f"[{symbol}] histoday error or no data")
        return []


async def download_history_range(session, symbol: str, from_date=START_DATE, to_date=LAST_DATE):
    """
    Презема историски дневни податоци за опсег:
    од from_date до to_date (и двата вклучени),
    во повеќе chunk-ови (while loop), без ограничување на 2000 дена.
    """

    target_ts = int(datetime(from_date.year, from_date.month, from_date.day,
                             tzinfo=timezone.utc).timestamp())
    current_ts = int(datetime(to_date.year, to_date.month, to_date.day,
                              tzinfo=timezone.utc).timestamp())

    total_inserted = 0

    while current_ts >= target_ts:
        # колку денови уште има до долната граница
        remaining_days = int((current_ts - target_ts) / 86400) + 1
        limit = min(DAYS_PER_CHUNK, remaining_days)

        # земи едно парче од историјата наназад
        chunk = await fetch_histoday_chunk(session, symbol, current_ts, limit=limit)
        await asyncio.sleep(REQUEST_DELAY)

        if not chunk:
            print(f"[{symbol}] no data in range, stop.")
            break

        # држиме само датуми во бараниот опсег
        filtered = []
        for rec in chunk:
            rec_date = datetime.fromtimestamp(rec["time"], tz=timezone.utc).date()
            if from_date <= rec_date <= to_date:
                filtered.append(rec)

        if not filtered:
            print(f"[{symbol}] got chunk but no dates in requested range, stop.")
            break

        inserted = db.insert_histoday(symbol, filtered)
        total_inserted += inserted

        # најстариот датум во ова парче
        oldest_ts = filtered[0]["time"]   # старо → ново
        oldest_dt = datetime.fromtimestamp(oldest_ts, tz=timezone.utc)
        print(f"[{symbol}] saved {inserted}/{len(filtered)} days from {oldest_dt.date()}")

        # ако стигнавме до долната граница – стоп
        if inserted < limit or oldest_dt.date() <= from_date:
            break

        # оди еден ден наназад од најстариот во ова парче
        current_ts = int(oldest_dt.timestamp()) - 86400

    return total_inserted
