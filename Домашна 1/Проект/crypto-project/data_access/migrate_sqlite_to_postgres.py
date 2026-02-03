import sqlite3
import psycopg2

from configuration.config import *


def get_sqlite_conn():
    return sqlite3.connect(SQLITE_PATH)


def get_pg_conn():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
    )


def migrate_coins():
    sqlite_conn = get_sqlite_conn()
    pg_conn = get_pg_conn()

    s_cur = sqlite_conn.cursor()
    p_cur = pg_conn.cursor()

    print("Migrating coins...")

    s_cur.execute("SELECT symbol, full_name FROM coins")
    rows = s_cur.fetchall()

    for symbol, full_name in rows:
        p_cur.execute("""
            INSERT INTO coins(symbol, full_name)
            VALUES (%s, %s)
            ON CONFLICT (symbol) DO NOTHING
        """, (symbol, full_name))

    pg_conn.commit()
    sqlite_conn.close()
    pg_conn.close()

    print(f"Done. Migrated {len(rows)} rows into coins.")


def migrate_historical_data():
    sqlite_conn = get_sqlite_conn()
    pg_conn = get_pg_conn()

    s_cur = sqlite_conn.cursor()
    p_cur = pg_conn.cursor()

    print("Migrating historical_data...")

    # Го игнорираме id и ги внесуваме останатите колони
    s_cur.execute("""
        SELECT symbol, date, close, high, low, open, volume_from, volume_to
        FROM historical_data
    """)
    rows = s_cur.fetchall()

    count = 0
    for row in rows:
        (symbol, date_str, close, high, low, open_price, volume_from, volume_to) = row

        p_cur.execute("""
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
            symbol, date_str, close, high, low, open_price, volume_from, volume_to
        ))
        count += 1

    pg_conn.commit()
    sqlite_conn.close()
    pg_conn.close()

    print(f"Done. Migrated {count} rows into historical_data.")


def migrate_snapshots():
    sqlite_conn = get_sqlite_conn()
    pg_conn = get_pg_conn()

    s_cur = sqlite_conn.cursor()
    p_cur = pg_conn.cursor()

    print("Migrating snapshots...")

    s_cur.execute("""
        SELECT symbol, date, last_price, open_24h, high_24h, low_24h,
               volume_24h, volume_24h_to, change_pct_24h, market_cap, supply
        FROM snapshots
    """)
    rows = s_cur.fetchall()

    count = 0
    for row in rows:
        (symbol, date_str, last_price, open_24h, high_24h, low_24h,
         volume_24h, volume_24h_to, change_pct_24h, market_cap, supply) = row

        p_cur.execute("""
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
            symbol, date_str, last_price, open_24h, high_24h, low_24h,
            volume_24h, volume_24h_to, change_pct_24h, market_cap, supply
        ))
        count += 1

    pg_conn.commit()
    sqlite_conn.close()
    pg_conn.close()

    print(f"Done. Migrated {count} rows into snapshots.")


def main():
    print("=== Migration START ===")
    migrate_coins()
    migrate_historical_data()
    migrate_snapshots()
    print("=== Migration DONE ===")


if __name__ == "__main__":
    main()
