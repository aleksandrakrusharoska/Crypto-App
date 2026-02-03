import os
import random
from math import sqrt
from typing import Dict

import numpy as np
import pandas as pd
import psycopg2
import tensorflow as tf
from dotenv import load_dotenv
from keras import regularizers
from keras.callbacks import EarlyStopping, ReduceLROnPlateau
from keras.layers import LSTM, Dense, Dropout
from keras.models import Sequential
from keras.optimizers import Adam
from sklearn.metrics import (
    mean_squared_error,
    r2_score,
    mean_absolute_percentage_error
)
from sklearn.preprocessing import MinMaxScaler

# Configuration
load_dotenv()

PG_HOST = os.getenv("PG_HOST")
PG_PORT = int(os.getenv("PG_PORT"))
PG_DB = os.getenv("PG_DB")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_SSLMODE = os.getenv("PG_SSLMODE", "require")

DEFAULT_LOOKBACK = 21
EPOCHS = 5
BATCH_SIZE = 16
SEED_VALUE = 42
MIN_LSTM_LENGTH = 120

np.random.seed(SEED_VALUE)
tf.random.set_seed(SEED_VALUE)
random.seed(SEED_VALUE)
os.environ["TF_DETERMINISTIC_OPS"] = "1"


# Database access
def get_conn():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
        sslmode=PG_SSLMODE
    )


def load_history(symbol: str) -> pd.DataFrame:
    query = """
        SELECT date, close
        FROM historical_data
        WHERE symbol = %s
          AND date >= CURRENT_DATE - interval '5 years'
        ORDER BY date ASC
    """
    with get_conn() as conn:
        return pd.read_sql(query, conn, params=(symbol,))


# Helper functions
def should_use_log(df: pd.DataFrame) -> bool:
    """
    Determines whether log-scaling should be applied based on
    price distribution and volatility.
    """
    mean_price = df["close"].mean()
    max_price = df["close"].max()
    std_price = df["close"].std()

    if mean_price < 1.0:
        return True
    if max_price > 5 * mean_price:
        return True
    if std_price / mean_price > 0.4:
        return True
    return False


def choose_lookback(n_rows: int, use_log: bool) -> int:
    if n_rows < 120:
        return 5
    elif n_rows < 250:
        return 9
    return 30 if use_log else DEFAULT_LOOKBACK


def make_sequences(data: np.ndarray, lookback: int):
    X, y = [], []
    for i in range(lookback, len(data)):
        X.append(data[i - lookback:i])
        y.append(data[i])
    return np.array(X), np.array(y)


def split_data(X, y):
    train_size = int(len(X) * 0.7)
    val_size = int(len(X) * 0.15)

    return (
        X[:train_size],
        y[:train_size],
        X[train_size:train_size + val_size],
        y[train_size:train_size + val_size],
        X[train_size + val_size:],
        y[train_size + val_size:]
    )


def build_model(input_shape):
    model = Sequential([
        LSTM(
            32,
            return_sequences=True,
            activation="relu",
            kernel_initializer="he_normal",
            kernel_regularizer=regularizers.l2(1e-4),
            input_shape=input_shape
        ),
        Dropout(0.15),
        LSTM(
            16,
            activation="relu",
            kernel_initializer="he_normal",
            kernel_regularizer=regularizers.l2(1e-4)
        ),
        Dense(1)
    ])

    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss="mse",
        metrics=["mae"]
    )
    return model


def calculate_metrics(y_true, y_pred):
    rmse = sqrt(mean_squared_error(y_true, y_pred))
    mae = float(np.mean(np.abs(y_true - y_pred)))

    if np.mean(y_true) < 0.05 or len(y_true) < 30:
        return rmse, mae, None, None

    mape = float(mean_absolute_percentage_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    return rmse, mae, mape, r2


# Main service entry point
def train_lstm_for_symbol(symbol: str) -> Dict:
    """
    End-to-end LSTM workflow:
    data loading, preprocessing, training and evaluation.
    Returns next-day price prediction on demand.
    """
    df = load_history(symbol)

    if df.empty or len(df) < MIN_LSTM_LENGTH:
        raise ValueError(
            f"Not enough data for {symbol}. "
            f"Required {MIN_LSTM_LENGTH}, got {len(df)}"
        )

    use_log = should_use_log(df)
    lookback = choose_lookback(len(df), use_log)

    closes_raw = df["close"].values.astype(float)
    closes = np.log1p(closes_raw) if use_log else closes_raw

    X_raw, y_raw = make_sequences(closes, lookback)
    X_train, y_train, X_val, y_val, X_test, y_test = split_data(X_raw, y_raw)

    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()

    X_train_s = scaler_X.fit_transform(X_train)
    X_val_s = scaler_X.transform(X_val)
    X_test_s = scaler_X.transform(X_test)

    y_train_s = scaler_y.fit_transform(y_train.reshape(-1, 1))
    y_val_s = scaler_y.transform(y_val.reshape(-1, 1))
    y_test_s = scaler_y.transform(y_test.reshape(-1, 1))

    X_train_l = X_train_s.reshape(-1, lookback, 1)
    X_val_l = X_val_s.reshape(-1, lookback, 1)
    X_test_l = X_test_s.reshape(-1, lookback, 1)

    model = build_model((lookback, 1))

    callbacks = [
        EarlyStopping(patience=10, restore_best_weights=True),
        ReduceLROnPlateau(patience=5, factor=0.5, min_lr=1e-5)
    ]

    model.fit(
        X_train_l,
        y_train_s,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_data=(X_val_l, y_val_s),
        shuffle=False,
        verbose=1,
        callbacks=callbacks
    )

    y_pred_s = model.predict(X_test_l, verbose=0)
    y_pred = scaler_y.inverse_transform(y_pred_s)[:, 0]
    y_test_orig = scaler_y.inverse_transform(y_test_s)[:, 0]

    if use_log:
        y_pred = np.expm1(y_pred)
        y_test_orig = np.expm1(y_test_orig)

    rmse, mae, mape, r2 = calculate_metrics(y_test_orig, y_pred)

    last_window = closes[-lookback:]
    last_window_s = scaler_X.transform(last_window.reshape(1, -1))
    last_window_l = last_window_s.reshape(1, lookback, 1)

    next_pred_s = model.predict(last_window_l, verbose=0)[0][0]
    next_pred = scaler_y.inverse_transform([[next_pred_s]])[0][0]
    next_price = float(np.expm1(next_pred)) if use_log else float(next_pred)

    last_date = pd.to_datetime(df["date"].iloc[-1])
    next_date = last_date + pd.Timedelta(days=1)

    return {
        "symbol": symbol,
        "prediction_date": str(next_date.date()),
        "predicted_close": next_price,
        "rmse": rmse,
        "mae": mae,
        "mape": mape,
        "r2": r2
    }
