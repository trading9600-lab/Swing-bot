import ccxt
import pandas as pd
import requests
import time
from datetime import datetime, timezone

# ===============================
# 🤖 BOT SOURCE
# ===============================
BOT_SOURCE = "GITHUB_ACTIONS"

# ===============================
# 🔐 TELEGRAM CONFIG (AS REQUESTED)
# ===============================
TOKEN = "8364584748:AAFeym3et4zJwmdKRxYtP3ieIKV8FuPWdQ8"
CHAT_ID = "@Tradecocom"

# ===============================
# ⚙️ SETTINGS
# ===============================
PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]

ENTRY_TIMEFRAME = "1h"
TREND_TIMEFRAME = "4h"

EMA_FAST = 20
EMA_SLOW = 50
EMA_TREND = 200

COOLDOWN = 3600  # 1 hour cooldown per signal

# ===============================
# 🔁 EXCHANGE (MEXC – FREE)
# ===============================
exchange = ccxt.mexc({"enableRateLimit": True})

last_signal = {}

# ===============================
# 📢 TELEGRAM ALERT
# ===============================
def send_alert(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ===============================
# 📊 FETCH DATA
# ===============================
def get_data(symbol, timeframe, limit=200):
    candles = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    return pd.DataFrame(
        candles,
        columns=["time", "open", "high", "low", "close", "volume"]
    )

# ===============================
# 📈 TREND CHECK (4H EMA 200)
# ===============================
def get_trend(symbol):
    df = get_data(symbol, TREND_TIMEFRAME)
    df["ema200"] = df["close"].ewm(span=EMA_TREND).mean()

    close = df["close"].iloc[-2]      # closed candle
    ema200 = df["ema200"].iloc[-2]

    return "BULL" if close > ema200 else "BEAR"

# ===============================
# 🚀 ENTRY SIGNAL (1H EMA CROSS)
# ===============================
def check_entry(symbol):
    trend = get_trend(symbol)

    df = get_data(symbol, ENTRY_TIMEFRAME)
    df["ema20"] = df["close"].ewm(span=EMA_FAST).mean()
    df["ema50"] = df["close"].ewm(span=EMA_SLOW).mean()

    # CLOSED candles only
    prev_fast = df["ema20"].iloc[-3]
    prev_slow = df["ema50"].iloc[-3]
    curr_fast = df["ema20"].iloc[-2]
    curr_slow = df["ema50"].iloc[-2]

    price = df["close"].iloc[-2]

    signal = None

    if trend == "BULL" and prev_fast < prev_slow and curr_fast > curr_slow:
        signal = "🟢 BUY (Swing EMA Crossover)"

    if trend == "BEAR" and prev_fast > prev_slow and curr_fast < curr_slow:
        signal = "🔴 SELL (Swing EMA Crossover)"

    if not signal:
        return

    key = f"{symbol}_{signal}"
    now = time.time()

    if key in last_signal and now - last_signal[key] < COOLDOWN:
        return

    last_signal[key] = now

    message = (
        f"{signal}\n"
        f"🤖 Source: {BOT_SOURCE}\n\n"
        f"📊 Pair: {symbol}\n"
        f"⏱ Entry TF: 1H\n"
        f"📈 Trend TF: 4H\n"
        f"💰 Price: {price}\n"
        f"🕒 UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
    )

    send_alert(message)

# ===============================
# ▶️ START MESSAGE
# ===============================
send_alert(
    "✅ Swing Trading Bot Started\n"
    "📊 Strategy: 4H Trend + 1H EMA Crossover\n"
    "⏱ Scan Interval: 1 Hour\n"
    f"🤖 Source: {BOT_SOURCE}"
)

# ===============================
# ▶️ RUN ONCE (GITHUB ACTION)
# ===============================
for pair in PAIRS:
    try:
        check_entry(pair)
    except Exception as e:
        send_alert(f"⚠️ Error on {pair}: {e}")
