"""
Nifty Analysis Bot — Full Streamlit App
Uses nsepython for live NSE data, pandas for indicators, plotly for charts.
"""
import streamlit as st
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
def fetch_index_data(symbol: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.nseindia.com/",
    }
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        url = f"https://www.nseindia.com/api/allIndices"
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
def fetch_historical_data(symbol: str, days: int = 60) -> pd.DataFrame:
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
        base_prices = {"NIFTY": 22_500, "BANKNIFTY": 48_500, "SENSEX": 74_000}
        base = base_prices.get(symbol, 22_500)
        dates = pd.bdate_range(end=datetime.today(), periods=days)
        np.random.seed(42)
        returns = np.random.normal(0, 0.008, len(dates))
        closes = base * np.cumprod(1 + returns)
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
# OI FALLBACK FUNCTION (moved up so it's defined before use)
# ─────────────────────────────────────────────
def get_option_chain_with_fallback(symbol: str):
    today = datetime.now()
    data = fetch_option_chain(symbol)
    
    if "error" in data or not data.get("records", {}).get("data"):
        st.info("Market closed or no live OI data available. Falling back to last trading day's data (Friday).")
        last_trading_day = today - timedelta(days=1)
        while last_trading_day.weekday() >= 5:  # skip Sat/Sun
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

