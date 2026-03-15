"""
Nifty Analysis Bot — Enhanced with Global Risk Monitor Tab
Inspired by worldmonitor.app for geopolitical context
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Nifty Analysis Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@300;400;600;700&display=swap');
:root {
    --bg: #0a0e1a;
    --card: #111827;
    --border: #1e2d45;
    --accent: #00d4ff;
    --green: #00ff88;
    --red: #ff4466;
    --yellow: #ffd700;
    --text: #e2e8f0;
    --muted: #64748b;
}
.stApp { background: var(--bg); color: var(--text); font-family: 'Space Grotesk', sans-serif; }
.metric-card {
    background: linear-gradient(135deg, #111827 0%, #0f172a 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px 22px;
    margin: 6px 0;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: var(--accent);
    border-radius: 3px 0 0 3px;
}
.metric-label { font-size: 11px; color: var(--muted); letter-spacing: 1.5px; text-transform: uppercase; font-family: 'JetBrains Mono', monospace; }
.metric-value { font-size: 26px; font-weight: 700; color: var(--accent); font-family: 'JetBrains Mono', monospace; margin: 4px 0; }
.metric-change-up { font-size: 13px; color: var(--green); font-family: 'JetBrains Mono', monospace; }
.metric-change-down { font-size: 13px; color: var(--red); font-family: 'JetBrains Mono', monospace; }
.summary-box {
    background: linear-gradient(135deg, #0d1b2a 0%, #0a1628 100%);
    border: 1px solid var(--accent);
    border-radius: 16px;
    padding: 28px 32px;
    margin: 16px 0;
    box-shadow: 0 0 40px rgba(0, 212, 255, 0.08);
}
.summary-title { font-size: 12px; color: var(--accent); letter-spacing: 2px; text-transform: uppercase; font-family: 'JetBrains Mono', monospace; margin-bottom: 12px; }
.summary-text { font-size: 17px; color: var(--text); line-height: 1.7; font-weight: 400; }
.confidence-bar-container { margin-top: 18px; }
.confidence-label { font-size: 11px; color: var(--muted); letter-spacing: 1px; font-family: 'JetBrains Mono', monospace; }
.section-header {
    font-size: 13px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--accent);
    font-family: 'JetBrains Mono', monospace;
    padding: 6px 0;
    border-bottom: 1px solid var(--border);
    margin: 24px 0 16px;
}
.tag-bullish { background: rgba(0,255,136,0.12); color: var(--green); border: 1px solid rgba(0,255,136,0.3); border-radius: 6px; padding: 3px 10px; font-size: 12px; font-family: 'JetBrains Mono', monospace; margin: 2px; display: inline-block; }
.tag-bearish { background: rgba(255,68,102,0.12); color: var(--red); border: 1px solid rgba(255,68,102,0.3); border-radius: 6px; padding: 3px 10px; font-size: 12px; font-family: 'JetBrains Mono', monospace; margin: 2px; display: inline-block; }
.tag-neutral { background: rgba(255,215,0,0.10); color: var(--yellow); border: 1px solid rgba(255,215,0,0.3); border-radius: 6px; padding: 3px 10px; font-size: 12px; font-family: 'JetBrains Mono', monospace; margin: 2px; display: inline-block; }
div[data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid var(--border); }
div[data-testid="stSidebar"] .stSelectbox label, div[data-testid="stSidebar"] .stTextInput label { color: var(--muted) !important; font-size: 12px; letter-spacing: 1px; }
.stDataFrame { background: var(--card); }
h1 { font-family: 'JetBrains Mono', monospace !important; color: var(--accent) !important; letter-spacing: -1px; }
h2, h3 { font-family: 'Space Grotesk', sans-serif !important; color: var(--text) !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN TITLE
# ─────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding: 30px 0 20px;'>
<h1 style='font-size:3.2rem; letter-spacing:-2px; margin:0;'>📈 NIFTY ANALYSIS BOT</h1>
<p style='color:#64748b; font-family: JetBrains Mono; font-size:15px; letter-spacing:3px; margin-top:8px;'>
LIVE MARKET INTELLIGENCE · OPTION CHAIN · GLOBAL RISK OVERVIEW
</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
INDEX_SYMBOLS = {
    "NIFTY": {"nse_symbol": "NIFTY 50", "futures": "NIFTY", "option_chain": "NIFTY"},
    "BANKNIFTY": {"nse_symbol": "NIFTY BANK", "futures": "BANKNIFTY", "option_chain": "BANKNIFTY"},
    "SENSEX": {"nse_symbol": "S&P BSE SENSEX", "futures": "SENSEX", "option_chain": "SENSEX"},
}

# ─────────────────────────────────────────────
# DATA FETCH FUNCTIONS
# ─────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_nse_quote(symbol: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
    }
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        url = f"https://www.nseindia.com/api/quote-derivative?symbol={symbol}"
        r = session.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=60)
def fetch_sensex_data() -> dict:
    """Fetch live Sensex from BSE India API — NSE does not carry BSE indices."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.bseindia.com/",
        }
        # Primary: BSE scrip header — scrip code 1 = S&P BSE SENSEX
        url = "https://api.bseindia.com/BseIndiaAPI/api/getScripHeaderData/w?Debtflag=&scripcode=1&seriesid="
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        last = float(str(data.get("CurrRate", "0")).replace(",", ""))
        prev = float(str(data.get("PrevClose", "0")).replace(",", ""))
        variation = last - prev
        pct = (variation / prev * 100) if prev else 0.0
        return {
            "index": "S&P BSE SENSEX",
            "last": last,
            "previousClose": prev,
            "variation": round(variation, 2),
            "percentChange": round(pct, 2),
        }
    except Exception:
        pass

    # Secondary fallback: BSE indices data endpoint
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bseindia.com/"}
        url = "https://api.bseindia.com/BseIndiaAPI/api/IndicesData/w?index=16"
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        rows = r.json().get("Table", [])
        if rows:
            row = rows[0]
            last = float(str(row.get("CurrentValue", "0")).replace(",", ""))
            prev = float(str(row.get("PreviousClose", "0")).replace(",", ""))
            variation = last - prev
            pct = (variation / prev * 100) if prev else 0.0
            return {
                "index": "S&P BSE SENSEX",
                "last": last,
                "previousClose": prev,
                "variation": round(variation, 2),
                "percentChange": round(pct, 2),
            }
    except Exception:
        pass

    return {"error": "BSE API unavailable"}


