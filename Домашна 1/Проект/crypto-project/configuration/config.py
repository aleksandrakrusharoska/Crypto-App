from datetime import datetime, timezone, timedelta, date

CC_API_BASE = "https://min-api.cryptocompare.com"

CC_API_KEYS = [
    "ac9e71a1b85ad060f6c955757307df9e4a746242f6d550bc49c52ec06e31dcfe",
    "7507e2bd7d57ed65b042304cae611505b155c420f4a2ce3b44397704da2701df",
    "e2a5a4462713ceb26ce79e59cea6426555ab151327e39dcd257b27a982997ce7"
]

# DB_PATH = "../database/crypto_data.db"
SQLITE_PATH = r"C:\Users\User\Downloads\crypto-app-main\crypto-app-main\Homework1\crypto-project\database\crypto_data.db"

PG_HOST = "localhost"
PG_PORT = 5432
PG_DB = "crypto_app"
PG_USER = "postgres"
PG_PASSWORD = "aleks123"

START_DATE = date(2010, 1, 1)
LAST_DATE = (datetime.now(tz=timezone.utc).date() - timedelta(days=1))

BATCH_SIZE = 50
DAYS_PER_CHUNK = 1800
REQUEST_DELAY = 1.0
MAX_PAGES = 15
PAGE_LIMIT = 100
BATCH_SLEEP = 4
RETRY_COUNT = 3
RETRY_SLEEP = 1.5
