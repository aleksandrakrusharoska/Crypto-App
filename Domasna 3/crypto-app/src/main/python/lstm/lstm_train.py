import os
import sys

from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
import random
import tensorflow as tf

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_percentage_error

from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras import regularizers

from dotenv import load_dotenv

import matplotlib.pyplot as plt

# ============= CONFIG =============
load_dotenv()

PG_HOST = os.getenv("PG_HOST")
PG_PORT = int(os.getenv("PG_PORT"))
PG_DB = os.getenv("PG_DB")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")

DEFAULT_LOOKBACK = 21
EPOCHS = 100
BATCH_SIZE = 8
SEED_VALUE = 42

MIN_LSTM_LENGTH = 120

np.random.seed(SEED_VALUE)
tf.random.set_seed(SEED_VALUE)
random.seed(SEED_VALUE)
os.environ['TF_DETERMINISTIC_OPS'] = '1'

PLOTS_DIR = Path(__file__).parent / "plots"
PLOTS_DIR.mkdir(exist_ok=True)


# ============= DATABASE =============


def get_conn():
    return psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB,
        user=PG_USER, password=PG_PASSWORD
    )


def load_history(symbol: str) -> pd.DataFrame:
    query = """
            SELECT date, close
            FROM historical_data
            WHERE symbol = %s
              AND date >= CURRENT_DATE - interval '5 years'
            ORDER BY date ASC \
            """
    with get_conn() as conn:
        return pd.read_sql(query, conn, params=(symbol,))


def save_prediction(symbol: str, next_date, next_price, rmse, mape, r2):
    sql = """
          INSERT INTO lstm_predictions(symbol, prediction_date, predicted_close, rmse, mape, r2)
          VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (symbol, prediction_date) DO
          UPDATE
              SET predicted_close = EXCLUDED.predicted_close,
              rmse = EXCLUDED.rmse,
              mape = EXCLUDED.mape,
              r2 = EXCLUDED.r2,
              updated_at = NOW() \
          """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (symbol, next_date, next_price, rmse, mape, r2))
        conn.commit()
    print(f"[OK] Saved prediction for {symbol} on {next_date.date()}")


# ============= DATA PROCESSING =============
def choose_lookback(n_rows: int, use_log: bool) -> int:
    if n_rows < 120:
        return 5
    elif n_rows < 250:
        return 9
    else:
        return 30 if use_log else DEFAULT_LOOKBACK


def should_use_log(df: pd.DataFrame) -> bool:
    mean_price = df["close"].mean()
    max_price = df["close"].max()
    std_price = df["close"].std()

    # Евтини монети
    if mean_price < 1.0:
        return True

    # Големи шпикови
    if max_price > 5 * mean_price:
        return True

    # Висока релативна волатилност
    if std_price / mean_price > 0.4:
        return True

    return False


def make_sequences_raw(closes: np.ndarray, lookback: int):
    X, y = [], []
    for i in range(lookback, len(closes)):
        X.append(closes[i - lookback:i])
        y.append(closes[i])
    return np.array(X), np.array(y)


def split_data(X_raw, y_raw):
    train_size = int(len(X_raw) * 0.70)
    val_size = int(len(X_raw) * 0.15)

    X_train = X_raw[:train_size]
    y_train = y_raw[:train_size]
    X_val = X_raw[train_size:train_size + val_size]
    y_val = y_raw[train_size:train_size + val_size]
    X_test = X_raw[train_size + val_size:]
    y_test = y_raw[train_size + val_size:]

    return X_train, y_train, X_val, y_val, X_test, y_test


def scale_data(X_train, X_val, X_test, y_train, y_val, y_test):
    scaler_X = MinMaxScaler()
    X_train_s = scaler_X.fit_transform(X_train)
    X_val_s = scaler_X.transform(X_val)
    X_test_s = scaler_X.transform(X_test)

    scaler_y = MinMaxScaler()
    y_train_s = scaler_y.fit_transform(y_train.reshape(-1, 1))
    y_val_s = scaler_y.transform(y_val.reshape(-1, 1))
    y_test_s = scaler_y.transform(y_test.reshape(-1, 1))

    return X_train_s, X_val_s, X_test_s, y_train_s, y_val_s, y_test_s, scaler_X, scaler_y


def reshape_for_lstm(X_train, X_val, X_test, lookback: int):
    return (
        X_train.reshape(-1, lookback, 1),
        X_val.reshape(-1, lookback, 1),
        X_test.reshape(-1, lookback, 1),
    )