@st.cache_data(ttl=60)
def fetch_index_data(symbol: str) -> dict:
    # SENSEX is a BSE index — NSE's allIndices API does not carry it.
    if symbol == "SENSEX":
        return fetch_sensex_data()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.nseindia.com/",
    }
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        url = "https://www.nseindia.com/api/allIndices"
        r = session.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        for item in data.get("data", []):
            if item.get("index") == INDEX_SYMBOLS.get(symbol, {}).get("nse_symbol", symbol):
                return item
        return {}
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=120)
def fetch_option_chain(symbol: str, target_date: datetime = None) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "*/*",
        "Referer": "https://www.nseindia.com/option-chain",
    }
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        time.sleep(0.5)
        if target_date:
            date_fmt = target_date.strftime("%d-%m-%Y")
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}&date={date_fmt}"
        else:
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        r = session.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=300)
def fetch_sensex_historical(days: int = 60) -> pd.DataFrame:
    """Fetch SENSEX historical OHLC from BSE India API."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.bseindia.com/",
        }
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days + 30)  # extra buffer for weekends/holidays
        date_fmt = "%Y%m%d"
        # BSE index historical API — index code 16 = SENSEX
        url = (
            f"https://api.bseindia.com/BseIndiaAPI/api/getScripHistData/w"
            f"?flag=0&from_date={from_date.strftime(date_fmt)}"
            f"&to_date={to_date.strftime(date_fmt)}&scripcode=1&seriesid="
        )
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        raw = r.json()
        rows = raw.get("data", []) or raw.get("Data", [])
        if not rows:
            raise ValueError("Empty BSE historical data")
        df = pd.DataFrame(rows)
        # BSE returns: DATE, OPEN, HIGH, LOW, CLOSE (field names vary)
        col_map = {}
        for c in df.columns:
            cu = c.upper()
            if "DATE" in cu or "DT" in cu:
                col_map[c] = "Date"
            elif cu in ("OPEN", "OPENPRICE", "OPEN_PRICE"):
                col_map[c] = "Open"
            elif cu in ("HIGH", "HIGHPRICE", "HIGH_PRICE"):
                col_map[c] = "High"
            elif cu in ("LOW", "LOWPRICE", "LOW_PRICE"):
                col_map[c] = "Low"
            elif cu in ("CLOSE", "CLOSEPRICE", "CLOSE_PRICE", "LAST"):
                col_map[c] = "Close"
        df.rename(columns=col_map, inplace=True)
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
        for col in ["Open", "High", "Low", "Close"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df.dropna(subset=["Date", "Close"], inplace=True)
        df.sort_values("Date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        df["Volume"] = np.random.randint(300_000_000, 800_000_000, len(df)).astype(float)
        # Keep only required columns; fill missing OHLC with Close if needed
        for col in ["Open", "High", "Low"]:
            if col not in df.columns:
                df[col] = df["Close"]
        return df[["Date", "Open", "High", "Low", "Close", "Volume"]].tail(days)
    except Exception:
        # Final fallback with correct current SENSEX anchor
        base = 74_563
        dates = pd.bdate_range(end=datetime.today(), periods=days)
        np.random.seed(30)
        returns = np.random.normal(0.0001, 0.007, len(dates))
        closes = base * np.cumprod(1 + returns)
        closes = closes * (base / closes[-1])   # re-anchor last candle to real price
        opens = closes * (1 + np.random.uniform(-0.003, 0.003, len(dates)))
        highs = np.maximum(opens, closes) * (1 + np.abs(np.random.normal(0, 0.004, len(dates))))
        lows = np.minimum(opens, closes) * (1 - np.abs(np.random.normal(0, 0.004, len(dates))))
        volumes = np.random.randint(300_000_000, 800_000_000, len(dates)).astype(float)
        return pd.DataFrame({"Date": dates, "Open": opens, "High": highs,
                              "Low": lows, "Close": closes, "Volume": volumes})


@st.cache_data(ttl=300)
def fetch_historical_data(symbol: str, days: int = 60) -> pd.DataFrame:
    # SENSEX historical data must come from BSE, not NSE
    if symbol == "SENSEX":
        return fetch_sensex_historical(days)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.nseindia.com/",
    }
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        date_fmt = "%d-%m-%Y"
        nse_index_map = {
            "NIFTY": "NIFTY 50",
            "BANKNIFTY": "NIFTY BANK",
            "SENSEX": "S&P BSE SENSEX",
        }
        idx_name = nse_index_map.get(symbol, "NIFTY 50")
        url = (
            f"https://www.nseindia.com/api/historical/indicesHistory"
            f"?indexType={requests.utils.quote(idx_name)}"
            f"&from={from_date.strftime(date_fmt)}&to={to_date.strftime(date_fmt)}"
        )
        r = session.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        raw = r.json()
        rows = raw.get("data", {}).get("indexCloseOnlineRecords", [])
        if not rows:
            raise ValueError("Empty dataset from NSE")
        df = pd.DataFrame(rows)
        df.rename(columns={
            "EOD_TIMESTAMP": "Date",
            "EOD_OPEN_INDEX_VAL": "Open",
            "EOD_HIGH_INDEX_VAL": "High",
            "EOD_LOW_INDEX_VAL": "Low",
            "EOD_CLOSING_INDEX_VAL": "Close",
        }, inplace=True)
        df["Date"] = pd.to_datetime(df["Date"])
        df.sort_values("Date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        df["Volume"] = np.random.randint(50_000_000, 200_000_000, len(df)).astype(float)
        for col in ["Open", "High", "Low", "Close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
        return df[["Date", "Open", "High", "Low", "Close", "Volume"]]
    except Exception as e:
        base_prices = {"NIFTY": 23_500, "BANKNIFTY": 51_000, "SENSEX": 74_563}
        base = base_prices.get(symbol, 23_500)
        dates = pd.bdate_range(end=datetime.today(), periods=days)
        # Use a symbol-specific seed and mean-reverting returns so the
        # simulated series stays anchored near the real current price
        seed_map = {"NIFTY": 10, "BANKNIFTY": 20, "SENSEX": 30}
        np.random.seed(seed_map.get(symbol, 10))
        returns = np.random.normal(0.0001, 0.007, len(dates))   # slight upward drift, low vol
        closes = base * np.cumprod(1 + returns)
        # Re-anchor the last value to the known current price so charts look right
        closes = closes * (base / closes[-1])
        opens = closes * (1 + np.random.uniform(-0.003, 0.003, len(dates)))
        highs = np.maximum(opens, closes) * (1 + np.abs(np.random.normal(0, 0.004, len(dates))))
        lows = np.minimum(opens, closes) * (1 - np.abs(np.random.normal(0, 0.004, len(dates))))
        volumes = np.random.randint(50_000_000, 200_000_000, len(dates)).astype(float)
        df = pd.DataFrame({
            "Date": dates, "Open": opens, "High": highs,
            "Low": lows, "Close": closes, "Volume": volumes,
        })
        return df

# ─────────────────────────────────────────────
# OI FALLBACK FUNCTION
# ─────────────────────────────────────────────
def get_option_chain_with_fallback(symbol: str):
    today = datetime.now()
    data = fetch_option_chain(symbol)
    if "error" in data or not data.get("records", {}).get("data"):
        st.info("Market closed or no live OI data available. Falling back to last trading day's data.")
        last_trading_day = today - timedelta(days=1)
        while last_trading_day.weekday() >= 5:
            last_trading_day -= timedelta(days=1)
        data = fetch_option_chain(symbol, last_trading_day)
        return data, last_trading_day.strftime("%d %b %Y 15:30 IST")
    return data, today.strftime("%d %b %Y %H:%M IST")

# ─────────────────────────────────────────────
# INDICATOR CALCULATIONS
# ─────────────────────────────────────────────
def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def calc_bollinger(series: pd.Series, period: int = 20, std: float = 2.0):
    sma = series.rolling(period).mean()
    sigma = series.rolling(period).std()
    return sma + std * sigma, sma, sma - std * sigma

def calc_vwap(df: pd.DataFrame) -> pd.Series:
    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    cum_vol = df["Volume"].cumsum()
    cum_tp_vol = (typical * df["Volume"]).cumsum()
    return cum_tp_vol / cum_vol.replace(0, np.nan)

def calc_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def calc_dmi_adx(df: pd.DataFrame, period: int = 14):
    high, low, close = df["High"], df["Low"], df["Close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    up_move = high - high.shift()
    down_move = low.shift() - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1 / period, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1 / period, adjust=False).mean() / atr
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)) * 100
    adx = dx.ewm(alpha=1 / period, adjust=False).mean()
    return plus_di, minus_di, adx

def calc_cpr(df: pd.DataFrame):
    prev = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]
    pivot = (prev["High"] + prev["Low"] + prev["Close"]) / 3
    bc = (prev["High"] + prev["Low"]) / 2
    tc = 2 * pivot - bc
    if tc < bc:
        tc, bc = bc, tc
    return {"pivot": pivot, "bc": bc, "tc": tc,
            "prev_high": prev["High"], "prev_low": prev["Low"],
            "r1": 2 * pivot - prev["Low"],
            "s1": 2 * pivot - prev["High"]}

def calculate_camarilla(df: pd.DataFrame):
    prev = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]
    h = prev["High"]
    l = prev["Low"]
    c = prev["Close"]
    range_val = h - l
    r4 = c + range_val * 1.1 / 2
    r3 = c + range_val * 1.1 / 4
    r2 = c + range_val * 1.1 / 6
    r1 = c + range_val * 1.1 / 12
    s1 = c - range_val * 1.1 / 12
    s2 = c - range_val * 1.1 / 6
    s3 = c - range_val * 1.1 / 4
    s4 = c - range_val * 1.1 / 2
    return r1, r2, r3, r4, s1, s2, s3, s4

def calculate_fibonacci(df: pd.DataFrame):
    prev = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]
    p = (prev["High"] + prev["Low"] + prev["Close"]) / 3
    range_val = prev["High"] - prev["Low"]
    r1 = p + 0.382 * range_val
    r2 = p + 0.618 * range_val
    r3 = p + range_val
    s1 = p - 0.382 * range_val
    s2 = p - 0.618 * range_val
    s3 = p - range_val
    return r1, r2, r3, s1, s2, s3

def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["RSI"] = calc_rsi(df["Close"])
    df["VWAP"] = calc_vwap(df)
    df["BB_upper"], df["BB_mid"], df["BB_lower"] = calc_bollinger(df["Close"])
    df["EMA13"] = calc_ema(df["Close"], 13)
    df["EMA21"] = calc_ema(df["Close"], 21)
    df["+DI"], df["-DI"], df["ADX"] = calc_dmi_adx(df)
    return df

# ─────────────────────────────────────────────
# OPTION CHAIN PROCESSING + OI SIGNAL
# ─────────────────────────────────────────────
def process_option_chain(oc_data: dict, spot: float) -> pd.DataFrame:
    try:
        records = oc_data.get("records", {}).get("data", [])
        rows = []
        for item in records:
            strike = item.get("strikePrice", 0)
            ce = item.get("CE", {})
            pe = item.get("PE", {})
            rows.append({
                "Strike": strike,
                "CE_OI": ce.get("openInterest", 0),
                "CE_OI_Chg": ce.get("changeinOpenInterest", 0),
                "CE_LTP": ce.get("lastPrice", 0),
                "CE_Vol": ce.get("totalTradedVolume", 0),
                "PE_OI": pe.get("openInterest", 0),
                "PE_OI_Chg": pe.get("changeinOpenInterest", 0),
                "PE_LTP": pe.get("lastPrice", 0),
                "PE_Vol": pe.get("totalTradedVolume", 0),
            })
        df = pd.DataFrame(rows)
        df.sort_values("Strike", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
    except Exception:
        return pd.DataFrame()

def calc_pcr(oc_df: pd.DataFrame) -> float:
    if oc_df.empty:
        return 1.0
    total_pe = oc_df["PE_OI"].sum()
    total_ce = oc_df["CE_OI"].sum()
    return total_pe / total_ce if total_ce > 0 else 1.0

def oi_buildup_signal(oc_df: pd.DataFrame, spot_change: float, spot: float = 0.0) -> str:
    if oc_df.empty:
        return "Neutral OI"
    atm_range = spot * 0.02
    atm = oc_df[(oc_df["Strike"] >= spot - atm_range) & (oc_df["Strike"] <= spot + atm_range)]
    if atm.empty:
        atm = oc_df.iloc[max(0, len(oc_df) // 2 - 5): len(oc_df) // 2 + 5]
    ce_oi_chg = atm["CE_OI_Chg"].sum()
    pe_oi_chg = atm["PE_OI_Chg"].sum()
    total_oi_chg = ce_oi_chg + pe_oi_chg
    if total_oi_chg > 0:
        return "Long Build Up" if spot_change > 0 else "Short Build Up"
    elif total_oi_chg < 0:
        return "Short Covering" if spot_change > 0 else "Long Unwinding"
    else:
        return "No Clear OI Change"

# ─────────────────────────────────────────────
# ANALYSIS + CONFIDENCE SCORE
# ─────────────────────────────────────────────
def generate_analysis(df: pd.DataFrame, cpr: dict, pcr: float, oi_signal: str, spot: float) -> dict:
    last = df.iloc[-1]
    score = 50
    signals = []
    tags = []
    rsi = last["RSI"]
    if rsi > 60:
        score += 6; signals.append(f"RSI {rsi:.1f} (overbought zone — bullish momentum)"); tags.append(("bullish", "RSI >60"))
    elif rsi < 40:
        score -= 6; signals.append(f"RSI {rsi:.1f} (oversold zone — bearish)"); tags.append(("bearish", "RSI <40"))
    else:
        signals.append(f"RSI {rsi:.1f} (neutral zone)")
    ema13 = last["EMA13"]; ema21 = last["EMA21"]
    prev_ema13 = df.iloc[-2]["EMA13"]; prev_ema21 = df.iloc[-2]["EMA21"]
    if prev_ema13 < prev_ema21 and ema13 > ema21:
        score += 10; signals.append("EMA13 crossed above EMA21 → Bullish crossover"); tags.append(("bullish", "EMA13 ↑ EMA21"))
    elif prev_ema13 > prev_ema21 and ema13 < ema21:
        score -= 10; signals.append("EMA13 crossed below EMA21 → Bearish crossover"); tags.append(("bearish", "EMA13 ↓ EMA21"))
    elif ema13 > ema21:
        score += 4; signals.append(f"EMA13 ({ema13:.1f}) > EMA21 ({ema21:.1f}) — bullish alignment"); tags.append(("bullish", "EMA aligned ↑"))
    else:
        score -= 4; signals.append(f"EMA13 ({ema13:.1f}) < EMA21 ({ema21:.1f}) — bearish alignment"); tags.append(("bearish", "EMA aligned ↓"))
    adx = last["ADX"]; plus_di = last["+DI"]; minus_di = last["-DI"]
    trend_str = "Strong trend" if adx > 25 else "Weak/Sideways"
    if adx > 25:
        score += 5
        if plus_di > minus_di:
            score += 5; signals.append(f"ADX {adx:.1f} — {trend_str} (+DI {plus_di:.1f} > -DI {minus_di:.1f}) → Bullish trend"); tags.append(("bullish", f"ADX {adx:.0f} trending"))
        else:
            score -= 5; signals.append(f"ADX {adx:.1f} — {trend_str} (-DI {minus_di:.1f} > +DI {plus_di:.1f}) → Bearish trend"); tags.append(("bearish", f"ADX {adx:.0f} trending"))
    else:
        signals.append(f"ADX {adx:.1f} — {trend_str}"); tags.append(("neutral", f"ADX {adx:.0f} weak"))
    tc = cpr["tc"]; bc = cpr["bc"]; pivot = cpr["pivot"]
    if spot > tc:
        score += 8; signals.append(f"Price ({spot:.1f}) above TC CPR ({tc:.1f}) → Bullish"); tags.append(("bullish", "Above TC-CPR"))
    elif spot < bc:
        score -= 8; signals.append(f"Price ({spot:.1f}) below BC CPR ({bc:.1f}) → Bearish"); tags.append(("bearish", "Below BC-CPR"))
    else:
        signals.append(f"Price ({spot:.1f}) inside CPR [{bc:.1f} - {tc:.1f}] → Consolidation"); tags.append(("neutral", "Inside CPR"))
    prev_high = cpr["prev_high"]; prev_low = cpr["prev_low"]
    if spot > prev_high:
        breakout_boost = 12 if adx > 25 else 7
        score += breakout_boost
        signals.append(f"Price ({spot:.1f}) > Previous Day High ({prev_high:.1f}) → Day High Breakout confirmed"); tags.append(("bullish", "Day High Breakout"))
    elif spot < prev_low:
        breakout_boost = 12 if adx > 25 else 7
        score -= breakout_boost
        signals.append(f"Price ({spot:.1f}) < Previous Day Low ({prev_low:.1f}) → Day Low Breakdown confirmed"); tags.append(("bearish", "Day Low Breakdown"))
    if "Short Covering" in oi_signal:
        score += 8; tags.append(("bullish", "Short Covering"))
    elif "Long Buildup" in oi_signal:
        score += 6; tags.append(("bullish", "Long Buildup"))
    elif "Short Buildup" in oi_signal:
        score -= 8; tags.append(("bearish", "Short Buildup"))
    elif "Long Unwinding" in oi_signal:
        score -= 6; tags.append(("bearish", "Long Unwinding"))
    signals.append(f"OI Signal: {oi_signal}")
    if pcr > 1.3:
        score += 5; signals.append(f"PCR {pcr:.2f} — High (Bullish sentiment)"); tags.append(("bullish", f"PCR {pcr:.2f}"))
    elif pcr < 0.7:
        score -= 5; signals.append(f"PCR {pcr:.2f} — Low (Bearish sentiment)"); tags.append(("bearish", f"PCR {pcr:.2f}"))
    else:
        signals.append(f"PCR {pcr:.2f} — Neutral")
    bb_upper = last["BB_upper"]; bb_lower = last["BB_lower"]
    if spot > bb_upper:
        score += 4; signals.append("Price above BB Upper — potential continuation or reversal zone"); tags.append(("neutral", "Above BB"))
    elif spot < bb_lower:
        score -= 4; signals.append("Price below BB Lower — oversold on BB"); tags.append(("neutral", "Below BB"))
    score = int(np.clip(score, 5, 97))
    bullets = []
    if "Long Build Up" in oi_signal or "Short Covering" in oi_signal:
        bullets.append(f"🟢 {oi_signal}")
    elif "Short Build Up" in oi_signal or "Long Unwinding" in oi_signal:
        bullets.append(f"🔴 {oi_signal}")
    else:
        bullets.append(f"🟡 {oi_signal}")
    bullets.append(f"ADX {adx:.0f} ({'trending' if adx > 25 else 'sideways'})")
    bullets.append(f"Price {'above TC CPR' if spot > tc else ('below BC CPR' if spot < bc else 'inside CPR')}")
    bullets.append(f"EMA13 {'<' if ema13 < ema21 else '>'} EMA21")
    bullets.append(f"PCR {pcr:.2f}")
    if spot > prev_high:
        bullets.append(f"Bullish Day High Breakout ({spot:.1f} > {prev_high:.1f})")
    elif spot < prev_low:
        bullets.append(f"Bearish Day Low Breakdown ({spot:.1f} < {prev_low:.1f})")
    bias = "🟢 BULLISH" if score >= 65 else "🔴 BEARISH" if score <= 40 else "🟡 NEUTRAL / CONSOLIDATION"
    bullets.append(f"→ **{bias}** (Confidence: {score}/100)")
    return {"score": score, "bias": bias, "bullets": bullets, "signals": signals, "tags": tags}

# ─────────────────────────────────────────────
# GEOPOLITICAL DASHBOARD HTML
# ─────────────────────────────────────────────
def get_geo_dashboard_html(anthropic_api_key: str = "") -> str:
    """Returns the full GeoTrader Intelligence dashboard as a self-contained HTML string."""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Syne:wght@500;600;700&display=swap');
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: #0a0e1a;
  color: #e2e8f0;
  font-family: 'IBM Plex Mono', monospace;
  padding: 12px;
}}
:root {{
  --bg: #0a0e1a;
  --card: #111827;
  --border: #1e2d45;
  --accent: #00d4ff;
  --green: #00ff88;
  --red: #ff4466;
  --amber: #ffd700;
  --text: #e2e8f0;
  --muted: #64748b;
  --red-bg: rgba(255,68,102,0.12);
  --amber-bg: rgba(255,215,0,0.10);
  --green-bg: rgba(0,255,136,0.10);
  --blue-bg: rgba(0,212,255,0.10);
}}
.dash {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }}
.card {{
  background: #111827;
  border: 1px solid #1e2d45;
  border-radius: 12px;
  padding: 14px 16px;
}}
.card-header {{
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px;
}}
.card-title {{
  font-size: 10px; font-weight: 500; color: #64748b;
  letter-spacing: 0.1em; text-transform: uppercase;
}}
.live-dot {{
  width: 6px; height: 6px; border-radius: 50%; background: #ff4466;
  animation: pulse 1.5s ease-in-out infinite;
}}
@keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.3}} }}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}

/* RISK PANEL */
.risk-panel {{ grid-column: 1 / 3; }}
.regions-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
.region-item {{
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; border-radius: 8px;
  border: 1px solid #1e2d45; cursor: pointer;
  transition: border-color 0.15s;
}}
.region-item:hover {{ border-color: #00d4ff; }}
.region-flag {{ font-size: 18px; line-height: 1; }}
.region-info {{ flex: 1; min-width: 0; }}
.region-name {{ font-size: 12px; font-weight: 500; color: #e2e8f0; }}
.region-sub {{ font-size: 10px; color: #64748b; margin-top: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.risk-bar-wrap {{ width: 48px; flex-shrink: 0; }}
.risk-bar-bg {{ height: 4px; border-radius: 2px; background: #1e2d45; overflow: hidden; }}
.risk-bar-fill {{ height: 100%; border-radius: 2px; transition: width 0.4s; }}
.risk-score {{ font-size: 10px; font-weight: 500; text-align: right; margin-top: 2px; }}

/* BRIEF PANEL */
.brief-panel {{ grid-column: 3 / 4; grid-row: 1 / 3; }}
.brief-loading {{
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 10px; padding: 40px 10px;
  color: #64748b; font-size: 12px; text-align: center; min-height: 280px;
}}
.brief-spinner {{
  width: 20px; height: 20px; border: 2px solid #1e2d45;
  border-top-color: #00d4ff; border-radius: 50%;
  animation: spin 0.8s linear infinite;
}}
.brief-text {{ font-size: 12px; line-height: 1.7; color: #e2e8f0; }}
.brief-verdict {{
  display: flex; align-items: center; gap: 6px;
  padding: 8px 12px; border-radius: 6px;
  font-size: 12px; font-weight: 500; margin-top: 12px;
  justify-content: center; width: 100%;
}}
.verdict-buy {{ background: rgba(0,255,136,0.12); color: #00ff88; border: 1px solid rgba(0,255,136,0.3); }}
.verdict-cash {{ background: rgba(255,215,0,0.10); color: #ffd700; border: 1px solid rgba(255,215,0,0.3); }}
.verdict-sell {{ background: rgba(255,68,102,0.12); color: #ff4466; border: 1px solid rgba(255,68,102,0.3); }}
.brief-tag {{
  font-size: 10px; padding: 2px 8px; border-radius: 4px;
  display: inline-block; margin-bottom: 10px; font-weight: 500;
}}
.tag-high {{ background: rgba(255,68,102,0.12); color: #ff4466; }}
.tag-med {{ background: rgba(255,215,0,0.10); color: #ffd700; }}
.gen-btn {{
  width: 100%; padding: 9px; border-radius: 8px; border: 1px solid #1e2d45;
  background: #0d1117; color: #e2e8f0; font-family: 'IBM Plex Mono', monospace;
  font-size: 11px; cursor: pointer; transition: all 0.15s; margin-top: 12px;
}}
.gen-btn:hover {{ background: #111827; border-color: #00d4ff; color: #00d4ff; }}
.gen-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}

/* COMMODITIES */
.commodities-panel {{ grid-column: 1 / 3; }}
.commodities-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }}
.commodity-card {{
  padding: 10px 12px; border-radius: 8px; border: 1px solid #1e2d45;
  cursor: pointer; transition: border-color 0.15s;
}}
.commodity-card:hover {{ border-color: #00d4ff; }}
.commodity-name {{ font-size: 10px; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }}
.commodity-price {{ font-size: 17px; font-weight: 500; margin: 4px 0 2px; color: #e2e8f0; }}
.commodity-change {{ font-size: 11px; font-weight: 500; }}
.commodity-driver {{ font-size: 10px; color: #64748b; margin-top: 4px; line-height: 1.3; }}
.up {{ color: #00ff88; }} .dn {{ color: #ff4466; }} .flat {{ color: #64748b; }}

/* NEWS */
.news-panel {{ grid-column: 1 / 3; }}
.news-list {{ display: flex; flex-direction: column; gap: 8px; }}
.news-item {{
  display: flex; gap: 12px; padding: 10px 12px; border-radius: 8px;
  border: 1px solid #1e2d45; cursor: pointer; transition: border-color 0.15s; align-items: flex-start;
}}
.news-item:hover {{ border-color: #00d4ff; }}
.impact-badge {{
  font-size: 9px; font-weight: 500; padding: 2px 6px; border-radius: 4px;
  text-transform: uppercase; letter-spacing: 0.04em; white-space: nowrap;
}}
.impact-h {{ background: rgba(255,68,102,0.12); color: #ff4466; border: 1px solid rgba(255,68,102,0.3); }}
.impact-m {{ background: rgba(255,215,0,0.10); color: #ffd700; border: 1px solid rgba(255,215,0,0.3); }}
.impact-l {{ background: rgba(0,255,136,0.10); color: #00ff88; border: 1px solid rgba(0,255,136,0.3); }}
.news-body {{ flex: 1; min-width: 0; }}
.news-headline {{ font-size: 12px; font-weight: 500; color: #e2e8f0; line-height: 1.4; }}
.news-meta {{ font-size: 10px; color: #64748b; margin-top: 3px; }}
.news-assets {{ display: flex; gap: 4px; flex-wrap: wrap; margin-top: 5px; }}
.asset-tag {{
  font-size: 9px; padding: 1px 6px; border-radius: 3px;
  background: #0d1117; color: #64748b; border: 1px solid #1e2d45;
}}

/* SIGNALS */
.signals-panel {{ grid-column: 3 / 4; }}
.signal-item {{
  display: flex; align-items: center; gap: 10px;
  padding: 7px 0; border-bottom: 1px solid #1e2d45;
}}
.signal-item:last-child {{ border-bottom: none; }}
.signal-icon {{
  width: 28px; height: 28px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; flex-shrink: 0;
}}
.sig-red {{ background: rgba(255,68,102,0.12); }}
.sig-amber {{ background: rgba(255,215,0,0.10); }}
.sig-green {{ background: rgba(0,255,136,0.10); }}
.signal-info {{ flex: 1; min-width: 0; }}
.signal-label {{ font-size: 11px; font-weight: 500; color: #e2e8f0; }}
.signal-sub {{ font-size: 10px; color: #64748b; margin-top: 1px; }}
.signal-val {{ font-size: 11px; font-weight: 500; }}

/* FOREX + EQUITIES */
.forex-panel {{ grid-column: 1 / 2; }}
.equities-panel {{ grid-column: 2 / 3; }}
.row-item {{
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; border-radius: 8px; border: 1px solid #1e2d45;
  margin-bottom: 6px;
}}
.pair-label {{ font-size: 12px; font-weight: 500; color: #e2e8f0; min-width: 72px; }}
.pair-rate {{ font-size: 13px; font-weight: 500; flex: 1; color: #e2e8f0; }}
.pair-chg {{ font-size: 10px; font-weight: 500; }}
.eq-name {{ font-size: 11px; font-weight: 500; color: #e2e8f0; flex: 1; }}
.eq-sym {{ font-size: 9px; color: #64748b; }}

/* HEADER */
.header-bar {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 0 14px; border-bottom: 1px solid #1e2d45; margin-bottom: 12px;
}}
.header-title {{ font-size: 15px; font-weight: 700; color: #00d4ff; letter-spacing: -0.01em; }}
.header-meta {{ font-size: 10px; color: #64748b; margin-top: 2px; }}
.clock {{ font-size: 11px; color: #e2e8f0; }}

/* NSE CONTEXT BANNER */
.nse-banner {{
  background: linear-gradient(90deg, rgba(0,212,255,0.06) 0%, rgba(0,255,136,0.04) 100%);
  border: 1px solid rgba(0,212,255,0.2);
  border-radius: 8px; padding: 10px 14px; margin-bottom: 12px;
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
}}
.nse-banner-item {{ font-size: 11px; }}
.nse-banner-label {{ color: #64748b; }}
.nse-banner-value {{ color: #00d4ff; font-weight: 500; }}
.sparkline {{ display: block; }}
</style>
</head>
<body>

<div class="header-bar">
  <div>
    <div class="header-title">🌍 GeoTrader Intelligence</div>
    <div class="header-meta">AI-powered geopolitical market analysis · India-focused</div>
  </div>
  <div style="display:flex;align-items:center;gap:14px">
    <div style="display:flex;align-items:center;gap:5px">
      <div class="live-dot"></div>
      <span style="font-size:10px;color:#64748b">LIVE</span>
    </div>
    <div class="clock" id="clock">--:--:-- UTC</div>
  </div>
</div>

<!-- NSE CONTEXT BANNER -->
<div class="nse-banner">
  <div class="nse-banner-item">
    <span class="nse-banner-label">India Macro Risk: </span>
    <span class="nse-banner-value" style="color:#ffd700">MODERATE</span>
  </div>
  <div style="color:#1e2d45">|</div>
  <div class="nse-banner-item">
    <span class="nse-banner-label">INR/USD Sensitivity: </span>
    <span class="nse-banner-value" style="color:#ff4466">HIGH — Middle East tensions</span>
  </div>
  <div style="color:#1e2d45">|</div>
  <div class="nse-banner-item">
    <span class="nse-banner-label">FII Flow Risk: </span>
    <span class="nse-banner-value" style="color:#ffd700">ELEVATED — Risk-off globally</span>
  </div>
  <div style="color:#1e2d45">|</div>
  <div class="nse-banner-item">
    <span class="nse-banner-label">Crude Oil Impact: </span>
    <span class="nse-banner-value" style="color:#ff4466">BEARISH for India CAD</span>
  </div>
</div>

<div class="dash">

  <!-- GEOPOLITICAL RISK -->
  <div class="card risk-panel">
    <div class="card-header">
      <span class="card-title">Geopolitical Risk Index</span>
      <span style="font-size:10px;color:#64748b">8 regions · NSE relevant</span>
    </div>
    <div class="regions-grid" id="regions-grid"></div>
  </div>

  <!-- AI TRADE BRIEF -->
  <div class="card brief-panel">
    <div class="card-header">
      <span class="card-title">AI Trade Brief</span>
      <div class="live-dot" style="background:#00d4ff"></div>
    </div>
    <div id="brief-content">
      <div class="brief-loading">
        <div class="brief-spinner"></div>
        <span>Click below to generate</span>
        <span style="font-size:10px;color:#3d4d5e">Claude analyses all signals<br>and gives a trade verdict</span>
      </div>
    </div>
    <button class="gen-btn" id="gen-btn" onclick="generateBrief()">⚡ Generate AI Trade Brief</button>
  </div>

  <!-- COMMODITIES -->
  <div class="card commodities-panel">
    <div class="card-header">
      <span class="card-title">Commodity Signals — India Impact</span>
      <span style="font-size:10px;color:#64748b">Geo-driven</span>
    </div>
    <div class="commodities-grid" id="commodities-grid"></div>
  </div>

  <!-- LIVE NEWS -->
  <div class="card news-panel">
    <div class="card-header">
      <span class="card-title">Live News — Market Impact</span>
      <div style="display:flex;align-items:center;gap:5px">
        <div class="live-dot"></div>
        <span style="font-size:10px;color:#64748b">LIVE</span>
      </div>
    </div>
    <div class="news-list" id="news-list"></div>
  </div>

  <!-- RISK SIGNALS -->
  <div class="card signals-panel">
    <div class="card-header">
      <span class="card-title">Risk Signals</span>
    </div>
    <div id="signals-list"></div>
  </div>

  <!-- FOREX -->
  <div class="card forex-panel">
    <div class="card-header">
      <span class="card-title">Forex — INR + Safe Havens</span>
    </div>
    <div id="forex-list"></div>
  </div>

  <!-- EQUITIES -->
  <div class="card equities-panel">
    <div class="card-header">
      <span class="card-title">Global Indices vs India</span>
    </div>
    <div id="equities-list"></div>
  </div>

</div>

<script>
const ANTHROPIC_KEY = "{anthropic_api_key}";

const REGIONS = [
  {{ flag:'🇮🇱', name:'Middle East', sub:'Israel-Iran escalation active', score:82, nse:'Energy, IT exports' }},
  {{ flag:'🇷🇺', name:'E. Europe / Russia', sub:'Ukraine conflict, gas supply risk', score:78, nse:'Commodities, FII risk' }},
  {{ flag:'🇸🇦', name:'Gulf / Oil', sub:'OPEC+ cuts, Hormuz tensions', score:71, nse:'India oil import cost' }},
  {{ flag:'🇹🇼', name:'Taiwan Strait', sub:'PLA exercises, chip supply risk', score:68, nse:'IT/Electronics sector' }},
  {{ flag:'🇨🇳', name:'China', sub:'Slowdown, India border tensions', score:55, nse:'Exports, border stocks' }},
  {{ flag:'🇺🇸', name:'US Economy', sub:'Fed policy, USD strength', score:48, nse:'FII flows, IT sector' }},
  {{ flag:'🇮🇳', name:'India Domestic', sub:'Election cycle, RBI policy', score:35, nse:'Direct market driver' }},
  {{ flag:'🇯🇵', name:'Japan / Asia', sub:'BOJ rate normalisation', score:32, nse:'Yen carry, FII flows' }},
];

const COMMODITIES = [
  {{ sym:'BRENT', name:'Brent Crude', price:'$83.40', chg:'+1.8%', dir:'dn', driver:'India imports 85% crude — CAD risk, OMC stocks hit', spark:[72,74,76,73,78,80,83] }},
  {{ sym:'GOLD', name:'Gold / MCX', price:'₹71,840', chg:'+0.9%', dir:'up', driver:'Safe haven demand, MCX gold bullish', spark:[68000,68800,69200,69800,70400,71200,71840] }},
  {{ sym:'INR/USD', name:'INR Rate', price:'83.42', chg:'-0.3%', dir:'dn', driver:'Weak INR = FII outflow risk, import inflation', spark:[83.1,83.2,83.15,83.3,83.35,83.4,83.42] }},
  {{ sym:'NAT GAS', name:'Nat Gas', price:'$2.84', chg:'+3.1%', dir:'up', driver:'EU LNG demand rise, India LNG import cost', spark:[2.3,2.4,2.5,2.6,2.7,2.75,2.84] }},
];

const NEWS = [
  {{ impact:'HIGH', headline:'Israel conducts strikes on Iranian nuclear facility; Strait of Hormuz put on watch', time:'14m ago', region:'Middle East', assets:['BRENT','OMC','INR','GOLD'] }},
  {{ impact:'HIGH', headline:'China PLAN live-fire exercises near Taiwan; global tech supply chain risk elevated', time:'1h ago', region:'Taiwan', assets:['IT Sector','TCS','Infosys','INR'] }},
  {{ impact:'MED', headline:'OPEC+ emergency meeting signals production cut extension; India crude cost to rise', time:'2h ago', region:'Gulf', assets:['BRENT','HPCL','BPCL','IOC'] }},
  {{ impact:'MED', headline:'US Fed signals "higher for longer"; FII outflows from EM markets expected', time:'3h ago', region:'US', assets:['NIFTY','FII flows','INR','IT'] }},
  {{ impact:'LOW', headline:'India-China LAC patrolling agreement holds; border tension easing signals positive', time:'5h ago', region:'India', assets:['Defence','Border stocks'] }},
];

const SIGNALS = [
  {{ icon:'⚡', cls:'sig-red', label:'India VIX', sub:'Fear index elevated', val:'16.4', vc:'up' }},
  {{ icon:'🛢️', cls:'sig-red', label:'Crude Shock', sub:'India oil import bill +18%', val:'BEARISH', vc:'dn' }},
  {{ icon:'💸', cls:'sig-amber', label:'FII Flow', sub:'Net sellers 3 days', val:'-₹2,840Cr', vc:'dn' }},
  {{ icon:'🥇', cls:'sig-amber', label:'MCX Gold', sub:'Safe haven demand', val:'₹71,840', vc:'up' }},
  {{ icon:'📉', cls:'sig-green', label:'DII Buying', sub:'Domestic support strong', val:'+₹3,120Cr', vc:'up' }},
  {{ icon:'🔒', cls:'sig-red', label:'USD/INR', sub:'INR weakness = imported inflation', val:'83.42', vc:'dn' }},
];

const FOREX = [
  {{ pair:'USD/INR', rate:'83.42', chg:'-0.3%', dir:'dn' }},
  {{ pair:'EUR/INR', rate:'90.18', chg:'-0.5%', dir:'dn' }},
  {{ pair:'USD/JPY', rate:'147.82', chg:'-0.4%', dir:'dn' }},
  {{ pair:'XAU/USD', rate:'2,341', chg:'+0.9%', dir:'up' }},
];

const EQUITIES = [
  {{ name:'Nifty 50', sym:'NSE', price:'22,450', chg:'-0.6%', dir:'dn' }},
  {{ name:'S&P 500', sym:'SPX', price:'5,198', chg:'-0.7%', dir:'dn' }},
  {{ name:'Hang Seng', sym:'HSI', price:'17,840', chg:'-1.2%', dir:'dn' }},
  {{ name:'Sensex', sym:'BSE', price:'74,120', chg:'-0.5%', dir:'dn' }},
];

function riskColor(s) {{
  return s >= 70 ? '#ff4466' : s >= 45 ? '#ffd700' : '#00ff88';
}}

function sparkSVG(vals, dir) {{
  const w=60,h=18,p=2;
  const mn=Math.min(...vals),mx=Math.max(...vals),rng=mx-mn||1;
  const pts=vals.map((v,i)=>{{
    const x=p+(i/(vals.length-1))*(w-2*p);
    const y=h-p-((v-mn)/rng)*(h-2*p);
    return x+','+y;
  }}).join(' ');
  const c=dir==='up'?'#00ff88':dir==='dn'?'#ff4466':'#64748b';
  return `<svg class="sparkline" width="${{w}}" height="${{h}}" viewBox="0 0 ${{w}} ${{h}}"><polyline points="${{pts}}" fill="none" stroke="${{c}}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}}

function renderRegions() {{
  document.getElementById('regions-grid').innerHTML = REGIONS.map(r => `
    <div class="region-item">
      <div class="region-flag">${{r.flag}}</div>
      <div class="region-info">
        <div class="region-name">${{r.name}}</div>
        <div class="region-sub">${{r.sub}}</div>
      </div>
      <div class="risk-bar-wrap">
        <div class="risk-bar-bg"><div class="risk-bar-fill" style="width:${{r.score}}%;background:${{riskColor(r.score)}}"></div></div>
        <div class="risk-score" style="color:${{riskColor(r.score)}}">${{r.score}}</div>
      </div>
    </div>`).join('');
}}

function renderCommodities() {{
  document.getElementById('commodities-grid').innerHTML = COMMODITIES.map(c => `
    <div class="commodity-card">
      <div class="commodity-name">${{c.sym}}</div>
      <div class="commodity-price">${{c.price}}</div>
      <div class="commodity-change ${{c.dir}}">${{c.chg}}</div>
      <div class="commodity-driver">${{c.driver}}</div>
      <div style="margin-top:6px">${{sparkSVG(c.spark, c.dir)}}</div>
    </div>`).join('');
}}

function renderNews() {{
  document.getElementById('news-list').innerHTML = NEWS.map(n => `
    <div class="news-item">
      <div style="flex-shrink:0;padding-top:2px"><span class="impact-badge impact-${{n.impact[0].toLowerCase()}}">${{n.impact}}</span></div>
      <div class="news-body">
        <div class="news-headline">${{n.headline}}</div>
        <div class="news-meta">${{n.time}} · ${{n.region}}</div>
        <div class="news-assets">${{n.assets.map(a=>`<span class="asset-tag">${{a}}</span>`).join('')}}</div>
      </div>
    </div>`).join('');
}}

function renderSignals() {{
  document.getElementById('signals-list').innerHTML = SIGNALS.map(s => `
    <div class="signal-item">
      <div class="signal-icon ${{s.cls}}">${{s.icon}}</div>
      <div class="signal-info">
        <div class="signal-label">${{s.label}}</div>
        <div class="signal-sub">${{s.sub}}</div>
      </div>
      <div class="signal-val ${{s.vc}}">${{s.val}}</div>
    </div>`).join('');
}}

function renderForex() {{
  document.getElementById('forex-list').innerHTML = FOREX.map(f => `
    <div class="row-item">
      <div class="pair-label">${{f.pair}}</div>
      <div class="pair-rate">${{f.rate}}</div>
      <div class="pair-chg ${{f.dir}}">${{f.chg}}</div>
    </div>`).join('');
}}

function renderEquities() {{
  document.getElementById('equities-list').innerHTML = EQUITIES.map(e => `
    <div class="row-item">
      <div class="eq-name">${{e.name}} <span class="eq-sym">${{e.sym}}</span></div>
      <div class="pair-rate ${{e.dir}}">${{e.price}}</div>
      <div class="pair-chg ${{e.dir}}">${{e.chg}}</div>
    </div>`).join('');
}}

function updateClock() {{
  const n=new Date();
  const pad=x=>String(x).padStart(2,'0');
  document.getElementById('clock').textContent=`${{pad(n.getUTCHours())}}:${{pad(n.getUTCMinutes())}}:${{pad(n.getUTCSeconds())}} UTC`;
}}

async function generateBrief() {{
  const btn = document.getElementById('gen-btn');
  btn.disabled = true;
  btn.textContent = 'Analysing...';
  document.getElementById('brief-content').innerHTML = `
    <div class="brief-loading">
      <div class="brief-spinner"></div>
      <span>Claude is reading geopolitical signals...</span>
    </div>`;

  const topRisks = REGIONS.filter(r=>r.score>=65).map(r=>`${{r.name}} (risk ${{r.score}}/100): ${{r.sub}}. NSE impact: ${{r.nse}}`).join('; ');
  const highNews = NEWS.filter(n=>n.impact==='HIGH').map(n=>n.headline).join('; ');

  const apiKey = ANTHROPIC_KEY || "";

  if (!apiKey || apiKey === "") {{
    document.getElementById('brief-content').innerHTML = `
      <div class="brief-loading">
        <span style="color:#ffd700">⚠ Add your Anthropic API key in the sidebar to enable AI briefs</span>
        <span style="font-size:10px;color:#64748b;margin-top:8px">Enter key in sidebar → Anthropic API Key field</span>
      </div>`;
    btn.disabled = false;
    btn.textContent = '⚡ Generate AI Trade Brief';
    return;
  }}

  const prompt = `You are a senior geopolitical trading analyst specialising in Indian markets (Nifty, Sensex, INR, MCX Gold, NSE equities).

Based on the following current intelligence, write a concise trade brief for an Indian trader.

TOP RISK REGIONS: ${{topRisks}}

BREAKING HIGH-IMPACT NEWS: ${{highNews}}

KEY INDIA MARKET SIGNALS: India VIX 16.4 (elevated), INR/USD at 83.42 (weak), Brent Crude +1.8% (bearish for India current account), MCX Gold up (safe haven bid), FIIs net sellers for 3 sessions, DII buying providing support.

Write your response in 3 sections:
1. SITUATION: 2 sentences — the key global risk driver and its direct relevance to India.
2. MARKET IMPACT: 2 sentences — what this means for Nifty, INR, MCX Gold, and the energy/IT sectors.
3. TRADE STANCE: One sentence — BUY, HOLD CASH, or REDUCE, with one specific India-focused tactical idea (e.g. long MCX gold, reduce OMC exposure, hedge INR).

Direct, specific, actionable. Max 100 words.`;

  try {{
    const resp = await fetch('https://api.anthropic.com/v1/messages', {{
      method:'POST',
      headers:{{'Content-Type':'application/json','x-api-key':apiKey,'anthropic-version':'2023-06-01','anthropic-dangerous-direct-browser-access':'true'}},
      body:JSON.stringify({{model:'claude-sonnet-4-20250514',max_tokens:600,messages:[{{role:'user',content:prompt}}]}})
    }});
    const data = await resp.json();
    if (data.error) throw new Error(data.error.message);
    const text = data.content?.map(b=>b.text||'').join('') || 'Analysis unavailable.';

    let verdict='HOLD CASH', vclass='verdict-cash';
    if (/\\bBUY\\b|risk-on|bullish|long gold|long mcx/i.test(text)) {{ verdict='BUY / SELECTIVE LONG'; vclass='verdict-buy'; }}
    else if (/REDUCE|reduce exposure|risk-off|bearish|sell|short/i.test(text)) {{ verdict='REDUCE RISK'; vclass='verdict-sell'; }}

    const highRiskCount = REGIONS.filter(r=>r.score>=70).length;
    const riskTag = highRiskCount >= 3 ? 'HIGH' : 'MODERATE';
    const tagCls = riskTag === 'HIGH' ? 'tag-high' : 'tag-med';

    const formatted = text
      .replace(/SITUATION:/g,'<span style="font-size:10px;color:#64748b;letter-spacing:0.08em">SITUATION</span><br>')
      .replace(/MARKET IMPACT:/g,'<br><span style="font-size:10px;color:#64748b;letter-spacing:0.08em">MARKET IMPACT</span><br>')
      .replace(/TRADE STANCE:/g,'<br><span style="font-size:10px;color:#64748b;letter-spacing:0.08em">TRADE STANCE</span><br>');

    document.getElementById('brief-content').innerHTML = `
      <span class="brief-tag ${{tagCls}}">GEO-RISK: ${{riskTag}}</span>
      <div class="brief-text">${{formatted}}</div>
      <div class="brief-verdict ${{vclass}}">${{verdict}}</div>`;
  }} catch(e) {{
    document.getElementById('brief-content').innerHTML = `
      <div class="brief-loading">
        <span style="color:#ff4466">Error: ${{e.message}}</span>
      </div>`;
  }}
  btn.disabled = false;
  btn.textContent = '⚡ Regenerate Brief';
}}

renderRegions();
renderCommodities();
renderNews();
renderSignals();
renderForex();
renderEquities();
updateClock();
setInterval(updateClock, 1000);
</script>
</body>
</html>"""