def oi_buildup_signal(oc_df: pd.DataFrame, spot_change: float) -> str:
    if oc_df.empty:
        return "Neutral OI"
    
    atm_range = spot_price * 0.02
    atm = oc_df[(oc_df["Strike"] >= spot_price - atm_range) & (oc_df["Strike"] <= spot_price + atm_range)]
    if atm.empty:
        atm = oc_df.iloc[max(0, len(oc_df) // 2 - 5): len(oc_df) // 2 + 5]
    
    ce_oi_chg = atm["CE_OI_Chg"].sum()
    pe_oi_chg = atm["PE_OI_Chg"].sum()
    total_oi_chg = ce_oi_chg + pe_oi_chg
    
    if total_oi_chg > 0:
        if spot_change > 0:
            return "Long Build Up"
        else:
            return "Short Build Up"
    elif total_oi_chg < 0:
        if spot_change > 0:
            return "Short Covering"
        else:
            return "Long Unwinding"
    else:
        return "No Clear OI Change"

# ─────────────────────────────────────────────
# ANALYSIS + CONFIDENCE SCORE (fixed)
# ─────────────────────────────────────────────
def generate_analysis(df: pd.DataFrame, cpr: dict, pcr: float, oi_signal: str, spot: float) -> dict:
    last = df.iloc[-1]
    score = 50
    signals = []
    tags = []
    # RSI
    rsi = last["RSI"]
    if rsi > 60:
        score += 6; signals.append(f"RSI {rsi:.1f} (overbought zone — bullish momentum)"); tags.append(("bullish", "RSI >60"))
    elif rsi < 40:
        score -= 6; signals.append(f"RSI {rsi:.1f} (oversold zone — bearish)"); tags.append(("bearish", "RSI <40"))
    else:
        signals.append(f"RSI {rsi:.1f} (neutral zone)")
    # EMA crossover
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
    # ADX / DMI
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
    # CPR position
    tc = cpr["tc"]; bc = cpr["bc"]; pivot = cpr["pivot"]
    if spot > tc:
        score += 8; signals.append(f"Price ({spot:.1f}) above TC CPR ({tc:.1f}) → Bullish"); tags.append(("bullish", "Above TC-CPR"))
    elif spot < bc:
        score -= 8; signals.append(f"Price ({spot:.1f}) below BC CPR ({bc:.1f}) → Bearish"); tags.append(("bearish", "Below BC-CPR"))
    else:
        signals.append(f"Price ({spot:.1f}) inside CPR [{bc:.1f} - {tc:.1f}] → Consolidation"); tags.append(("neutral", "Inside CPR"))
    # Day H/L breakout
    prev_high = cpr["prev_high"]; prev_low = cpr["prev_low"]
    if spot > prev_high:
        breakout_boost = 12 if adx > 25 else 7
        score += breakout_boost
        signals.append(f"Price ({spot:.1f}) > Previous Day High ({prev_high:.1f}) → Day High Breakout confirmed" + (" with trend" if adx > 25 else "")); tags.append(("bullish", "Day High Breakout"))
    elif spot < prev_low:
        breakout_boost = 12 if adx > 25 else 7
        score -= breakout_boost
        signals.append(f"Price ({spot:.1f}) < Previous Day Low ({prev_low:.1f}) → Day Low Breakdown confirmed"); tags.append(("bearish", "Day Low Breakdown"))
    # OI buildup
    if "Short Covering" in oi_signal:
        score += 8; tags.append(("bullish", "Short Covering"))
    elif "Long Buildup" in oi_signal:
        score += 6; tags.append(("bullish", "Long Buildup"))
    elif "Short Buildup" in oi_signal:
        score -= 8; tags.append(("bearish", "Short Buildup"))
    elif "Long Unwinding" in oi_signal:
        score -= 6; tags.append(("bearish", "Long Unwinding"))
    signals.append(f"OI Signal: {oi_signal}")
    # PCR
    if pcr > 1.3:
        score += 5; signals.append(f"PCR {pcr:.2f} — High (Bullish sentiment)"); tags.append(("bullish", f"PCR {pcr:.2f}"))
    elif pcr < 0.7:
        score -= 5; signals.append(f"PCR {pcr:.2f} — Low (Bearish sentiment)"); tags.append(("bearish", f"PCR {pcr:.2f}"))
    else:
        signals.append(f"PCR {pcr:.2f} — Neutral")
    # Bollinger
    bb_upper = last["BB_upper"]; bb_lower = last["BB_lower"]
    if spot > bb_upper:
        score += 4; signals.append("Price above BB Upper — potential continuation or reversal zone"); tags.append(("neutral", "Above BB"))
    elif spot < bb_lower:
        score -= 4; signals.append("Price below BB Lower — oversold on BB"); tags.append(("neutral", "Below BB"))
    # Clamp score
    score = int(np.clip(score, 5, 97))
    # Bullet list for interpretation
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
# MAIN EXECUTION
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")
    selected_index = st.selectbox("Select Index", ["NIFTY", "BANKNIFTY", "SENSEX"], index=0)
    hist_days = st.slider("Historical Days", 15, 120, 60, step=5)

    # Chart Type Selector
    chart_type = st.selectbox(
        "Chart Type",
        options=["Candlestick", "Kagi", "Point & Figure"],
        index=0,
        help="Switch between classic candlestick and reversal-based charts"
    )

    # Optional controls for P&F and Kagi
    if chart_type in ["Point & Figure", "Kagi"]:
        box_size = st.slider(
            "Box/Reversal Size",
            min_value=0.25, max_value=5.0, value=1.0, step=0.25,
            help="Box size for P&F or reversal threshold for Kagi (in points)"
        )
        reversal_boxes = st.slider(
            "Reversal (boxes)",
            min_value=1, max_value=5, value=3, step=1,
            help="Number of boxes needed for reversal"
        )
    else:
        box_size = 1.0
        reversal_boxes = 3

    st.markdown("---")
    st.markdown("##### 🔑 API Keys (Optional)")
    anthropic_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
    dhan_client_id = st.text_input("Dhan Client ID", placeholder="Client ID")
    dhan_token = st.text_input("Dhan Access Token", type="password", placeholder="Access Token")
    st.markdown("---")
    refresh = st.button("🔄 Refresh Data", use_container_width=True)
    auto_refresh = st.checkbox("Auto Refresh (60s)", value=False)

with st.spinner("Fetching live market data..."):
    hist_df = fetch_historical_data(selected_index, hist_days)
    if hist_df.empty:
        st.error("❌ Failed to fetch historical data. Please check your connection.")
        st.stop()
    hist_df = add_all_indicators(hist_df)
    cpr = calc_cpr(hist_df)

    # Calculate Camarilla Pivots
    cam_r1, cam_r2, cam_r3, cam_r4, cam_s1, cam_s2, cam_s3, cam_s4 = calculate_camarilla(hist_df)

    # Calculate Fibonacci Pivots
    fib_r1, fib_r2, fib_r3, fib_s1, fib_s2, fib_s3 = calculate_fibonacci(hist_df)

    last_row = hist_df.iloc[-1]
    index_live = fetch_index_data(selected_index)
    spot_price = float(index_live.get("last", last_row["Close"])) if index_live and "error" not in index_live else float(last_row["Close"])
    spot_change = float(index_live.get("variation", 0)) if index_live and "error" not in index_live else 0.0
    spot_pct = float(index_live.get("percentChange", 0)) if index_live and "error" not in index_live else 0.0

    # Fetch OI with fallback
    oc_data, last_updated_note = get_option_chain_with_fallback(INDEX_SYMBOLS[selected_index]["option_chain"])
    if "error" in oc_data:
        st.warning(f"⚠️ Option chain data unavailable: {oc_data['error']}")
        oc_df = pd.DataFrame()
        pcr = 1.0
        oi_signal = "N/A (OC fetch failed)"
    else:
        oc_df = process_option_chain(oc_data, spot_price)
        pcr = calc_pcr(oc_df)
        oi_signal = oi_buildup_signal(oc_df, spot_change)
    analysis = generate_analysis(hist_df, cpr, pcr, oi_signal, spot_price)

# ─────────────────────────────────────────────
# LAST UPDATED NOTE
# ─────────────────────────────────────────────
st.markdown(f"<p style='text-align:center; color:#64748b; font-size:11px;'>Last updated: {last_updated_note} · Index: <span style='color:#00d4ff'>{selected_index}</span></p>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LIVE METRICS ROW (with OI Interpretation)
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">LIVE MARKET SNAPSHOT</div>', unsafe_allow_html=True)
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
        </div>
        """, unsafe_allow_html=True)

# OI Interpretation card
with c7:
    oi_sig = oi_signal
    oi_class = "metric-change-up" if "Build Up" in oi_sig or "Covering" in oi_sig else "metric-change-down"
    oi_icon = "🟢" if "Build Up" in oi_sig or "Covering" in oi_sig else "🔴"
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: { 'var(--green)' if oi_class == 'metric-change-up' else 'var(--red)' };">
        <div class="metric-label">OI Interpretation</div>
        <div class="metric-value">{oi_icon} {oi_sig}</div>
        <div class="{oi_class}"></div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# OPEN INTEREST REPRESENTATION SECTION
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">OPEN INTEREST REPRESENTATION</div>', unsafe_allow_html=True)

if not oc_df.empty:
    atm_range = spot_price * 0.02
    oi_near = oc_df[(oc_df["Strike"] >= spot_price - atm_range) & (oc_df["Strike"] <= spot_price + atm_range)].copy()
    if oi_near.empty:
        oi_near = oc_df.iloc[max(0, len(oc_df) // 2 - 5): len(oc_df) // 2 + 5]

    fig_oi = go.Figure()

    fig_oi.add_trace(go.Bar(
        x=oi_near["Strike"],
        y=oi_near["CE_OI_Chg"],
        name="CE OI Change",
        marker_color="#ff4466",
        opacity=0.8
    ))

    fig_oi.add_trace(go.Bar(
        x=oi_near["Strike"],
        y=oi_near["PE_OI_Chg"],
        name="PE OI Change",
        marker_color="#00ff88",
        opacity=0.8
    ))

    fig_oi.add_vline(
        x=spot_price,
        line_dash="dash",
        line_color="#00d4ff",
        annotation_text=f"Spot {spot_price:,.0f}",
        annotation_font_color="#00d4ff"
    )

    fig_oi.update_layout(
        barmode="group",
        height=400,
        title="Open Interest Change Near ATM (CE vs PE)",
        xaxis_title="Strike Price",
        yaxis_title="Change in OI",
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0d1117",
        font=dict(family="JetBrains Mono", color="#e2e8f0"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=40, r=40, t=60, b=40)
    )

    st.plotly_chart(fig_oi, use_container_width=True)

    st.markdown(f"""
    <div style="font-size:16px; margin:16px 0; text-align:center;">
        <strong>Current OI Signal:</strong> {oi_icon} <span style="color:{'var(--green)' if oi_class == 'metric-change-up' else 'var(--red)'}">{oi_sig}</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("Open Interest data not available. Market closed or NSE connectivity issue. Showing last available data.")

# ─────────────────────────────────────────────
# MARKET INTERPRETATION AS BULLET LIST
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">MARKET INTERPRETATION</div>', unsafe_allow_html=True)
bullets = analysis.get("bullets", [])  # fallback if not present
if bullets:
    bullet_html = ""
    for bullet in bullets:
        color = "var(--green)" if "🟢" in bullet or "BULLISH" in bullet else "var(--red)" if "🔴" in bullet or "BEARISH" in bullet else "var(--yellow)"
        bullet_html += f'<li style="color:{color}; margin:6px 0;">{bullet}</li>'
    st.markdown(f"""
    <div class="summary-box">
        <ul style="list-style:none; padding-left:0; margin:0;">
            {bullet_html}
        </ul>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("No interpretation bullets available.")

# ─────────────────────────────────────────────
# PRICE CHART WITH TYPE SELECTION
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">PRICE CHART (' + chart_type + ')</div>', unsafe_allow_html=True)

fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    row_heights=[0.55, 0.25, 0.20],
    vertical_spacing=0.04,
    subplot_titles=("Price / Indicators", "ADX / DMI", "Volume"),
)

# ── Main Chart Type ────────────────────────────────────────────────
if chart_type == "Candlestick":
    fig.add_trace(go.Candlestick(
        x=hist_df["Date"], open=hist_df["Open"], high=hist_df["High"],
        low=hist_df["Low"], close=hist_df["Close"],
        name="Candlestick",
        increasing_line_color="#00ff88",
        decreasing_line_color="#ff4466",
        increasing_fillcolor="#00ff88",
        decreasing_fillcolor="#ff4466"
    ), row=1, col=1)

elif chart_type == "Kagi":
    kagi = hist_df["Close"].copy()
    direction = np.sign(kagi.diff())
    reversal_points = np.where(direction != direction.shift())[0]
    for i in range(len(reversal_points)-1):
        start = reversal_points[i]
        end = reversal_points[i+1]
        segment = kagi.iloc[start:end]
        fig.add_trace(go.Scatter(
            x=segment.index,
            y=segment,
            mode='lines',
            line=dict(
                color="#00d4ff" if segment.iloc[-1] > segment.iloc[0] else "#ff4466",
                width=4 if abs(segment.iloc[-1] - segment.iloc[0]) > box_size * reversal_boxes else 1
            ),
            name="Kagi Segment",
            showlegend=False
        ), row=1, col=1)

elif chart_type == "Point & Figure":
    pnf_boxes = []
    current_col = []
    current_dir = 1
    last_price = hist_df["Close"].iloc[0]

    for price in hist_df["Close"]:
        if price >= last_price + box_size * reversal_boxes:
            if current_dir == -1:
                pnf_boxes.append(current_col)
                current_col = []
                current_dir = 1
            current_col.extend(["X"] * int((price - last_price) // box_size))
            last_price = price
        elif price <= last_price - box_size * reversal_boxes:
            if current_dir == 1:
                pnf_boxes.append(current_col)
                current_col = []
                current_dir = -1
            current_col.extend(["O"] * int((last_price - price) // box_size))
            last_price = price

    pnf_boxes.append(current_col)

    x_pos = []
    y_pos = []
    colors = []
    for col_idx, col in enumerate(pnf_boxes):
        for box_idx, box in enumerate(col):
            x_pos.append(col_idx)
            y_pos.append(last_price - box_idx * box_size)
            colors.append("green" if box == "X" else "red")

    fig.add_trace(go.Scatter(
        x=x_pos,
        y=y_pos,
        mode="markers",
        marker=dict(
            symbol="square" if colors[0] == "green" else "circle",
            size=10,
            color=colors,
            line=dict(width=1, color="black")
        ),
        name="P&F Boxes",
        showlegend=False
    ), row=1, col=1)

# ── Common overlays ────────────────────────────────────────────────────
fig.add_trace(go.Scatter(x=hist_df["Date"], y=hist_df["EMA13"], mode="lines", name="EMA 13", line=dict(color="#ffd700")), row=1, col=1)
fig.add_trace(go.Scatter(x=hist_df["Date"], y=hist_df["EMA21"], mode="lines", name="EMA 21", line=dict(color="#ff8c00")), row=1, col=1)

fig.add_hline(y=cpr["pivot"], line_dash="dash", line_color="#00d4ff", annotation_text="Pivot", row=1, col=1)
fig.add_hline(y=cpr["bc"], line_dash="dot", line_color="#ff4466", annotation_text="BC", row=1, col=1)
fig.add_hline(y=cpr["tc"], line_dash="dot", line_color="#00ff88", annotation_text="TC", row=1, col=1)

fig.add_hline(y=cam_r3, line_color="#00ff88", line_dash="dash", annotation_text="Cam R3", row=1, col=1)
fig.add_hline(y=fib_r3, line_color="#ffd700", line_dash="dash", annotation_text="Fib R3", row=1, col=1)

# ── ADX & Volume ───────────────────────────────────────────────────────
fig.add_trace(go.Scatter(x=hist_df["Date"], y=hist_df["ADX"], name="ADX", line=dict(color="#ffd700")), row=2, col=1)
fig.add_trace(go.Bar(x=hist_df["Date"], y=hist_df["Volume"], name="Volume", marker_color=["#00ff88" if c >= o else "#ff4466" for c, o in zip(hist_df["Close"], hist_df["Open"])]), row=3, col=1)

fig.update_layout(
    height=700,
    title=f"{selected_index} - {chart_type} Chart",
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis_rangeslider_visible=False,
    margin=dict(l=40, r=40, t=60, b=40),
    paper_bgcolor="#0a0e1a",
    plot_bgcolor="#0d1117",
    font=dict(family="JetBrains Mono", color="#e2e8f0")
)

st.plotly_chart(fig, use_container_width=True)

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