# ============= MODEL =============
def build_model(input_shape):
    l2_reg = 1e-4

    model = Sequential()
    model.add(
        LSTM(
            32,
            return_sequences=True,
            input_shape=input_shape,
            activation='relu',
            kernel_initializer='he_normal',
            kernel_regularizer=regularizers.l2(l2_reg)
        )
    )
    model.add(Dropout(0.15))
    model.add(LSTM(16, activation='relu', kernel_initializer='he_normal', kernel_regularizer=regularizers.l2(l2_reg)))
    model.add(Dense(1, activation='linear'))

    optimizer = Adam(learning_rate=0.001)
    model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
    return model


# ============= VISUALIZATION =============
def plot_loss(history, symbol):
    plt.figure(figsize=(10, 5))
    plt.plot(history.history["loss"], label="train_loss", linewidth=2)
    plt.plot(history.history["val_loss"], label="val_loss", linewidth=2)
    plt.title(f"LSTM Loss - {symbol}")
    plt.xlabel("Epoch")
    plt.ylabel("MSE")
    plt.legend()
    plt.grid(True, alpha=0.3)

    path = PLOTS_DIR / f"{symbol}_loss.png"
    plt.savefig(path, bbox_inches="tight", dpi=100)
    plt.close()
    return str(path)


def plot_predictions(test_dates, y_real, y_pred, symbol):
    plt.figure(figsize=(12, 5))

    plt.plot(test_dates, y_real, label="Real", linewidth=1.2,
             marker='o', markersize=3, alpha=0.9, color="#1f77b4")
    plt.plot(test_dates, y_pred, label="Predicted", linewidth=1.2,
             marker='s', markersize=3, alpha=0.9, color="#ff7f0e")

    plt.title(f"LSTM Prediction - {symbol}", fontsize=14)
    plt.xlabel("Date")
    plt.ylabel("Price")

    ymin = min(y_real.min(), y_pred.min())
    ymax = max(y_real.max(), y_pred.max())
    padding = (ymax - ymin) * 0.1
    plt.ylim(ymin - padding, ymax + padding)

    plt.xticks(rotation=35, fontsize=9)
    plt.yticks(fontsize=9)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.25, linestyle='--')
    plt.tight_layout()

    path = PLOTS_DIR / f"{symbol}_prediction.png"
    plt.savefig(path, bbox_inches="tight", dpi=120)
    plt.close()
    return str(path)


# ============= METRICS =============
def calculate_metrics(y_true, y_pred):
    rmse = sqrt(mean_squared_error(y_true, y_pred))
    mae = float(np.mean(np.abs(y_true - y_pred)))

    # За многу мали цени или премалку примероци, MAPE и R² не се стабилни
    if np.mean(y_true) < 0.05 or len(y_true) < 30:
        mape = None
        r2 = None
    else:
        mape = float(mean_absolute_percentage_error(y_true, y_pred))
        r2 = float(r2_score(y_true, y_pred))
    return rmse, mape, r2, mae


def print_metrics(symbol, rmse, mape, r2, mae):
    print(f"\n\t{symbol} Metrics:")
    print(f"\tRMSE = {rmse:.6f}")
    print(f"\tMAE  = {mae:.6f}")
    if mape is not None:
        print(f"\tMAPE = {mape:.6f}")
    else:
        print("\tMAPE = n/a (price too small or too few test samples)")
    if r2 is not None:
        print(f"\tR²   = {r2:.6f}")
    else:
        print("\tR²   = n/a (not reliable for this test set)")