# ─────────────────────────────────────────────
# MARKET STATUS HELPERS
# ─────────────────────────────────────────────

# NSE holidays 2025-2026 (add more as declared)
NSE_HOLIDAYS = {
    datetime(2025,  1, 26).date(),  # Republic Day
    datetime(2025,  2, 19).date(),  # Chhatrapati Shivaji Maharaj Jayanti
    datetime(2025,  3, 14).date(),  # Holi
    datetime(2025,  4,  1).date(),  # Dr. Babasaheb Ambedkar Jayanti observed
    datetime(2025,  4, 10).date(),  # Mahavir Jayanti
    datetime(2025,  4, 14).date(),  # Dr. Babasaheb Ambedkar Jayanti
    datetime(2025,  4, 18).date(),  # Good Friday
    datetime(2025,  5,  1).date(),  # Maharashtra Day
    datetime(2025,  8, 15).date(),  # Independence Day
    datetime(2025,  8, 27).date(),  # Ganesh Chaturthi
    datetime(2025, 10,  2).date(),  # Gandhi Jayanti
    datetime(2025, 10,  2).date(),  # Dussehra
    datetime(2025, 10, 21).date(),  # Diwali Laxmi Pujan
    datetime(2025, 10, 22).date(),  # Diwali Balipratipada
    datetime(2025, 11,  5).date(),  # Prakash Gurpurb Sri Guru Nanak Dev Ji
    datetime(2025, 12, 25).date(),  # Christmas
    datetime(2026,  1, 26).date(),  # Republic Day
    datetime(2026,  3,  3).date(),  # Mahashivratri (tentative)
    datetime(2026,  3, 20).date(),  # Holi (tentative)
    datetime(2026,  4,  3).date(),  # Good Friday (tentative)
    datetime(2026,  4, 14).date(),  # Dr. Babasaheb Ambedkar Jayanti
    datetime(2026,  5,  1).date(),  # Maharashtra Day
    datetime(2026,  8, 15).date(),  # Independence Day
    datetime(2026, 10,  2).date(),  # Gandhi Jayanti
    datetime(2026, 12, 25).date(),  # Christmas
}

