import asyncio
import aiohttp
from typing import Optional, Dict, Any
from configuration.config import CC_API_KEYS, RETRY_COUNT, RETRY_SLEEP

_api_key_index = 0


def _next_api_key() -> str:
    global _api_key_index
    key = CC_API_KEYS[_api_key_index]
    _api_key_index = (_api_key_index + 1) % len(CC_API_KEYS)
    return key


async def fetch_json(session: aiohttp.ClientSession, url: str, params: dict) -> Optional[Dict[str, Any]]:
    for attempt in range(RETRY_COUNT):
        headers = {"authorization": f"Apikey {_next_api_key()}"} if CC_API_KEYS else {}
        try:
            async with session.get(url, params=params, headers=headers, timeout=15) as resp:
                return await resp.json()
        except Exception as e:
            print(f"Network error on {url} try {attempt + 1}/{RETRY_COUNT}: {e}")
            await asyncio.sleep(RETRY_SLEEP)
    return None