# ============= TRAINING =============
def train_lstm_for_symbol(symbol: str):
    print(f"\n{'=' * 60}")
    print(f"LSTM Training for {symbol}")
    print(f"{'=' * 60}")

    df = load_history(symbol)

    if df.empty:
        print(f"[WARN] No data for {symbol}")
        return

    if should_use_log(df) and len(df) > 730:
        df = df.tail(730)
        print(f"[INFO] {symbol}: using only the last 730 days of history")

    n_rows = len(df)
    print("\n--- Data Statistics ---")
    print(df["close"].describe())
    print("-------------------------")

    # Not enough data → no training, no prediction
    if n_rows < MIN_LSTM_LENGTH:
        print(f"\n[INFO] {symbol}: Not enough data for prediction.")
        print(f"Required minimum: {MIN_LSTM_LENGTH}, available: {n_rows}")
        print("STATUS:NOT_ENOUGH_DATA")
        return

    use_log = should_use_log(df)

    # Динамичен lookback
    lookback = choose_lookback(n_rows, use_log)
    print(f"\n--- Config Selection ---")
    print(f"Data Length: {n_rows}")
    print(f"Lookback: {lookback}")
    print("-------------------------")

    closes_raw = df["close"].values.astype(float)

    if use_log:
        print(f"[INFO] Using log1p transform for {symbol}")
        closes_for_model = np.log1p(closes_raw)
    else:
        print(f"[INFO] Using RAW prices (no log) for {symbol}")
        closes_for_model = closes_raw

    # 1. Create sequences
    X_raw, y_raw = make_sequences_raw(closes_for_model, lookback)

    # 2. Split data
    X_train, y_train, X_val, y_val, X_test, y_test = split_data(X_raw, y_raw)

    # 3. Scale data
    X_train_s, X_val_s, X_test_s, y_train_s, y_val_s, y_test_s, scaler_X, scaler_y = scale_data(
        X_train, X_val, X_test, y_train, y_val, y_test
    )

    # 4. Reshape for LSTM
    X_train_l, X_val_l, X_test_l = reshape_for_lstm(X_train_s, X_val_s, X_test_s, lookback)

    print(f"\nDataset Sizes:")
    print(f"  Train: {len(X_train_l)}, Val: {len(X_val_l)}, Test: {len(X_test_l)}")
    print(f"  Input shape: {X_train_l.shape}")

    # 5. Build model
    model = build_model((lookback, 1))

    # 6. Train
    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=0)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=0.00001, verbose=0)

    local_batch_size = BATCH_SIZE if n_rows > 500 else 8
    history = model.fit(
        X_train_l, y_train_s,
        epochs=EPOCHS,
        batch_size=local_batch_size,
        validation_data=(X_val_l, y_val_s),
        callbacks=[early_stop, reduce_lr],
        shuffle=False,
        verbose=0
    )

    # 7. Evaluate
    y_pred_s = model.predict(X_test_l, verbose=0)
    y_test_model_space = scaler_y.inverse_transform(y_test_s)[:, 0]
    y_pred_model_space = scaler_y.inverse_transform(y_pred_s)[:, 0]

    if use_log:
        y_test_orig = np.expm1(y_test_model_space)
        y_pred_orig = np.expm1(y_pred_model_space)
    else:
        y_test_orig = y_test_model_space
        y_pred_orig = y_pred_model_space

    rmse, mape, r2, mae = calculate_metrics(y_test_orig, y_pred_orig)
    print_metrics(symbol, rmse, mape, r2, mae)

    # 8. Plot loss
    plot_loss(history, symbol)
    print(f"[OK] Saved loss plot")

    # 9. Plot predictions
    start_idx = lookback + int(len(X_raw) * 0.70) + int(len(X_raw) * 0.15)
    test_dates = df["date"].iloc[start_idx:start_idx + len(y_test_orig)]

    plot_predictions(test_dates, y_test_orig, y_pred_orig, symbol)
    print(f"[OK] Saved prediction plot")

    # 10. Next-day prediction
    last_window_model = closes_for_model[-lookback:]
    last_window_s = scaler_X.transform(last_window_model.reshape(1, -1)).reshape(1, lookback, 1)

    next_pred_model_s = model.predict(last_window_s, verbose=0)[0][0]
    next_pred_model = scaler_y.inverse_transform([[next_pred_model_s]])[0][0]

    if use_log:
        next_price = float(np.expm1(next_pred_model))
    else:
        next_price = float(next_pred_model)

    last_date = df["date"].iloc[-1]
    if not isinstance(last_date, pd.Timestamp):
        last_date = pd.Timestamp(last_date)
    next_date = last_date + pd.Timedelta(days=1)

    print(f"\nPrediction:")
    print(f"  Last close ({last_date.date()}): {closes_raw[-1]:.6f}")
    print(f"  Next close ({next_date.date()}): {next_price:.6f}")

    print(f"DATE:{next_date.date()}")
    print(f"PREDICTION:{next_price}")

    # 11. Save to database
    save_prediction(symbol, next_date, next_price, rmse if rmse is not None else None,
                    mape, r2)


# ============= MAIN =============
if __name__ == "__main__":
    if len(sys.argv) > 1:
        symbols = [sys.argv[1]]
    else:
        symbols = ["BTC", "ETH", "NODE", "SLAY", "CORN", "ASD", "USDT", "XRP"]

    for sym in symbols:
        try:
            train_lstm_for_symbol(sym)
        except Exception as e:
            print(f"\n[ERROR] Failed for {sym}: {e}")
            import traceback

            traceback.print_exc()