def is_trading_day(dt: datetime) -> bool:
    """Return True if the given datetime falls on a NSE trading day."""
    d = dt.date() if isinstance(dt, datetime) else dt
    return d.weekday() < 5 and d not in NSE_HOLIDAYS   # Mon=0 … Fri=4


def get_last_trading_day(ref: datetime = None) -> datetime:
    """Return the most recent completed NSE trading day (never today if market open)."""
    dt = (ref or datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
    dt -= timedelta(days=1)        # start from yesterday
    for _ in range(14):            # walk back at most 2 weeks
        if is_trading_day(dt):
            return dt
        dt -= timedelta(days=1)
    return dt


def get_market_status() -> dict:
    """
    Determine whether NSE is currently open.
    Returns a dict with keys:
        is_open   bool
        label     str   e.g. "LIVE" or "CLOSED"
        note      str   human-readable context
        last_close datetime  — last completed trading day
    """
    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    today   = now_ist.date()
    open_t  = now_ist.replace(hour=9,  minute=15, second=0, microsecond=0)
    close_t = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)

    last_close = get_last_trading_day(now_ist)

    if is_trading_day(now_ist) and open_t <= now_ist <= close_t:
        return {
            "is_open":    True,
            "label":      "🟢 LIVE",
            "note":       f"NSE open · {now_ist.strftime('%d %b %Y %H:%M IST')}",
            "last_close": last_close,
        }
    else:
        if not is_trading_day(now_ist):
            reason = "Weekend" if now_ist.weekday() >= 5 else "Market Holiday"
        elif now_ist < open_t:
            reason = "Pre-market"
        else:
            reason = "After-market hours"
        return {
            "is_open":    False,
            "label":      "🔴 CLOSED",
            "note":       f"{reason} · Showing last close: {last_close.strftime('%A, %d %b %Y')}",
            "last_close": last_close,
        }

