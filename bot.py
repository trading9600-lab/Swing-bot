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
# 🔐 TELEGRAM CONFIG
# ===============================
TOKEN = "8364584748:AAFeym3et4zJwmdKRxYtP3ieIKV8FuPWdQ8"
CHAT_ID = "@Tradecocom"

# ===============================
# ⚙️ SETTINGS
# ===============================
PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]

EMA_FAST = 20
EMA_SLOW = 50
EMA_TREND = 200

COOLDOWN = 900  # 15 minutes cooldown

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
def get_data(symbol, timeframe, limit=300):
    candles = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    return pd.DataFrame(
        candles,
        columns=["time", "open", "high", "low", "close", "volume"]
    )

# ===============================
# 📈 GENERIC TREND FUNCTION
# ===============================
def get_trend(symbol, timeframe):
    df = get_data(symbol, timeframe)
    df["ema200"] = df["close"].ewm(span=EMA_TREND).mean()

    close = df["close"].iloc[-2]
    ema200 = df["ema200"].iloc[-2]

    return "BULL" if close > ema200 else "BEAR"

# ===============================
# 🚀 GENERIC ENTRY CHECK
# ===============================
def check_entry(symbol, trend_tf, entry_tf, strategy_name):
    trend = get_trend(symbol, trend_tf)

    df = get_data(symbol, entry_tf)
    df["ema20"] = df["close"].ewm(span=EMA_FAST).mean()
    df["ema50"] = df["close"].ewm(span=EMA_SLOW).mean()

    prev_fast = df["ema20"].iloc[-3]
    prev_slow = df["ema50"].iloc[-3]
    curr_fast = df["ema20"].iloc[-2]
    curr_slow = df["ema50"].iloc[-2]
    price = df["close"].iloc[-2]

    signal = None

    if trend == "BULL" and prev_fast < prev_slow and curr_fast > curr_slow:
        signal = f"🟢 BUY ({strategy_name})"

    if trend == "BEAR" and prev_fast > prev_slow and curr_fast < curr_slow:
        signal = f"🔴 SELL ({strategy_name})"

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
        f"⏱ Entry TF: {entry_tf}\n"
        f"📈 Trend TF: {trend_tf} (EMA 200)\n"
        f"💰 Price: {price}\n"
        f"🕒 UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
    )

    send_alert(message)

# ===============================
# ▶️ START MESSAGE
# ===============================
send_alert(
    "✅ Multi-Strategy Bot Started\n"
    "📊 Strategy 1: 4H Trend + 1H EMA Cross\n"
    "⚡ Strategy 2: 1H Trend + 15M EMA Cross\n"
    "⏱ Scan Interval: 15 Minutes\n"
    f"🤖 Source: {BOT_SOURCE}"
)

# ===============================
# ▶️ RUN
# ===============================
for pair in PAIRS:
    try:
        # 🔵 Strategy 1 (Original)
        check_entry(
            symbol=pair,
            trend_tf="4h",
            entry_tf="1h",
            strategy_name="Swing 4H/1H"
        )

        # 🟣 Strategy 2 (New)
        check_entry(
            symbol=pair,
            trend_tf="1h",
            entry_tf="15m",
            strategy_name="Intraday 1H/15M"
        )

    except Exception as e:
        send_alert(f"⚠️ Error on {pair}: {e}")
        
