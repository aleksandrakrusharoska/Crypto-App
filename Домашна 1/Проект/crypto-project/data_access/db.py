import psycopg2

from typing import List, Optional, Tuple
from configuration.config import *


def get_conn():
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
    )
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
            CREATE TABLE IF NOT EXISTS coins (
                symbol    TEXT PRIMARY KEY,
                full_name TEXT
            )
        """)

    cur.execute("""
            CREATE TABLE IF NOT EXISTS historical_data (
                id          BIGSERIAL PRIMARY KEY,
                symbol      TEXT NOT NULL,
                date        DATE NOT NULL,
                close       DOUBLE PRECISION,
                high        DOUBLE PRECISION,
                low         DOUBLE PRECISION,
                open        DOUBLE PRECISION,
                volume_from DOUBLE PRECISION,
                volume_to   DOUBLE PRECISION,
                CONSTRAINT historical_symbol_date_unique UNIQUE (symbol, date),
                CONSTRAINT historical_symbol_fk FOREIGN KEY (symbol)
                    REFERENCES coins(symbol)
                    ON UPDATE CASCADE
                    ON DELETE CASCADE
            )
        """)

    cur.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id             BIGSERIAL PRIMARY KEY,
                symbol         TEXT NOT NULL,
                date           DATE NOT NULL,
                last_price     DOUBLE PRECISION,
                open_24h       DOUBLE PRECISION,
                high_24h       DOUBLE PRECISION,
                low_24h        DOUBLE PRECISION,
                volume_24h     DOUBLE PRECISION,
                volume_24h_to  DOUBLE PRECISION,
                change_pct_24h DOUBLE PRECISION,
                market_cap     DOUBLE PRECISION,
                supply         DOUBLE PRECISION,
                CONSTRAINT snapshots_symbol_date_unique UNIQUE (symbol, date),
                CONSTRAINT snapshots_symbol_fk FOREIGN KEY (symbol)
                    REFERENCES coins(symbol)
                    ON UPDATE CASCADE
                    ON DELETE CASCADE
            )
        """)

    conn.commit()
    conn.close()


def insert_coins(symbol_fullname_map: dict):
    conn = get_conn()
    cur = conn.cursor()

    for symbol, fullname in symbol_fullname_map.items():
        cur.execute("""
            INSERT INTO coins(symbol, full_name)
            VALUES (%s, %s)
            ON CONFLICT (symbol) DO NOTHING
        """, (symbol, fullname))

    conn.commit()
    conn.close()


def snapshot_exists_today(symbol: str) -> bool:
    today = datetime.now(tz=timezone.utc).date().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
                SELECT 1
                FROM snapshots
                WHERE symbol = %s
                  AND date = %s
                LIMIT 1
                """, (symbol, today))
    row = cur.fetchone()
    conn.close()
    return row is not None


def save_snapshot_row(symbol: str, date_str: str, row: Tuple):
    (last_price, open_24h, high_24h, low_24h,
     volume_24h, volume_24h_to, change_pct_24h,
     market_cap, supply) = row

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO snapshots
        (symbol, date, last_price, open_24h, high_24h, low_24h,
         volume_24h, volume_24h_to, change_pct_24h, market_cap, supply)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol, date) DO UPDATE
        SET last_price     = EXCLUDED.last_price,
            open_24h       = EXCLUDED.open_24h,
            high_24h       = EXCLUDED.high_24h,
            low_24h        = EXCLUDED.low_24h,
            volume_24h     = EXCLUDED.volume_24h,
            volume_24h_to  = EXCLUDED.volume_24h_to,
            change_pct_24h = EXCLUDED.change_pct_24h,
            market_cap     = EXCLUDED.market_cap,
            supply         = EXCLUDED.supply
    """, (
        symbol, date_str,
        last_price, open_24h, high_24h, low_24h,
        volume_24h, volume_24h_to, change_pct_24h, market_cap, supply
    ))
    conn.commit()
    conn.close()


def insert_histoday(symbol: str, data: List[dict]) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cutoff = date(2015, 1, 1)
    today = datetime.now(tz=timezone.utc).date()
    inserted = 0
    for item in data:
        dt = datetime.fromtimestamp(item["time"], tz=timezone.utc).date()
        if dt == today:
            continue
        if dt < cutoff:
            continue
        if all((item.get(k) or 0) == 0 for k in ["open", "high", "low", "close"]):
            continue
        d = dt.isoformat()
        cur.execute("""
            INSERT INTO historical_data
            (symbol, date, close, high, low, open, volume_from, volume_to)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol, date) DO UPDATE
            SET close       = EXCLUDED.close,
                high        = EXCLUDED.high,
                low         = EXCLUDED.low,
                open        = EXCLUDED.open,
                volume_from = EXCLUDED.volume_from,
                volume_to   = EXCLUDED.volume_to
        """, (
            symbol, d,
            item.get("close"),
            item.get("high"),
            item.get("low"),
            item.get("open"),
            item.get("volumefrom"),
            item.get("volumeto"),
        ))
        inserted += 1
    conn.commit()
    conn.close()
    return inserted


def get_last_historical_date(symbol: str) -> Optional[date]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT date
        FROM historical_data
        WHERE symbol = %s
        ORDER BY date DESC
        LIMIT 1
    """, (symbol,))
    row = cur.fetchone()
    conn.close()

    return row[0] if row else None


def get_all_coin_symbols() -> List[str]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT symbol
        FROM coins
        ORDER BY symbol
    """)
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]
    