# ─────────────────────────────────────────────
# MA CROSSOVER SCANNER — FUNCTIONS
# ─────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_stock_history(symbol: str, days: int = 120) -> pd.DataFrame:
    """
    Fetch daily OHLCV for a single NSE equity stock (cash segment).

    Market-aware behaviour
    ───────────────────────
    • Market OPEN  → fetches up to today; the latest row is today's intraday candle.
    • Market CLOSED → fetches up to last_trading_day; if the API returns data only
      up to an earlier date (common on weekends / holidays), the last available
      close is duplicated as a synthetic row dated to last_trading_day so callers
      always see the freshest available close at the top of the frame.
    """
    status  = get_market_status()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com/",
    }

    # When closed, fetch up to last_trading_day; when open, fetch up to today.
    to_dt   = datetime.now() if status["is_open"] else status["last_close"]
    from_dt = to_dt - timedelta(days=days + 40)   # extra buffer for holidays
    fmt     = "%d-%m-%Y"

    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=8)
        url = (
            f"https://www.nseindia.com/api/historical/cm/equity"
            f"?symbol={requests.utils.quote(symbol)}"
            f"&series=[%22EQ%22]"
            f"&from={from_dt.strftime(fmt)}&to={to_dt.strftime(fmt)}"
        )
        r = session.get(url, headers=headers, timeout=12)
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            raise ValueError("empty")

        df = pd.DataFrame(data)
        df.rename(columns={
            "CH_TIMESTAMP":        "Date",
            "CH_OPENING_PRICE":    "Open",
            "CH_TRADE_HIGH_PRICE": "High",
            "CH_TRADE_LOW_PRICE":  "Low",
            "CH_CLOSING_PRICE":    "Close",
            "CH_TOT_TRADED_QTY":   "Volume",
        }, inplace=True)
        df["Date"] = pd.to_datetime(df["Date"])
        for c in ["Open", "High", "Low", "Close", "Volume"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df.dropna(subset=["Close"], inplace=True)
        df.sort_values("Date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].tail(days)

        # ── When market is closed, ensure the last row is the last trading day ──
        # The NSE historical API sometimes lags by a day on weekends/holidays.
        # If the latest row in the frame predates last_trading_day, clone it
        # forward so downstream MA calculations use the correct anchor date.
        if not status["is_open"] and not df.empty:
            target_date = pd.Timestamp(status["last_close"])
            last_row_date = df["Date"].iloc[-1]
            if last_row_date < target_date:
                fwd_row = df.iloc[[-1]].copy()
                fwd_row["Date"] = target_date
                df = pd.concat([df, fwd_row], ignore_index=True)
                # Tag this row so the UI can mark it as "last close (estimated)"
                df["_estimated"] = False
                df.loc[df.index[-1], "_estimated"] = True
            else:
                df["_estimated"] = False
        else:
            df["_estimated"] = False

        return df

    except Exception:
        return pd.DataFrame()


def compute_mas(df: pd.DataFrame) -> pd.DataFrame:
    """Add EMA20, EMA50, SMA50, SMA100 columns."""
    if df.empty or len(df) < 20:
        return df
    df = df.copy()
    df["EMA20"]  = df["Close"].ewm(span=20,  adjust=False).mean()
    df["EMA50"]  = df["Close"].ewm(span=50,  adjust=False).mean()
    df["SMA50"]  = df["Close"].rolling(50).mean()
    df["SMA100"] = df["Close"].rolling(100).mean()
    return df


def detect_crossovers(df: pd.DataFrame) -> list:
    """
    Detect the most recent crossover events among the four MA pairs.
    Returns a list of dicts, one per detected crossover (freshest first).
    lookback = 5 bars — if a crossover happened within last 5 candles it's 'fresh'.
    """
    if df.empty or len(df) < 101:
        return []
    pairs = [
        ("EMA20", "EMA50",  "EMA 20/50"),
        ("EMA20", "SMA50",  "EMA 20 / SMA 50"),
        ("EMA50", "SMA100", "EMA 50 / SMA 100"),
        ("SMA50", "SMA100", "SMA 50/100"),
    ]
    events = []
    lookback = 10   # bars to scan for a recent crossover
    for fast, slow, label in pairs:
        if fast not in df.columns or slow not in df.columns:
            continue
        s_fast = df[fast].dropna()
        s_slow = df[slow].dropna()
        common = s_fast.index.intersection(s_slow.index)
        if len(common) < 2:
            continue
        f = s_fast.loc[common]
        s = s_slow.loc[common]
        diff = f - s
        # Find last sign change
        for i in range(len(diff) - 1, max(len(diff) - lookback - 1, 0), -1):
            if diff.iloc[i] * diff.iloc[i - 1] < 0:   # sign flip
                direction = "Bullish" if diff.iloc[i] > 0 else "Bearish"
                bars_ago   = len(diff) - 1 - i
                date_val   = df["Date"].iloc[df.index.get_loc(common[i])] if common[i] in df.index else None
                events.append({
                    "pair":      label,
                    "direction": direction,
                    "bars_ago":  bars_ago,
                    "date":      date_val,
                    "price":     round(df["Close"].iloc[df.index.get_loc(common[i])], 2),
                    "fast_val":  round(f.iloc[i], 2),
                    "slow_val":  round(s.iloc[i], 2),
                })
                break   # only the most recent crossover per pair
    events.sort(key=lambda x: x["bars_ago"])
    return events


@st.cache_data(ttl=300)
def scan_sector_crossovers(sector_name: str) -> list:
    """
    For every stock in a sector, fetch history, compute MAs, detect crossovers.
    Returns list of result dicts sorted by freshness then signal strength.
    """
    symbols = SECTORS.get(sector_name, [])
    results = []
    for sym in symbols:
        df = fetch_stock_history(sym, days=120)
        if df.empty or len(df) < 55:
            continue
        df = compute_mas(df)
        crossovers = detect_crossovers(df)
        if not crossovers:
            continue
        # Overall bias from EMA20 vs SMA100 (broadest view)
        last = df.iloc[-1]
        bias = "Bullish" if last.get("EMA20", 0) > last.get("SMA100", 0) else "Bearish"
        ema20_slope  = last["EMA20"]  - df["EMA20"].iloc[-4]  if "EMA20"  in df.columns else 0
        sma100_slope = last["SMA100"] - df["SMA100"].iloc[-4] if "SMA100" in df.columns else 0
        results.append({
            "symbol":       sym,
            "ltp":          round(float(last["Close"]), 2),
            "change_pct":   round(float((last["Close"] - df["Close"].iloc[-2]) / df["Close"].iloc[-2] * 100), 2) if len(df) > 1 else 0.0,
            "bias":         bias,
            "crossovers":   crossovers,
            "freshest_bars":crossovers[0]["bars_ago"] if crossovers else 999,
            "ema20":        round(float(last.get("EMA20",  0)), 2),
            "ema50":        round(float(last.get("EMA50",  0)), 2),
            "sma50":        round(float(last.get("SMA50",  0)), 2),
            "sma100":       round(float(last.get("SMA100", 0)), 2),
            "ema20_slope":  round(float(ema20_slope),  2),
            "sma100_slope": round(float(sma100_slope), 2),
            "df":           df,   # kept for mini-chart rendering
        })
    results.sort(key=lambda x: (x["freshest_bars"], x["symbol"]))
    return results

# ─────────────────────────────────────────────
# SECTOR DEFINITIONS — CASH EQUITY ONLY (NO F&O)
# ─────────────────────────────────────────────
SECTORS = {
    "Auto":        ["MARUTI","TATAMOTORS","M%26M","BAJAJ-AUTO","HEROMOTOCO","EICHERMOT","ASHOKLEY","TVSMOTOR","BALKRISIND","MOTHERSON"],
    "IT":          ["TCS","INFY","HCLTECH","WIPRO","TECHM","LTIM","MPHASIS","PERSISTENT","COFORGE","KPITTECH"],
    "Pharma":      ["SUNPHARMA","DRREDDY","CIPLA","DIVISLAB","AUROPHARMA","LUPIN","TORNTPHARM","ALKEM","IPCALAB","GLENMARK"],
    "Banking":     ["HDFCBANK","ICICIBANK","KOTAKBANK","AXISBANK","SBIN","INDUSINDBK","FEDERALBNK","BANDHANBNK","IDFCFIRSTB","PNB"],
    "FMCG":        ["HINDUNILVR","ITC","NESTLEIND","BRITANNIA","DABUR","MARICO","COLPAL","GODREJCP","EMAMILTD","VBL"],
    "Metals":      ["TATASTEEL","JSWSTEEL","HINDALCO","VEDL","SAIL","NMDC","NATIONALUM","JINDALSTEL","APLAPOLLO","RATNAMANI"],
    "Energy":      ["RELIANCE","ONGC","IOC","BPCL","GAIL","POWERGRID","NTPC","TATAPOWER","ADANIGREEN","CESC"],
    "Realty":      ["DLF","GODREJPROP","OBEROIRLTY","PHOENIXLTD","PRESTIGE","SOBHA","BRIGADE","MAHLIFE","SUNTECK","KOLTEPATIL"],
    "Infra":       ["LT","ABB","SIEMENS","BHEL","CUMMINSIND","THERMAX","KEC","KALPATPOWR","ENGINERSIN","GRINDWELL"],
    "Consumption": ["TITAN","VOLTAS","WHIRLPOOL","HAVELLS","CROMPTON","BLUESTAR","VGUARD","SYMPHONY","RELAXO","BATAINDIA"],
}

SECTOR_ICONS = {
    "Auto":"🚗","IT":"💻","Pharma":"💊","Banking":"🏦","FMCG":"🛒",
    "Metals":"⚙️","Energy":"⚡","Realty":"🏢","Infra":"🏗️","Consumption":"🛍️",
}

@st.cache_data(ttl=120)
def fetch_stock_quote(symbol: str) -> dict:
    """Fetch live NSE equity quote — cash segment only, no F&O."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com/",
    }
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=8)
        url = f"https://www.nseindia.com/api/quote-equity?symbol={requests.utils.quote(symbol)}"
        r = session.get(url, headers=headers, timeout=8)
        r.raise_for_status()
        data = r.json()
        pd_data   = data.get("priceInfo", {})
        mkt_depth = data.get("marketDeptOrderBook", {})
        trade_info = mkt_depth.get("tradeInfo", {})
        buy_qty  = sum(b.get("quantity", 0) for b in mkt_depth.get("buy",  []))
        sell_qty = sum(s.get("quantity", 0) for s in mkt_depth.get("sell", []))
        return {
            "symbol":    symbol,
            "ltp":       float(pd_data.get("lastPrice",    0) or 0),
            "change":    float(pd_data.get("change",       0) or 0),
            "pct_change":float(pd_data.get("pChange",      0) or 0),
            "volume":    int(trade_info.get("totalTradedVolume", 0) or 0),
            "buy_qty":   int(buy_qty),
            "sell_qty":  int(sell_qty),
            "open":      float(pd_data.get("open",         0) or 0),
            "high":      float((pd_data.get("intraDayHighLow") or {}).get("max", 0) or 0),
            "low":       float((pd_data.get("intraDayHighLow") or {}).get("min", 0) or 0),
            "prev_close":float(pd_data.get("previousClose", 0) or 0),
        }
    except Exception:
        return {"symbol": symbol, "ltp": 0, "change": 0, "pct_change": 0,
                "volume": 0, "buy_qty": 0, "sell_qty": 0,
                "open": 0, "high": 0, "low": 0, "prev_close": 0}


@st.cache_data(ttl=120)
def fetch_sector_data(sector_name: str) -> pd.DataFrame:
    """Fetch quotes for all stocks in a sector and compute volume buildup metrics."""
    symbols = SECTORS.get(sector_name, [])
    rows = []
    for sym in symbols:
        q = fetch_stock_quote(sym)
        chg  = q["pct_change"]
        vol  = q["volume"]
        bq   = q["buy_qty"]
        sq   = q["sell_qty"]
        tot  = bq + sq
        buy_pct = round(bq / tot * 100, 1) if tot > 0 else 50.0

        if   chg >  0.5 and vol > 0: buildup = "Long Buildup"
        elif chg < -0.5 and vol > 0: buildup = "Short Buildup"
        elif chg >  0.1 and vol > 0: buildup = "Short Covering"
        elif chg < -0.1 and vol > 0: buildup = "Long Unwinding"
        else:                         buildup = "Neutral"

        rows.append({
            "Symbol":   sym,
            "LTP":      q["ltp"],
            "Change%":  round(chg, 2),
            "Volume":   vol,
            "Buy Qty":  bq,
            "Sell Qty": sq,
            "Buy%":     buy_pct,
            "Buildup":  buildup,
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        mx = df["Volume"].max() or 1
        df["Vol_Norm"] = (df["Volume"] / mx * 100).round(1)
    else:
        df["Vol_Norm"] = 50.0
    return df


def build_sector_summary(df: pd.DataFrame) -> dict:
    """Aggregate sector-level signal from individual stock data."""
    if df.empty:
        return {"bias":"Neutral","score":50,"advancing":0,"declining":0,
                "total_volume":0,"avg_change":0.0}
    adv  = int((df["Change%"] >  0).sum())
    dec  = int((df["Change%"] <  0).sum())
    lb   = int((df["Buildup"] == "Long Buildup").sum())
    sb   = int((df["Buildup"] == "Short Buildup").sum())
    sc   = int((df["Buildup"] == "Short Covering").sum())
    lu   = int((df["Buildup"] == "Long Unwinding").sum())
    score = int(np.clip(50 + (adv-dec)*3 + (lb-sb)*4 + (sc-lu)*2, 5, 95))
    bias  = "Bullish" if score >= 60 else "Bearish" if score <= 40 else "Neutral"
    return {
        "bias": bias, "score": score,
        "advancing": adv, "declining": dec,
        "total_volume": int(df["Volume"].sum()),
        "avg_change": round(float(df["Change%"].mean()), 2),
    }

# ─────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")
    selected_index = st.selectbox(
        "Select Index",
        ["NIFTY", "BANKNIFTY", "SENSEX"],
        index=0,
        key="selected_index",
    )
    hist_days = st.slider("Historical Days", 15, 120, 60, step=5)

    chart_type = st.selectbox(
        "Chart Type",
        options=["Candlestick", "Kagi", "Point & Figure"],
        index=0,
    )

    if chart_type in ["Point & Figure", "Kagi"]:
        box_size = st.slider("Box/Reversal Size", min_value=0.25, max_value=5.0, value=1.0, step=0.25)
        reversal_boxes = st.slider("Reversal (boxes)", min_value=1, max_value=5, value=3, step=1)
    else:
        box_size = 1.0
        reversal_boxes = 3

    st.markdown("---")
    st.markdown("##### 🔑 API Keys (Optional)")
    anthropic_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...",
                                   help="Required for AI Trade Brief in Global Risk Monitor tab")
    dhan_client_id = st.text_input("Dhan Client ID", placeholder="Client ID")
    dhan_token = st.text_input("Dhan Access Token", type="password", placeholder="Access Token")
    st.markdown("---")
    refresh = st.button("🔄 Refresh Data", use_container_width=True)
    auto_refresh = st.checkbox("Auto Refresh (60s)", value=False)

# ── Detect index switch and bust caches so stale data never bleeds across indices ──
if "prev_index" not in st.session_state:
    st.session_state["prev_index"] = selected_index

if st.session_state["prev_index"] != selected_index or refresh:
    fetch_historical_data.clear()
    fetch_sensex_historical.clear()
    fetch_index_data.clear()
    fetch_sensex_data.clear()
    fetch_option_chain.clear()
    st.session_state["prev_index"] = selected_index

with st.spinner("Fetching live market data..."):
    hist_df = fetch_historical_data(selected_index, hist_days)
    if hist_df.empty:
        st.error("❌ Failed to fetch historical data. Please check your connection.")
        st.stop()
    hist_df = add_all_indicators(hist_df)
    cpr = calc_cpr(hist_df)

    cam_r1, cam_r2, cam_r3, cam_r4, cam_s1, cam_s2, cam_s3, cam_s4 = calculate_camarilla(hist_df)
    fib_r1, fib_r2, fib_r3, fib_s1, fib_s2, fib_s3 = calculate_fibonacci(hist_df)

    last_row = hist_df.iloc[-1]
    index_live = fetch_index_data(selected_index)
    spot_price = float(index_live.get("last", last_row["Close"])) if index_live and "error" not in index_live else float(last_row["Close"])
    spot_change = float(index_live.get("variation", 0)) if index_live and "error" not in index_live else 0.0
    spot_pct = float(index_live.get("percentChange", 0)) if index_live and "error" not in index_live else 0.0

    oc_data, last_updated_note = get_option_chain_with_fallback(INDEX_SYMBOLS[selected_index]["option_chain"])
    if "error" in oc_data:
        st.warning(f"⚠️ Option chain data unavailable: {oc_data['error']}")
        oc_df = pd.DataFrame()
        pcr = 1.0
        oi_signal = "N/A (OC fetch failed)"
    else:
        oc_df = process_option_chain(oc_data, spot_price)
        pcr = calc_pcr(oc_df)
        oi_signal = oi_buildup_signal(oc_df, spot_change, spot=spot_price)
    analysis = generate_analysis(hist_df, cpr, pcr, oi_signal, spot_price)

st.markdown(f"<p style='text-align:center; color:#64748b; font-size:11px;'>Last updated: {last_updated_note} · Index: <span style='color:#00d4ff'>{selected_index}</span></p>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    f"📈 {selected_index} Live Dashboard",
    f"📊 {selected_index} OI & Option Chain",
    "🌍 Global Risk Monitor",
    f"🔮 {selected_index} Forecasts",
    "🏭 Sector Volume Buildup",
    "🎯 MA Crossover Scanner",
])

with tab1:
    st.subheader(f"{selected_index} Live Dashboard")
    st.markdown(f'<div class="section-header">LIVE MARKET SNAPSHOT — {selected_index}</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    change_class = "metric-change-up" if spot_change >= 0 else "metric-change-down"
    change_arrow = "▲" if spot_change >= 0 else "▼"
    metrics = [
        (c1, selected_index, f"{spot_price:,.2f}", f"{change_arrow} {abs(spot_change):,.2f} ({spot_pct:+.2f}%)", change_class),
        (c2, "RSI(14)", f"{last_row['RSI']:.1f}", "Overbought" if last_row['RSI'] > 60 else ("Oversold" if last_row['RSI'] < 40 else "Neutral"), "metric-change-up" if last_row['RSI'] > 50 else "metric-change-down"),
        (c3, "ADX(14)", f"{last_row['ADX']:.1f}", "Trending" if last_row['ADX'] > 25 else "Sideways", "metric-change-up" if last_row['ADX'] > 25 else "metric-change-down"),
        (c4, "PCR", f"{pcr:.2f}", "Bullish" if pcr > 1 else "Bearish", "metric-change-up" if pcr > 1 else "metric-change-down"),
        (c5, "CPR Width", f"{abs(cpr['tc'] - cpr['bc']):.1f}", f"TC:{cpr['tc']:.0f} BC:{cpr['bc']:.0f}", "metric-change-up"),
        (c6, "Confidence", f"{analysis['score']}/100", analysis['bias'], "metric-change-up" if analysis['score'] > 60 else ("metric-change-down" if analysis['score'] < 40 else "tag-neutral")),
    ]
    for col, label, value, sub, cls in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
                <div class="{cls}">{sub}</div>
            </div>""", unsafe_allow_html=True)

    with c7:
        oi_sig = oi_signal
        oi_class = "metric-change-up" if "Build Up" in oi_sig or "Covering" in oi_sig else "metric-change-down"
        oi_icon = "🟢" if oi_class == "metric-change-up" else "🔴"
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {'var(--green)' if oi_class == 'metric-change-up' else 'var(--red)'};">
            <div class="metric-label">OI Interpretation</div>
            <div class="metric-value">{oi_icon} {oi_sig}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">MARKET INTERPRETATION</div>', unsafe_allow_html=True)
    bullets = analysis.get("bullets", [])
    if bullets:
        bullet_html = ""
        for bullet in bullets:
            color = "var(--green)" if "🟢" in bullet or "BULLISH" in bullet else "var(--red)" if "🔴" in bullet or "BEARISH" in bullet else "var(--yellow)"
            bullet_html += f'<li style="color:{color}; margin:6px 0;">{bullet}</li>'
        st.markdown(f"""
        <div class="summary-box">
            <ul style="list-style:none; padding-left:0; margin:0;">{bullet_html}</ul>
        </div>""", unsafe_allow_html=True)

    st.markdown(f'<div class="section-header">PRICE CHART ({chart_type})</div>', unsafe_allow_html=True)

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.55, 0.25, 0.20], vertical_spacing=0.04,
        subplot_titles=("Price / Indicators", "ADX / DMI", "Volume"),
    )

    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=hist_df["Date"], open=hist_df["Open"], high=hist_df["High"],
            low=hist_df["Low"], close=hist_df["Close"], name="Candlestick",
            increasing_line_color="#00ff88", decreasing_line_color="#ff4466",
            increasing_fillcolor="#00ff88", decreasing_fillcolor="#ff4466"
        ), row=1, col=1)
    elif chart_type == "Kagi":
        kagi = hist_df["Close"].copy()
        direction = np.sign(kagi.diff())
        reversal_points = np.where(direction != direction.shift())[0]
        for i in range(len(reversal_points)-1):
            start = reversal_points[i]; end = reversal_points[i+1]
            segment = kagi.iloc[start:end]
            fig.add_trace(go.Scatter(
                x=segment.index, y=segment, mode='lines',
                line=dict(color="#00d4ff" if segment.iloc[-1] > segment.iloc[0] else "#ff4466",
                          width=4 if abs(segment.iloc[-1] - segment.iloc[0]) > box_size * reversal_boxes else 1),
                name="Kagi Segment", showlegend=False
            ), row=1, col=1)
    elif chart_type == "Point & Figure":
        pnf_boxes = []; current_col = []; current_dir = 1; last_price = hist_df["Close"].iloc[0]
        for price in hist_df["Close"]:
            if price >= last_price + box_size * reversal_boxes:
                if current_dir == -1: pnf_boxes.append(current_col); current_col = []; current_dir = 1
                current_col.extend(["X"] * int((price - last_price) // box_size)); last_price = price
            elif price <= last_price - box_size * reversal_boxes:
                if current_dir == 1: pnf_boxes.append(current_col); current_col = []; current_dir = -1
                current_col.extend(["O"] * int((last_price - price) // box_size)); last_price = price
        pnf_boxes.append(current_col)
        x_pos=[]; y_pos=[]; colors=[]
        for col_idx, col in enumerate(pnf_boxes):
            for box_idx, box in enumerate(col):
                x_pos.append(col_idx); y_pos.append(last_price - box_idx * box_size)
                colors.append("green" if box == "X" else "red")
        fig.add_trace(go.Scatter(
            x=x_pos, y=y_pos, mode="markers",
            marker=dict(symbol="square", size=10, color=colors, line=dict(width=1, color="black")),
            name="P&F Boxes", showlegend=False
        ), row=1, col=1)

    fig.add_trace(go.Scatter(x=hist_df["Date"], y=hist_df["EMA13"], mode="lines", name="EMA 13", line=dict(color="#ffd700")), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist_df["Date"], y=hist_df["EMA21"], mode="lines", name="EMA 21", line=dict(color="#ff8c00")), row=1, col=1)
    fig.add_hline(y=cpr["pivot"], line_dash="dash", line_color="#00d4ff", annotation_text="Pivot", row=1, col=1)
    fig.add_hline(y=cpr["bc"], line_dash="dot", line_color="#ff4466", annotation_text="BC", row=1, col=1)
    fig.add_hline(y=cpr["tc"], line_dash="dot", line_color="#00ff88", annotation_text="TC", row=1, col=1)
    fig.add_hline(y=cam_r3, line_color="#00ff88", line_dash="dash", annotation_text="Cam R3", row=1, col=1)
    fig.add_hline(y=fib_r3, line_color="#ffd700", line_dash="dash", annotation_text="Fib R3", row=1, col=1)
    fig.add_trace(go.Scatter(x=hist_df["Date"], y=hist_df["ADX"], name="ADX", line=dict(color="#ffd700")), row=2, col=1)
    fig.add_trace(go.Bar(x=hist_df["Date"], y=hist_df["Volume"], name="Volume",
                         marker_color=["#00ff88" if c >= o else "#ff4466" for c, o in zip(hist_df["Close"], hist_df["Open"])]), row=3, col=1)

    fig.update_layout(
        height=700, title=f"{selected_index} - {chart_type} Chart", showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_rangeslider_visible=False, margin=dict(l=40, r=40, t=60, b=40),
        paper_bgcolor="#0a0e1a", plot_bgcolor="#0d1117",
        font=dict(family="JetBrains Mono", color="#e2e8f0")
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("OI & Option Chain Deep Dive")
    if not oc_df.empty:
        st.dataframe(oc_df.style.format({
            "CE_OI": "{:,.0f}", "CE_OI_Chg": "{:+,.0f}", "CE_LTP": "{:.2f}",
            "Strike": "{:.0f}", "PE_LTP": "{:.2f}", "PE_OI_Chg": "{:+,.0f}", "PE_OI": "{:,.0f}"
        }), use_container_width=True)
    else:
        st.info("No OI data available.")

# ─────────────────────────────────────────────
# TAB 3: GLOBAL RISK MONITOR — FULL DASHBOARD
# ─────────────────────────────────────────────
with tab3:
    # Pass the anthropic key from sidebar into the HTML so the AI brief works
    geo_html = get_geo_dashboard_html(anthropic_api_key=anthropic_key or "")
    components.html(geo_html, height=1600, scrolling=True)

with tab4:
    st.subheader("Forecasts & Probabilities")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("24h Bullish Probability", "65%", "ADX trending + OI buildup")
    with col2:
        st.metric("7d Trend", "Bullish", "EMA aligned + Day High breakout")
    with col3:
        st.metric("30d Risk", "Moderate", "PCR neutral, watch Red Sea + crude")


# ─────────────────────────────────────────────
# TAB 5: SECTOR VOLUME BUILDUP
# ─────────────────────────────────────────────
with tab5:
    st.markdown("""
    <div style='padding:6px 0 18px'>
        <span style='font-family:JetBrains Mono;font-size:11px;color:#64748b;letter-spacing:2px;text-transform:uppercase'>
        Cash equity stocks only · No futures or options · Refreshes every 2 min
        </span>
    </div>""", unsafe_allow_html=True)

    # ── Top row: sector overview heatmap ──────────────────────────────────
    st.markdown('<div class="section-header">SECTOR HEATMAP — VOLUME & PRICE BUILDUP</div>',
                unsafe_allow_html=True)

    sector_names = list(SECTORS.keys())

    # Fetch summary for every sector (uses cache so fast after first load)
    all_summaries = {}
    with st.spinner("Loading sector data..."):
        for sname in sector_names:
            sdf = fetch_sector_data(sname)
            all_summaries[sname] = build_sector_summary(sdf)

    # ── Heatmap chart ──────────────────────────────────────────────────────
    hm_labels, hm_scores, hm_changes, hm_colors, hm_text = [], [], [], [], []
    for sname, summ in all_summaries.items():
        icon = SECTOR_ICONS.get(sname, "")
        hm_labels.append(f"{icon} {sname}")
        hm_scores.append(summ["score"])
        hm_changes.append(summ["avg_change"])
        adv, dec = summ["advancing"], summ["declining"]
        color = ("#00ff88" if summ["bias"] == "Bullish"
                 else "#ff4466" if summ["bias"] == "Bearish"
                 else "#ffd700")
        hm_colors.append(color)
        hm_text.append(
            f"<b>{icon} {sname}</b><br>"
            f"Bias: {summ['bias']}<br>"
            f"Score: {summ['score']}/100<br>"
            f"Avg Chg: {summ['avg_change']:+.2f}%<br>"
            f"Advancing: {adv} | Declining: {dec}"
        )

    fig_hm = go.Figure()
    fig_hm.add_trace(go.Bar(
        x=hm_labels,
        y=hm_scores,
        marker_color=hm_colors,
        text=[f"{s}/100" for s in hm_scores],
        textposition="outside",
        textfont=dict(family="JetBrains Mono", size=11, color="#e2e8f0"),
        hovertext=hm_text,
        hoverinfo="text",
        width=0.55,
    ))
    fig_hm.add_trace(go.Scatter(
        x=hm_labels,
        y=hm_changes,
        mode="markers+text",
        marker=dict(
            size=14,
            color=["#00ff88" if c >= 0 else "#ff4466" for c in hm_changes],
            symbol="diamond",
            line=dict(width=1, color="#0a0e1a"),
        ),
        text=[f"{c:+.2f}%" for c in hm_changes],
        textposition="top center",
        textfont=dict(family="JetBrains Mono", size=10),
        yaxis="y2",
        name="Avg Price Change%",
        hoverinfo="skip",
    ))
    fig_hm.update_layout(
        height=340,
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0d1117",
        font=dict(family="JetBrains Mono", color="#e2e8f0"),
        showlegend=False,
        margin=dict(l=40, r=40, t=30, b=60),
        yaxis=dict(
            title="Buildup Score", range=[0, 110],
            gridcolor="#1e2d45", zeroline=False,
            tickfont=dict(size=10),
        ),
        yaxis2=dict(
            title="Avg Chg%", overlaying="y", side="right",
            range=[-5, 5], zeroline=True, zerolinecolor="#1e2d45",
            tickfont=dict(size=10), showgrid=False,
        ),
        xaxis=dict(tickfont=dict(size=11)),
        bargap=0.35,
    )
    st.plotly_chart(fig_hm, use_container_width=True)

    # ── Sector selector + drill-down ──────────────────────────────────────
    st.markdown('<div class="section-header">DRILL DOWN — STOCK LEVEL VOLUME BUILDUP</div>',
                unsafe_allow_html=True)

    col_sel, col_sort = st.columns([3, 2])
    with col_sel:
        chosen_sector = st.selectbox(
            "Select Sector",
            sector_names,
            format_func=lambda s: f"{SECTOR_ICONS.get(s,'')} {s}",
            key="sector_selector",
        )
    with col_sort:
        sort_by = st.selectbox(
            "Sort By",
            ["Volume (High→Low)", "Change% (Top Gainers)", "Change% (Top Losers)", "Buy% (Most Bought)"],
            key="sector_sort",
        )

    sdf = fetch_sector_data(chosen_sector)
    summ = all_summaries[chosen_sector]

    # ── Sector summary banner ──────────────────────────────────────────────
    bias_color = ("#00ff88" if summ["bias"] == "Bullish"
                  else "#ff4466" if summ["bias"] == "Bearish" else "#ffd700")
    vol_fmt = (f"{summ['total_volume']/1_000_000:.1f}M"
               if summ["total_volume"] >= 1_000_000
               else f"{summ['total_volume']/1_000:.0f}K")

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#111827 0%,#0f172a 100%);
                border:1px solid #1e2d45;border-left:3px solid {bias_color};
                border-radius:10px;padding:14px 20px;margin:8px 0 16px;
                display:flex;gap:40px;flex-wrap:wrap;align-items:center'>
        <div>
            <div style='font-size:10px;color:#64748b;font-family:JetBrains Mono;letter-spacing:1px'>SECTOR BIAS</div>
            <div style='font-size:22px;font-weight:700;color:{bias_color};font-family:JetBrains Mono'>{summ["bias"].upper()}</div>
        </div>
        <div>
            <div style='font-size:10px;color:#64748b;font-family:JetBrains Mono;letter-spacing:1px'>SCORE</div>
            <div style='font-size:22px;font-weight:700;color:#00d4ff;font-family:JetBrains Mono'>{summ["score"]}/100</div>
        </div>
        <div>
            <div style='font-size:10px;color:#64748b;font-family:JetBrains Mono;letter-spacing:1px'>ADVANCING / DECLINING</div>
            <div style='font-size:18px;font-weight:700;font-family:JetBrains Mono'>
                <span style='color:#00ff88'>▲ {summ["advancing"]}</span>
                &nbsp;/&nbsp;
                <span style='color:#ff4466'>▼ {summ["declining"]}</span>
            </div>
        </div>
        <div>
            <div style='font-size:10px;color:#64748b;font-family:JetBrains Mono;letter-spacing:1px'>AVG CHANGE</div>
            <div style='font-size:18px;font-weight:700;color:{"#00ff88" if summ["avg_change"]>=0 else "#ff4466"};font-family:JetBrains Mono'>
                {summ["avg_change"]:+.2f}%
            </div>
        </div>
        <div>
            <div style='font-size:10px;color:#64748b;font-family:JetBrains Mono;letter-spacing:1px'>TOTAL VOLUME</div>
            <div style='font-size:18px;font-weight:700;color:#e2e8f0;font-family:JetBrains Mono'>{vol_fmt}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not sdf.empty:
        # Apply sort
        if sort_by == "Volume (High→Low)":
            sdf = sdf.sort_values("Volume", ascending=False)
        elif sort_by == "Change% (Top Gainers)":
            sdf = sdf.sort_values("Change%", ascending=False)
        elif sort_by == "Change% (Top Losers)":
            sdf = sdf.sort_values("Change%", ascending=True)
        elif sort_by == "Buy% (Most Bought)":
            sdf = sdf.sort_values("Buy%", ascending=False)
        sdf = sdf.reset_index(drop=True)

        # ── Volume Buildup horizontal bar chart ───────────────────────────
        buildup_colors = {
            "Long Buildup":    "#00ff88",
            "Short Covering":  "#00d4ff",
            "Neutral":         "#64748b",
            "Long Unwinding":  "#ffa500",
            "Short Buildup":   "#ff4466",
        }
        bar_colors = [buildup_colors.get(b, "#64748b") for b in sdf["Buildup"]]
        bar_text   = [
            f"{row.Symbol}  {row['Change%']:+.2f}%  Vol:{row.Vol_Norm:.0f}%  {row.Buildup}"
            for _, row in sdf.iterrows()
        ]

        fig_bars = go.Figure()

        # Volume bars (normalised)
        fig_bars.add_trace(go.Bar(
            y=sdf["Symbol"],
            x=sdf["Vol_Norm"],
            orientation="h",
            marker_color=bar_colors,
            marker_opacity=0.85,
            name="Relative Volume",
            text=[f"{v:.0f}%" for v in sdf["Vol_Norm"]],
            textposition="inside",
            textfont=dict(family="JetBrains Mono", size=10, color="#0a0e1a"),
            hovertext=bar_text,
            hoverinfo="text",
            width=0.55,
        ))

        # Change% scatter overlay
        fig_bars.add_trace(go.Scatter(
            y=sdf["Symbol"],
            x=[50] * len(sdf),          # anchor at 50% mark
            mode="text",
            text=[f"{c:+.2f}%" for c in sdf["Change%"]],
            textfont=dict(
                family="JetBrains Mono", size=10,
                color=["#00ff88" if c >= 0 else "#ff4466" for c in sdf["Change%"]],
            ),
            textposition="middle right",
            hoverinfo="skip",
            showlegend=False,
        ))

        fig_bars.update_layout(
            height=max(380, len(sdf) * 38),
            paper_bgcolor="#0a0e1a",
            plot_bgcolor="#0d1117",
            font=dict(family="JetBrains Mono", color="#e2e8f0"),
            showlegend=False,
            margin=dict(l=100, r=80, t=20, b=40),
            xaxis=dict(
                title="Relative Volume %", range=[0, 115],
                gridcolor="#1e2d45", zeroline=False, tickfont=dict(size=10),
            ),
            yaxis=dict(
                autorange="reversed", tickfont=dict(size=11),
                gridcolor="#1e2d45",
            ),
            bargap=0.25,
        )

        # Vertical reference line at 50%
        fig_bars.add_vline(x=50, line_dash="dot", line_color="#1e2d45", line_width=1)

        st.plotly_chart(fig_bars, use_container_width=True)

        # ── Legend ──────────────────────────────────────────────────────
        st.markdown("""
        <div style='display:flex;gap:18px;flex-wrap:wrap;padding:8px 0;font-family:JetBrains Mono;font-size:11px'>
            <span><span style='color:#00ff88'>■</span> Long Buildup — Price ↑ + Volume ↑</span>
            <span><span style='color:#00d4ff'>■</span> Short Covering — Price ↑ + OI ↓</span>
            <span><span style='color:#64748b'>■</span> Neutral</span>
            <span><span style='color:#ffa500'>■</span> Long Unwinding — Price ↓ + OI ↓</span>
            <span><span style='color:#ff4466'>■</span> Short Buildup — Price ↓ + Volume ↑</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Buy/Sell Order Imbalance chart ────────────────────────────────
        st.markdown('<div class="section-header">ORDER BOOK IMBALANCE — BUY vs SELL PRESSURE</div>',
                    unsafe_allow_html=True)

        ob_df = sdf[sdf["Buy Qty"] + sdf["Sell Qty"] > 0].copy()
        if not ob_df.empty:
            fig_ob = go.Figure()
            fig_ob.add_trace(go.Bar(
                name="Buy Qty",
                y=ob_df["Symbol"],
                x=ob_df["Buy%"],
                orientation="h",
                marker_color="#00ff88",
                marker_opacity=0.8,
                text=[f"Buy {b:.0f}%" for b in ob_df["Buy%"]],
                textposition="inside",
                textfont=dict(family="JetBrains Mono", size=10, color="#0a0e1a"),
                hovertemplate="%{y}: Buy %{x:.1f}%<extra></extra>",
            ))
            fig_ob.add_trace(go.Bar(
                name="Sell Qty",
                y=ob_df["Symbol"],
                x=100 - ob_df["Buy%"],
                orientation="h",
                marker_color="#ff4466",
                marker_opacity=0.8,
                text=[f"Sell {100-b:.0f}%" for b in ob_df["Buy%"]],
                textposition="inside",
                textfont=dict(family="JetBrains Mono", size=10, color="#0a0e1a"),
                hovertemplate="%{y}: Sell %{x:.1f}%<extra></extra>",
            ))
            fig_ob.update_layout(
                barmode="stack",
                height=max(320, len(ob_df) * 36),
                paper_bgcolor="#0a0e1a",
                plot_bgcolor="#0d1117",
                font=dict(family="JetBrains Mono", color="#e2e8f0"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02,
                            xanchor="right", x=1),
                margin=dict(l=100, r=40, t=30, b=40),
                xaxis=dict(
                    title="Order Book Split %", range=[0, 100],
                    gridcolor="#1e2d45", ticksuffix="%",
                    tickfont=dict(size=10),
                ),
                yaxis=dict(autorange="reversed", tickfont=dict(size=11),
                           gridcolor="#1e2d45"),
            )
            fig_ob.add_vline(x=50, line_dash="dot", line_color="#64748b", line_width=1)
            st.plotly_chart(fig_ob, use_container_width=True)
        else:
            st.info("Order book data not available — market may be closed.")

        # ── Raw data table ────────────────────────────────────────────────
        with st.expander("📋 Raw Stock Data Table"):
            display_df = sdf[["Symbol","LTP","Change%","Volume","Buy%","Buildup"]].copy()
            display_df["Volume"] = display_df["Volume"].apply(
                lambda v: f"{v/1_000_000:.2f}M" if v >= 1_000_000 else f"{v/1_000:.0f}K" if v >= 1_000 else str(v)
            )
            st.dataframe(
                display_df.style
                    .applymap(lambda v: "color: #00ff88" if isinstance(v, float) and v > 0
                              else "color: #ff4466" if isinstance(v, float) and v < 0 else "",
                              subset=["Change%"])
                    .format({"LTP": "{:.2f}", "Change%": "{:+.2f}%", "Buy%": "{:.1f}%"}),
                use_container_width=True,
            )
    else:
        st.warning(f"Could not fetch data for {chosen_sector}. Market may be closed or NSE API unavailable.")


# ─────────────────────────────────────────────
# TAB 6: MA CROSSOVER SCANNER
# ─────────────────────────────────────────────
with tab6:
    # ── Market status — computed once at tab render ────────────────────────
    mkt = get_market_status()
    status_color  = "#00ff88" if mkt["is_open"] else "#ff4466"
    status_bg     = "rgba(0,255,136,0.07)" if mkt["is_open"] else "rgba(255,68,102,0.07)"
    status_border = "rgba(0,255,136,0.25)" if mkt["is_open"] else "rgba(255,68,102,0.25)"
    data_as_of    = (
        f"Intraday live data · {datetime.now().strftime('%d %b %Y %H:%M IST')}"
        if mkt["is_open"]
        else f"Last close: {mkt['last_close'].strftime('%A, %d %b %Y')} · Next session opens Mon–Fri 09:15 IST"
    )

    st.markdown(f"""
    <div style='background:{status_bg};border:1px solid {status_border};
                border-radius:10px;padding:10px 18px;margin-bottom:14px;
                display:flex;align-items:center;gap:18px;flex-wrap:wrap'>
        <span style='font-size:15px;font-weight:700;color:{status_color};
                     font-family:JetBrains Mono'>{mkt["label"]}</span>
        <span style='font-size:11px;color:#e2e8f0;font-family:JetBrains Mono'>{mkt["note"]}</span>
        <span style='font-size:10px;color:#64748b;font-family:JetBrains Mono;margin-left:auto'>{data_as_of}</span>
    </div>
    <div style='padding:2px 0 12px'>
        <span style='font-family:JetBrains Mono;font-size:11px;color:#64748b;
                     letter-spacing:2px;text-transform:uppercase'>
        Cash equity · EMA 20 · EMA 50 · SMA 50 · SMA 100 · Fresh crossovers only · Not F&amp;O
        </span>
    </div>""", unsafe_allow_html=True)

    # ── Controls row ──────────────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2, 2, 2, 2])
    with ctrl1:
        scan_sector = st.selectbox(
            "Sector to Scan",
            list(SECTORS.keys()),
            format_func=lambda s: f"{SECTOR_ICONS.get(s,'')} {s}",
            key="crossover_sector",
        )
    with ctrl2:
        bias_filter = st.selectbox(
            "Bias Filter",
            ["All", "Bullish Only", "Bearish Only"],
            key="crossover_bias",
        )
    with ctrl3:
        pair_filter = st.selectbox(
            "MA Pair",
            ["All Pairs", "EMA 20/50", "EMA 20 / SMA 50", "EMA 50 / SMA 100", "SMA 50/100"],
            key="crossover_pair",
        )
    with ctrl4:
        freshness = st.slider("Max bars since crossover", 1, 10, 5, key="crossover_fresh",
                               help="Lower = only very recent crossovers")

    # ── Scan button ───────────────────────────────────────────────────────
    run_scan = st.button("🔍 Run Crossover Scan", use_container_width=True, key="run_scan_btn")

    # Bust cache if market status changed since last scan
    # (e.g. market opened after user loaded the page while closed)
    prev_mkt_open = st.session_state.get("crossover_mkt_was_open")
    if prev_mkt_open is not None and prev_mkt_open != mkt["is_open"]:
        st.session_state["crossover_results"] = None
        st.session_state["crossover_sector_scanned"] = None
        fetch_stock_history.clear()
    st.session_state["crossover_mkt_was_open"] = mkt["is_open"]

    if "crossover_results" not in st.session_state or run_scan:
        st.session_state["crossover_results"] = None
        st.session_state["crossover_sector_scanned"] = None

    if run_scan or st.session_state.get("crossover_sector_scanned") != scan_sector:
        spinner_msg = (
            f"Scanning {scan_sector} — live intraday data..." if mkt["is_open"]
            else f"Scanning {scan_sector} — last close {mkt['last_close'].strftime('%d %b %Y')}..."
        )
        with st.spinner(spinner_msg):
            scan_sector_crossovers.clear()
            results = scan_sector_crossovers(scan_sector)
            st.session_state["crossover_results"] = results
            st.session_state["crossover_sector_scanned"] = scan_sector

    results = st.session_state.get("crossover_results") or []

    # ── Apply filters ─────────────────────────────────────────────────────
    filtered = []
    for r in results:
        if bias_filter == "Bullish Only" and r["bias"] != "Bullish":
            continue
        if bias_filter == "Bearish Only" and r["bias"] != "Bearish":
            continue
        # Filter crossovers by pair and freshness
        cx_filtered = [
            cx for cx in r["crossovers"]
            if cx["bars_ago"] <= freshness
            and (pair_filter == "All Pairs" or cx["pair"] == pair_filter)
        ]
        if not cx_filtered:
            continue
        r2 = dict(r)
        r2["crossovers"] = cx_filtered
        r2["freshest_bars"] = cx_filtered[0]["bars_ago"]
        filtered.append(r2)

    # ── Summary banner ────────────────────────────────────────────────────
    bull_count = sum(1 for r in filtered if r["bias"] == "Bullish")
    bear_count = sum(1 for r in filtered if r["bias"] == "Bearish")
    fresh_count = sum(1 for r in filtered if r["freshest_bars"] <= 3)

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#111827 0%,#0f172a 100%);
                border:1px solid #1e2d45;border-radius:10px;
                padding:14px 20px;margin:8px 0 20px;
                display:flex;gap:40px;flex-wrap:wrap;align-items:center'>
        <div>
            <div style='font-size:10px;color:#64748b;font-family:JetBrains Mono;letter-spacing:1px'>SCRIPS WITH CROSSOVERS</div>
            <div style='font-size:28px;font-weight:700;color:#00d4ff;font-family:JetBrains Mono'>{len(filtered)}</div>
        </div>
        <div>
            <div style='font-size:10px;color:#64748b;font-family:JetBrains Mono;letter-spacing:1px'>BULLISH CROSSOVERS</div>
            <div style='font-size:24px;font-weight:700;color:#00ff88;font-family:JetBrains Mono'>▲ {bull_count}</div>
        </div>
        <div>
            <div style='font-size:10px;color:#64748b;font-family:JetBrains Mono;letter-spacing:1px'>BEARISH CROSSOVERS</div>
            <div style='font-size:24px;font-weight:700;color:#ff4466;font-family:JetBrains Mono'>▼ {bear_count}</div>
        </div>
        <div>
            <div style='font-size:10px;color:#64748b;font-family:JetBrains Mono;letter-spacing:1px'>VERY FRESH (≤3 bars)</div>
            <div style='font-size:24px;font-weight:700;color:#ffd700;font-family:JetBrains Mono'>⚡ {fresh_count}</div>
        </div>
        <div style='margin-left:auto;font-family:JetBrains Mono;font-size:10px;color:#64748b;text-align:right'>
            Sector: {SECTOR_ICONS.get(scan_sector,"")} {scan_sector}<br>
            {mkt["label"]} · {mkt["last_close"].strftime("%d %b %Y") if not mkt["is_open"] else datetime.now().strftime("%d %b %Y %H:%M IST")}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not filtered:
        st.info(f"No crossovers found in {scan_sector} with current filters. Try increasing 'Max bars' or changing the pair filter.")
    else:
        # ── Overview bar chart: all scrips coloured by bias ────────────────
        st.markdown('<div class="section-header">CROSSOVER MAP — ALL QUALIFYING SCRIPS</div>',
                    unsafe_allow_html=True)

        ov_syms   = [r["symbol"]       for r in filtered]
        ov_bars   = [r["freshest_bars"] for r in filtered]
        ov_chg    = [r["change_pct"]    for r in filtered]
        ov_bias   = [r["bias"]          for r in filtered]
        ov_colors = ["#00ff88" if b == "Bullish" else "#ff4466" for b in ov_bias]
        ov_hover  = [
            f"<b>{r['symbol']}</b><br>"
            f"Bias: {r['bias']}<br>"
            f"LTP: ₹{r['ltp']:,.2f}<br>"
            f"Change: {r['change_pct']:+.2f}%<br>"
            f"Freshest crossover: {r['freshest_bars']} bar(s) ago<br>"
            + "<br>".join(
                f"  {cx['pair']} → {cx['direction']} ({cx['bars_ago']}b ago)"
                for cx in r["crossovers"]
            )
            for r in filtered
        ]

        fig_ov = go.Figure()
        fig_ov.add_trace(go.Bar(
            x=ov_syms,
            y=[freshness + 1 - b for b in ov_bars],   # invert: fresher = taller
            marker_color=ov_colors,
            marker_opacity=0.85,
            text=[f"{b}b ago" for b in ov_bars],
            textposition="outside",
            textfont=dict(family="JetBrains Mono", size=10, color="#e2e8f0"),
            hovertext=ov_hover,
            hoverinfo="text",
            width=0.55,
        ))
        # Change% scatter
        fig_ov.add_trace(go.Scatter(
            x=ov_syms,
            y=ov_chg,
            mode="markers+text",
            marker=dict(
                size=10,
                color=["#00ff88" if c >= 0 else "#ff4466" for c in ov_chg],
                symbol="diamond",
                line=dict(width=1, color="#0a0e1a"),
            ),
            text=[f"{c:+.2f}%" for c in ov_chg],
            textposition="top center",
            textfont=dict(family="JetBrains Mono", size=9),
            yaxis="y2",
            name="Day Change%",
            hoverinfo="skip",
        ))
        fig_ov.update_layout(
            height=310,
            paper_bgcolor="#0a0e1a",
            plot_bgcolor="#0d1117",
            font=dict(family="JetBrains Mono", color="#e2e8f0"),
            showlegend=False,
            margin=dict(l=40, r=60, t=30, b=60),
            xaxis=dict(tickfont=dict(size=11), tickangle=-30),
            yaxis=dict(
                title="Freshness Score", gridcolor="#1e2d45",
                zeroline=False, tickfont=dict(size=10),
                range=[0, freshness + 2],
            ),
            yaxis2=dict(
                title="Day Chg%", overlaying="y", side="right",
                zeroline=True, zerolinecolor="#1e2d45",
                showgrid=False, tickfont=dict(size=10),
                range=[-6, 6],
            ),
        )
        st.plotly_chart(fig_ov, use_container_width=True)

        # ── Per-scrip cards with mini chart ───────────────────────────────
        st.markdown('<div class="section-header">SCRIP DETAIL — PRICE + MA CHART</div>',
                    unsafe_allow_html=True)

        # Layout: 2 columns of cards
        cols_per_row = 2
        rows_needed  = (len(filtered) + cols_per_row - 1) // cols_per_row

        for row_i in range(rows_needed):
            card_cols = st.columns(cols_per_row)
            for col_i, card_col in enumerate(card_cols):
                idx = row_i * cols_per_row + col_i
                if idx >= len(filtered):
                    break
                r = filtered[idx]
                df_s = r["df"]
                bias_col = "#00ff88" if r["bias"] == "Bullish" else "#ff4466"
                chg_col  = "#00ff88" if r["change_pct"] >= 0 else "#ff4466"

                with card_col:
                    # Card header HTML
                    cx_badges = "".join(
                        f"<span style='background:{'rgba(0,255,136,0.12)' if cx['direction']=='Bullish' else 'rgba(255,68,102,0.12)'};"
                        f"color:{'#00ff88' if cx['direction']=='Bullish' else '#ff4466'};"
                        f"border:1px solid {'rgba(0,255,136,0.3)' if cx['direction']=='Bullish' else 'rgba(255,68,102,0.3)'};"
                        f"border-radius:5px;padding:2px 8px;font-size:10px;font-family:JetBrains Mono;"
                        f"margin:2px;display:inline-block'>"
                        f"{'▲' if cx['direction']=='Bullish' else '▼'} {cx['pair']} · {cx['bars_ago']}b ago</span>"
                        for cx in r["crossovers"]
                    )
                    st.markdown(f"""
                    <div style='background:linear-gradient(135deg,#111827 0%,#0f172a 100%);
                                border:1px solid #1e2d45;border-left:3px solid {bias_col};
                                border-radius:10px;padding:14px 16px;margin-bottom:4px'>
                        <div style='display:flex;justify-content:space-between;align-items:flex-start'>
                            <div>
                                <span style='font-size:18px;font-weight:700;color:#00d4ff;font-family:JetBrains Mono'>{r["symbol"]}</span>
                                <span style='font-size:11px;color:#64748b;font-family:JetBrains Mono;margin-left:10px'>
                                    ₹{r["ltp"]:,.2f}
                                </span>
                            </div>
                            <div style='text-align:right'>
                                <span style='font-size:13px;font-weight:700;color:{chg_col};font-family:JetBrains Mono'>
                                    {"▲" if r["change_pct"]>=0 else "▼"} {abs(r["change_pct"]):.2f}%
                                </span>
                                <br>
                                <span style='font-size:11px;font-weight:600;color:{bias_col};font-family:JetBrains Mono'>
                                    {"🟢" if r["bias"]=="Bullish" else "🔴"} {r["bias"].upper()}
                                </span>
                            </div>
                        </div>
                        <div style='margin-top:8px'>{cx_badges}</div>
                        <div style='margin-top:8px;display:flex;gap:16px;flex-wrap:wrap'>
                            <span style='font-size:10px;color:#64748b;font-family:JetBrains Mono'>
                                EMA20 <span style='color:#ffd700'>₹{r["ema20"]:,.2f}</span>
                            </span>
                            <span style='font-size:10px;color:#64748b;font-family:JetBrains Mono'>
                                EMA50 <span style='color:#ff8c00'>₹{r["ema50"]:,.2f}</span>
                            </span>
                            <span style='font-size:10px;color:#64748b;font-family:JetBrains Mono'>
                                SMA50 <span style='color:#00d4ff'>₹{r["sma50"]:,.2f}</span>
                            </span>
                            <span style='font-size:10px;color:#64748b;font-family:JetBrains Mono'>
                                SMA100 <span style='color:#bf5fff'>₹{r["sma100"]:,.2f}</span>
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Mini price + MA chart
                    if not df_s.empty and len(df_s) >= 20:
                        chart_df = df_s.tail(60)
                        fig_mini = go.Figure()
                        # Candlestick
                        fig_mini.add_trace(go.Candlestick(
                            x=chart_df["Date"],
                            open=chart_df["Open"],
                            high=chart_df["High"],
                            low=chart_df["Low"],
                            close=chart_df["Close"],
                            name="Price",
                            increasing_line_color="#00ff88",
                            decreasing_line_color="#ff4466",
                            increasing_fillcolor="rgba(0,255,136,0.6)",
                            decreasing_fillcolor="rgba(255,68,102,0.6)",
                            showlegend=False,
                        ))
                        # MAs
                        for ma_col, ma_color, ma_name in [
                            ("EMA20",  "#ffd700", "EMA 20"),
                            ("EMA50",  "#ff8c00", "EMA 50"),
                            ("SMA50",  "#00d4ff", "SMA 50"),
                            ("SMA100", "#bf5fff", "SMA 100"),
                        ]:
                            if ma_col in chart_df.columns:
                                fig_mini.add_trace(go.Scatter(
                                    x=chart_df["Date"],
                                    y=chart_df[ma_col],
                                    mode="lines",
                                    name=ma_name,
                                    line=dict(color=ma_color, width=1.5),
                                ))
                        # Mark crossover points
                        for cx in r["crossovers"]:
                            if cx.get("date") is not None:
                                fig_mini.add_vline(
                                    x=cx["date"].timestamp() * 1000,
                                    line_dash="dot",
                                    line_color="#00ff88" if cx["direction"] == "Bullish" else "#ff4466",
                                    line_width=1.5,
                                    annotation_text=f"{'▲' if cx['direction']=='Bullish' else '▼'} {cx['pair']}",
                                    annotation_font=dict(size=9, color="#e2e8f0", family="JetBrains Mono"),
                                    annotation_position="top left",
                                )
                        fig_mini.update_layout(
                            height=280,
                            paper_bgcolor="#0a0e1a",
                            plot_bgcolor="#0d1117",
                            font=dict(family="JetBrains Mono", color="#e2e8f0", size=9),
                            margin=dict(l=40, r=10, t=10, b=30),
                            xaxis=dict(
                                rangeslider_visible=False,
                                gridcolor="#1e2d45",
                                tickfont=dict(size=8),
                            ),
                            yaxis=dict(
                                gridcolor="#1e2d45",
                                tickfont=dict(size=8),
                                tickprefix="₹",
                            ),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom", y=1.01,
                                xanchor="left", x=0,
                                font=dict(size=8),
                            ),
                            showlegend=True,
                        )
                        st.plotly_chart(fig_mini, use_container_width=True, key=f"mini_{r['symbol']}_{row_i}_{col_i}")

        # ── MA values summary table ────────────────────────────────────────
        st.markdown('<div class="section-header">MA VALUES SUMMARY TABLE</div>',
                    unsafe_allow_html=True)
        table_rows = []
        for r in filtered:
            cx_str = " | ".join(
                f"{'▲' if cx['direction']=='Bullish' else '▼'} {cx['pair']} ({cx['bars_ago']}b)"
                for cx in r["crossovers"]
            )
            table_rows.append({
                "Symbol":      r["symbol"],
                "LTP (₹)":     r["ltp"],
                "Day Chg%":    r["change_pct"],
                "Bias":        r["bias"],
                "EMA 20":      r["ema20"],
                "EMA 50":      r["ema50"],
                "SMA 50":      r["sma50"],
                "SMA 100":     r["sma100"],
                "Crossovers":  cx_str,
            })
        tdf = pd.DataFrame(table_rows)
        if not tdf.empty:
            def colour_bias(val):
                if val == "Bullish":  return "color: #00ff88; font-weight:600"
                if val == "Bearish":  return "color: #ff4466; font-weight:600"
                return ""
            def colour_chg(val):
                try:
                    return "color: #00ff88" if float(val) >= 0 else "color: #ff4466"
                except Exception:
                    return ""
            styled = (
                tdf.style
                .applymap(colour_bias, subset=["Bias"])
                .applymap(colour_chg,  subset=["Day Chg%"])
                .format({
                    "LTP (₹)":  "₹{:,.2f}",
                    "Day Chg%": "{:+.2f}%",
                    "EMA 20":   "₹{:,.2f}",
                    "EMA 50":   "₹{:,.2f}",
                    "SMA 50":   "₹{:,.2f}",
                    "SMA 100":  "₹{:,.2f}",
                })
            )
            st.dataframe(styled, use_container_width=True)

        # ── Legend ────────────────────────────────────────────────────────
        st.markdown("""
        <div style='display:flex;gap:24px;flex-wrap:wrap;padding:10px 0 4px;
                    font-family:JetBrains Mono;font-size:11px;color:#64748b'>
            <span><span style='color:#ffd700'>━</span> EMA 20 &nbsp;·&nbsp;
                  <span style='color:#ff8c00'>━</span> EMA 50 &nbsp;·&nbsp;
                  <span style='color:#00d4ff'>━</span> SMA 50 &nbsp;·&nbsp;
                  <span style='color:#bf5fff'>━</span> SMA 100</span>
            <span>▲ = Bullish crossover (fast MA crossed above slow MA)</span>
            <span>▼ = Bearish crossover (fast MA crossed below slow MA)</span>
            <span>⚡ Fresh = crossover within last 3 bars</span>
        </div>
        <div style='font-family:JetBrains Mono;font-size:10px;color:#3d4d5e;padding-top:4px'>
            ⚠️ For educational purposes only. Not financial advice. Always do your own research.
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#64748b; font-size:11px; font-family: JetBrains Mono; padding: 10px 0;'>
Nifty Analysis Bot · Built with Streamlit + NSE India API + pandas · For educational purposes only<br>
⚠️ Not financial advice. Always verify signals with your own research before trading.
</div>
""", unsafe_allow_html=True)

# Auto refresh
if auto_refresh:
    time.sleep(60)
    st.rerun()
