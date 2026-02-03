import asyncio
import time
import aiohttp

from data_access import db
from configuration.config import *
from services.api_client import fetch_json
from services.filters import (
    filter1_has_recent_history,
    filter2_get_missing_from,
    filter3_fill_missing_and_snapshot,
)


async def fetch_top_coins_paged(session: aiohttp.ClientSession, max_coins=1500):
    all_coins = []

    for page in range(MAX_PAGES):
        if len(all_coins) >= max_coins:
            break

        url = f"{CC_API_BASE}/data/top/mktcapfull"
        params = {"tsym": "USD", "limit": 100, "page": page}
        data = await fetch_json(session, url, params)

        if not data or data.get("Response") == "Error":
            break

        page_data = data.get("Data", [])
        if not page_data:
            break

        all_coins.extend(page_data)

        print(f"Loaded page {page}, {len(page_data)} coins (total = {len(all_coins)})")

        await asyncio.sleep(0.6)

    print(f"Fetched {len(all_coins)} raw coins.")
    return all_coins


async def pick_exactly_1000_symbols(session, all_symbols):
    valid_symbols = []

    for sym in all_symbols:
        ok = await filter1_has_recent_history(session, sym)
        if ok:
            valid_symbols.append(sym)
        if len(valid_symbols) == 1000:
            break

        await asyncio.sleep(0.2)

    return valid_symbols


async def main():
    start_time = time.time()
    db.init_db()

    existing_symbols = db.get_all_coin_symbols()

    async with aiohttp.ClientSession() as session:
        if existing_symbols:
            print(f"Found {len(existing_symbols)} symbols in coins table.")
            print("Skipping API fetch and Filter1, using symbols from DB.")
            valid_symbols = existing_symbols

        else:
            print("No symbols in coins table. Fetching from API and running Filter1...")
            raw_coins = await fetch_top_coins_paged(session)

            symbol_fullname_map = {}
            all_symbols = []

            for c in raw_coins:
                info = c.get("CoinInfo", {})
                symbol = info.get("Name")
                fullname = info.get("FullName")

                if (
                        not symbol
                        or len(symbol) < 2
                        or not symbol.isalnum()
                        or symbol == "00"
                        or not fullname
                ):
                    continue

                symbol_fullname_map[symbol] = fullname
                all_symbols.append(symbol)

            print(f"Collected {len(all_symbols)} raw symbols from API.")
            print("Running Filter1...")

            # После Filter1 сакаме точно 1000 симболи
            valid_symbols = await pick_exactly_1000_symbols(session, all_symbols)
            print(f"Selected {len(valid_symbols)} valid symbols after Filter1.")

            final_symbol_map = {sym: symbol_fullname_map[sym] for sym in valid_symbols}

            print("Saving 1000 valid symbols into coins table...")
            db.insert_coins(final_symbol_map)

        # Filter2 + Filter3 за секое од 1000
        total = len(valid_symbols)
        for i, sym in enumerate(valid_symbols, start=1):
            print(f"[{i}/{total}] processing {sym}")

            missing_from = filter2_get_missing_from(sym)
            await filter3_fill_missing_and_snapshot(session, sym, missing_from)

            await asyncio.sleep(0.2)

    end_time = time.time()
    mins = int((end_time - start_time) // 60)
    secs = (end_time - start_time) % 60
    print(f"Run finished in {mins}m {secs:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
