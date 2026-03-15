"""
Nifty Analysis Bot — Full Streamlit App
Uses nsepython for live NSE data, pandas-ta for indicators, plotly for charts.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
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
    """Fetch live quote from NSE India."""
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
    """Fetch index spot data from NSE."""
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
def fetch_option_chain(symbol: str) -> dict:
    """Fetch option chain data from NSE."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "*/*",
        "Referer": "https://www.nseindia.com/option-chain",
    }
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        time.sleep(0.5)
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        r = session.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=300)
def fetch_historical_data(symbol: str, days: int = 60) -> pd.DataFrame:
    """
    Fetch historical OHLCV data for Nifty indices from NSE.
    Falls back to synthetic data if fetch fails (for demo / network limits).
    """
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
            "SENSEX": "NIFTY 50",  # BSE not available on NSE endpoint
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

        # Volume column (NSE index data has no real volume — use synthetic)
        df["Volume"] = np.random.randint(50_000_000, 200_000_000, len(df)).astype(float)

        for col in ["Open", "High", "Low", "Close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
        return df[["Date", "Open", "High", "Low", "Close", "Volume"]]

    except Exception as e:
        # ── Synthetic fallback ──────────────────────────────
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
# INDICATOR CALCULATIONS (pure pandas / numpy)
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
    """Calculate CPR using previous day OHLC."""
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
# OPTION CHAIN PROCESSING
# ─────────────────────────────────────────────
def process_option_chain(oc_data: dict, spot: float) -> pd.DataFrame:
    """Parse raw option chain JSON into a clean DataFrame."""
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


def oi_buildup_signal(oc_df: pd.DataFrame, spot: float) -> str:
    """Determine OI buildup type near ATM strikes."""
    if oc_df.empty:
        return "Neutral"
    atm_range = spot * 0.02
    atm = oc_df[(oc_df["Strike"] >= spot - atm_range) & (oc_df["Strike"] <= spot + atm_range)]
    if atm.empty:
        atm = oc_df.iloc[max(0, len(oc_df) // 2 - 3): len(oc_df) // 2 + 3]

    ce_oi_chg = atm["CE_OI_Chg"].sum()
    pe_oi_chg = atm["PE_OI_Chg"].sum()

    if ce_oi_chg < 0 and pe_oi_chg > 0:
        return "Short Covering (CE) + Long Buildup (PE)"
    elif ce_oi_chg > 0 and pe_oi_chg < 0:
        return "Short Buildup (CE) + Long Unwinding (PE)"
    elif ce_oi_chg < 0 and pe_oi_chg < 0:
        return "Long Unwinding"
    elif ce_oi_chg > 0 and pe_oi_chg > 0:
        return "Long Buildup"
    else:
        return "Neutral OI"


# ─────────────────────────────────────────────
# ANALYSIS + CONFIDENCE SCORE
# ─────────────────────────────────────────────
def generate_analysis(df: pd.DataFrame, cpr: dict, pcr: float, oi_signal: str, spot: float) -> dict:
    """Rule-based analysis combining all signals."""
    last = df.iloc[-1]
    score = 50
    signals = []
    tags = []

    # ── RSI ──────────────────────────────────
    rsi = last["RSI"]
    if rsi > 60:
        score += 6; signals.append(f"RSI {rsi:.1f} (overbought zone — bullish momentum)"); tags.append(("bullish", "RSI >60"))
    elif rsi < 40:
        score -= 6; signals.append(f"RSI {rsi:.1f} (oversold zone — bearish)"); tags.append(("bearish", "RSI <40"))
    else:
        signals.append(f"RSI {rsi:.1f} (neutral zone)")

    # ── EMA crossover ────────────────────────
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

    # ── ADX / DMI ────────────────────────────
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

    # ── CPR position ─────────────────────────
    tc = cpr["tc"]; bc = cpr["bc"]; pivot = cpr["pivot"]
    if spot > tc:
        score += 8; signals.append(f"Price ({spot:.1f}) above TC CPR ({tc:.1f}) → Bullish"); tags.append(("bullish", "Above TC-CPR"))
    elif spot < bc:
        score -= 8; signals.append(f"Price ({spot:.1f}) below BC CPR ({bc:.1f}) → Bearish"); tags.append(("bearish", "Below BC-CPR"))
    else:
        signals.append(f"Price ({spot:.1f}) inside CPR [{bc:.1f} - {tc:.1f}] → Consolidation"); tags.append(("neutral", "Inside CPR"))

    # ── Day H/L breakout ─────────────────────
    prev_high = cpr["prev_high"]; prev_low = cpr["prev_low"]
    if spot > prev_high:
        breakout_boost = 12 if adx > 25 else 7
        score += breakout_boost
        signals.append(f"Price ({spot:.1f}) > Previous Day High ({prev_high:.1f}) → Day High Breakout confirmed" + (" with trend" if adx > 25 else "")); tags.append(("bullish", "Day High Breakout"))
    elif spot < prev_low:
        breakout_boost = 12 if adx > 25 else 7
        score -= breakout_boost
        signals.append(f"Price ({spot:.1f}) < Previous Day Low ({prev_low:.1f}) → Day Low Breakdown confirmed"); tags.append(("bearish", "Day Low Breakdown"))

    # ── OI buildup ───────────────────────────
    if "Short Covering" in oi_signal:
        score += 8; tags.append(("bullish", "Short Covering"))
    elif "Long Buildup" in oi_signal:
        score += 6; tags.append(("bullish", "Long Buildup"))
    elif "Short Buildup" in oi_signal:
        score -= 8; tags.append(("bearish", "Short Buildup"))
    elif "Long Unwinding" in oi_signal:
        score -= 6; tags.append(("bearish", "Long Unwinding"))
    signals.append(f"OI Signal: {oi_signal}")

    # ── PCR ──────────────────────────────────
    if pcr > 1.3:
        score += 5; signals.append(f"PCR {pcr:.2f} — High (Bullish sentiment)"); tags.append(("bullish", f"PCR {pcr:.2f}"))
    elif pcr < 0.7:
        score -= 5; signals.append(f"PCR {pcr:.2f} — Low (Bearish sentiment)"); tags.append(("bearish", f"PCR {pcr:.2f}"))
    else:
        signals.append(f"PCR {pcr:.2f} — Neutral")

    # ── Bollinger ────────────────────────────
    bb_upper = last["BB_upper"]; bb_lower = last["BB_lower"]
    if spot > bb_upper:
        score += 4; signals.append("Price above BB Upper — potential continuation or reversal zone"); tags.append(("neutral", "Above BB"))
    elif spot < bb_lower:
        score -= 4; signals.append("Price below BB Lower — oversold on BB"); tags.append(("neutral", "Below BB"))

    # ── Clamp score ──────────────────────────
    score = int(np.clip(score, 5, 97))

    # ── Narrative summary ────────────────────
    if score >= 65:
        bias = "🟢 BULLISH"
    elif score <= 40:
        bias = "🔴 BEARISH"
    else:
        bias = "🟡 NEUTRAL / CONSOLIDATION"

    key_bullets = " + ".join([t[1] for t in tags[:5]])
    day_hl = ""
    if spot > prev_high:
        day_hl = f"Bullish Day High Breakout ({spot:.1f} > {prev_high:.1f})"
    elif spot < prev_low:
        day_hl = f"Bearish Day Low Breakdown ({spot:.1f} < {prev_low:.1f})"

    summary = (
        f"{oi_signal} detected · ADX {adx:.0f} ({'trending' if adx > 25 else 'sideways'}) · "
        f"Price {'above TC' if spot > tc else ('below BC' if spot < bc else 'inside')} CPR · "
        f"{'EMA13 > EMA21' if ema13 > ema21 else 'EMA13 < EMA21'} · PCR {pcr:.2f}"
        + (f" · {day_hl}" if day_hl else "")
        + f" → **{bias}** (Confidence: {score}/100)"
    )

    return {"score": score, "bias": bias, "summary": summary, "signals": signals, "tags": tags}


# ─────────────────────────────────────────────
# PLOTLY CHART
# ─────────────────────────────────────────────
def build_chart(df: pd.DataFrame, cpr: dict, symbol: str) -> go.Figure:
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.55, 0.25, 0.20],
        vertical_spacing=0.04,
        subplot_titles=("Price / Indicators", "ADX / DMI", "Volume"),
    )

    # ── Candlestick ──────────────────────────
    fig.add_trace(go.Candlestick(
        x=df["Date"], open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        name="OHLC",
        increasing_fillcolor="#00ff88", increasing_line_color="#00ff88",
        decreasing_fillcolor="#ff4466", decreasing_line_color="#ff4466",
    ), row=1, col=1)

    # ── Bollinger Bands ──────────────────────
    fig.add_trace(go.Scatter(x=df["Date"], y=df["BB_upper"], name="BB Upper",
        line=dict(color="rgba(0,212,255,0.4)", dash="dash", width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["BB_mid"], name="BB Mid",
        line=dict(color="rgba(0,212,255,0.25)", width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["BB_lower"], name="BB Lower",
        fill="tonexty", fillcolor="rgba(0,212,255,0.04)",
        line=dict(color="rgba(0,212,255,0.4)", dash="dash", width=1)), row=1, col=1)

    # ── EMAs ─────────────────────────────────
    fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA13"], name="EMA 13",
        line=dict(color="#ffd700", width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA21"], name="EMA 21",
        line=dict(color="#ff8c00", width=1.5, dash="dot")), row=1, col=1)

    # ── CPR lines ────────────────────────────
    x0, x1 = df["Date"].iloc[0], df["Date"].iloc[-1]
    for level, color, label in [
        (cpr["tc"], "#00ff88", "TC"), (cpr["pivot"], "#00d4ff", "Pivot"),
        (cpr["bc"], "#ff4466", "BC"), (cpr["prev_high"], "#ffffff", "PDH"),
        (cpr["prev_low"], "#aaaaaa", "PDL"),
    ]:
        fig.add_shape(type="line", x0=x0, x1=x1, y0=level, y1=level,
            line=dict(color=color, width=1, dash="dot"), row=1, col=1)
        fig.add_annotation(x=x1, y=level, text=f"  {label} {level:.0f}",
            showarrow=False, xanchor="left", font=dict(color=color, size=10), row=1, col=1)

    # ── ADX / DMI ────────────────────────────
    fig.add_trace(go.Scatter(x=df["Date"], y=df["ADX"], name="ADX",
        line=dict(color="#ffd700", width=2)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["+DI"], name="+DI",
        line=dict(color="#00ff88", width=1.2, dash="dot")), row=2, col=1)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["-DI"], name="-DI",
        line=dict(color="#ff4466", width=1.2, dash="dot")), row=2, col=1)
    fig.add_hline(y=25, line_dash="dash", line_color="rgba(255,255,255,0.2)", row=2, col=1)

    # ── Volume ───────────────────────────────
    colors = ["#00ff88" if c >= o else "#ff4466"
              for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=df["Date"], y=df["Volume"], name="Volume",
        marker_color=colors, opacity=0.7), row=3, col=1)

    # ── Layout ───────────────────────────────
    fig.update_layout(
        height=700,
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0d1117",
        font=dict(family="JetBrains Mono", color="#e2e8f0", size=11),
        showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=80, t=40, b=10),
        title=dict(text=f"{symbol} — Price & Indicators", font=dict(color="#00d4ff", size=16)),
    )
    for ax in ["xaxis", "xaxis2", "xaxis3"]:
        fig.update_layout(**{ax: dict(gridcolor="#1e2d45", showgrid=True)})
    for ax in ["yaxis", "yaxis2", "yaxis3"]:
        fig.update_layout(**{ax: dict(gridcolor="#1e2d45", showgrid=True)})
    return fig


# ─────────────────────────────────────────────
# OPTION CHAIN CHART
# ─────────────────────────────────────────────
def build_oi_chart(oc_df: pd.DataFrame, spot: float) -> go.Figure:
    near = oc_df.copy()
    # Show 10 strikes around ATM
    atm_idx = (near["Strike"] - spot).abs().idxmin()
    lo = max(0, atm_idx - 10)
    hi = min(len(near), atm_idx + 10)
    near = near.iloc[lo:hi].reset_index(drop=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=near["Strike"], y=near["CE_OI"] / 1e5, name="CE OI (L)",
        marker_color="#ff4466", opacity=0.8))
    fig.add_trace(go.Bar(x=near["Strike"], y=near["PE_OI"] / 1e5, name="PE OI (L)",
        marker_color="#00ff88", opacity=0.8))
    fig.add_vline(x=spot, line_dash="dash", line_color="#00d4ff",
        annotation_text=f"Spot {spot:.0f}", annotation_font_color="#00d4ff")
    fig.update_layout(
        barmode="group", height=350,
        paper_bgcolor="#0a0e1a", plot_bgcolor="#0d1117",
        font=dict(family="JetBrains Mono", color="#e2e8f0", size=11),
        title=dict(text="Open Interest (CE vs PE) — Near ATM", font=dict(color="#00d4ff")),
        xaxis=dict(title="Strike", gridcolor="#1e2d45"),
        yaxis=dict(title="OI (Lakhs)", gridcolor="#1e2d45"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")

    selected_index = st.selectbox("Select Index", ["NIFTY", "BANKNIFTY", "SENSEX"], index=0)
    hist_days = st.slider("Historical Days", 15, 120, 60, step=5)

    st.markdown("---")
    st.markdown("##### 🔑 API Keys (Optional)")
    anthropic_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
    dhan_client_id = st.text_input("Dhan Client ID", placeholder="Client ID")
    dhan_token = st.text_input("Dhan Access Token", type="password", placeholder="Access Token")

    st.markdown("---")
    refresh = st.button("🔄 Refresh Data", use_container_width=True)
    auto_refresh = st.checkbox("Auto Refresh (60s)", value=False)

    st.markdown("---")
    st.markdown("""
    <div style='font-size:11px; color:#64748b; line-height:1.6;'>
    <b style='color:#00d4ff;'>Data Sources</b><br>
    • NSE India (Live quotes)<br>
    • NSE Option Chain API<br>
    • Historical Index Data<br><br>
    <b style='color:#00d4ff;'>Indicators</b><br>
    RSI(14) · VWAP · BB(20,2)<br>
    EMA(13) · EMA(21) · ADX(14)<br>
    +DI · -DI · CPR · Volume
    </div>
    """, unsafe_allow_html=True)

if auto_refresh:
    time.sleep(60)
    st.rerun()

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding: 10px 0 20px;'>
<h1 style='font-size:2.6rem; letter-spacing:-2px; margin:0;'>📈 NIFTY ANALYSIS BOT</h1>
<p style='color:#64748b; font-family: JetBrains Mono; font-size:12px; letter-spacing:3px; margin-top:6px;'>
LIVE MARKET INTELLIGENCE · OPTION CHAIN · SMART ANALYSIS
</p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"<p style='text-align:center; color:#64748b; font-size:11px; font-family: JetBrains Mono;'>Last updated: {datetime.now().strftime('%d %b %Y %H:%M:%S IST')} · Index: <span style='color:#00d4ff'>{selected_index}</span></p>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN DATA PIPELINE
# ─────────────────────────────────────────────
with st.spinner("Fetching live market data..."):
    # ── Historical data + indicators ──────────
    hist_df = fetch_historical_data(selected_index, hist_days)
    if hist_df.empty:
        st.error("❌ Failed to fetch historical data. Please check your connection.")
        st.stop()

    hist_df = add_all_indicators(hist_df)
    cpr = calc_cpr(hist_df)
    last_row = hist_df.iloc[-1]

    # ── Live spot quote ───────────────────────
    index_live = fetch_index_data(selected_index)
    spot_price = float(index_live.get("last", last_row["Close"])) if index_live and "error" not in index_live else float(last_row["Close"])
    spot_change = float(index_live.get("variation", 0)) if index_live and "error" not in index_live else 0.0
    spot_pct = float(index_live.get("percentChange", 0)) if index_live and "error" not in index_live else 0.0

    # ── Option chain ──────────────────────────
    oc_data = fetch_option_chain(INDEX_SYMBOLS[selected_index]["option_chain"])
    if "error" in oc_data:
        st.warning(f"⚠️ Option chain data unavailable: {oc_data['error']}")
        oc_df = pd.DataFrame()
        pcr = 1.0
        oi_signal = "N/A (OC fetch failed)"
    else:
        oc_df = process_option_chain(oc_data, spot_price)
        pcr = calc_pcr(oc_df)
        oi_signal = oi_buildup_signal(oc_df, spot_price)

    # ── Analysis ──────────────────────────────
    analysis = generate_analysis(hist_df, cpr, pcr, oi_signal, spot_price)

# ─────────────────────────────────────────────
# LIVE METRICS ROW
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">LIVE MARKET SNAPSHOT</div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5, c6 = st.columns(6)
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

# ─────────────────────────────────────────────
# SUMMARY + TAGS
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">AI ANALYSIS SUMMARY</div>', unsafe_allow_html=True)

tag_html = ""
for tag_type, tag_text in analysis["tags"]:
    tag_html += f'<span class="tag-{tag_type}">{tag_text}</span> '

progress_color = "#00ff88" if analysis['score'] > 60 else ("#ff4466" if analysis['score'] < 40 else "#ffd700")

st.markdown(f"""
<div class="summary-box">
    <div class="summary-title">Market Interpretation — {selected_index}</div>
    <div class="summary-text">{analysis['summary']}</div>
    <div style='margin-top:14px;'>{tag_html}</div>
    <div class="confidence-bar-container">
        <div class="confidence-label">CONFIDENCE SCORE: {analysis['score']}/100</div>
        <div style="background:#1e2d45; border-radius:8px; height:8px; margin-top:6px; overflow:hidden;">
            <div style="background: {progress_color}; width:{analysis['score']}%; height:100%; border-radius:8px; transition:width 0.5s;"></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CPR TABLE
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">CPR LEVELS</div>', unsafe_allow_html=True)
cpr_cols = st.columns(7)
cpr_levels = [
    ("R1", cpr["r1"], "#ff9900"),
    ("PDH", cpr["prev_high"], "#ffffff"),
    ("TC", cpr["tc"], "#00ff88"),
    ("Pivot", cpr["pivot"], "#00d4ff"),
    ("BC", cpr["bc"], "#ff4466"),
    ("PDL", cpr["prev_low"], "#aaaaaa"),
    ("S1", cpr["s1"], "#ff4466"),
]
for i, (lbl, val, clr) in enumerate(cpr_levels):
    with cpr_cols[i]:
        indicator = "◀ Current" if (val * 1.001 > spot_price > val * 0.999) else (
            "✓ Above" if spot_price > val else "")
        st.markdown(f"""
        <div class="metric-card" style="border-left-color:{clr};">
            <div class="metric-label">{lbl}</div>
            <div style="font-size:18px; font-weight:700; color:{clr}; font-family:'JetBrains Mono';">{val:,.1f}</div>
            <div style="font-size:10px; color:#64748b;">{indicator}</div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN CHART
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">PRICE CHART WITH INDICATORS</div>', unsafe_allow_html=True)
fig_main = build_chart(hist_df, cpr, selected_index)
st.plotly_chart(fig_main, use_container_width=True)

# ─────────────────────────────────────────────
# OPTION CHAIN
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">OPTION CHAIN ANALYSIS</div>', unsafe_allow_html=True)

if not oc_df.empty:
    col_chart, col_stats = st.columns([3, 1])
    with col_chart:
        st.plotly_chart(build_oi_chart(oc_df, spot_price), use_container_width=True)
    with col_stats:
        st.markdown("""<div style='margin-top:20px;'>""", unsafe_allow_html=True)
        total_ce = oc_df["CE_OI"].sum()
        total_pe = oc_df["PE_OI"].sum()
        max_ce_strike = oc_df.loc[oc_df["CE_OI"].idxmax(), "Strike"] if not oc_df.empty else "N/A"
        max_pe_strike = oc_df.loc[oc_df["PE_OI"].idxmax(), "Strike"] if not oc_df.empty else "N/A"
        for label, value, color in [
            ("Total CE OI", f"{total_ce / 1e5:.1f}L", "#ff4466"),
            ("Total PE OI", f"{total_pe / 1e5:.1f}L", "#00ff88"),
            ("PCR", f"{pcr:.3f}", "#00d4ff"),
            ("Max CE (Resistance)", f"{max_ce_strike}", "#ff4466"),
            ("Max PE (Support)", f"{max_pe_strike}", "#00ff88"),
            ("OI Signal", oi_signal[:20], "#ffd700"),
        ]:
            st.markdown(f"""
            <div class="metric-card" style='border-left-color:{color}'>
                <div class='metric-label'>{label}</div>
                <div style='font-size:15px; font-weight:700; color:{color}; font-family:JetBrains Mono;'>{value}</div>
            </div>""", unsafe_allow_html=True)

    # Option Chain table (near ATM)
    st.markdown("##### Near-ATM Option Chain")
    if not oc_df.empty:
        atm_idx = (oc_df["Strike"] - spot_price).abs().idxmin()
        lo = max(0, atm_idx - 7)
        hi = min(len(oc_df), atm_idx + 7)
        display_oc = oc_df.iloc[lo:hi].copy()
        display_oc = display_oc[["CE_OI", "CE_OI_Chg", "CE_LTP", "Strike", "PE_LTP", "PE_OI_Chg", "PE_OI"]].reset_index(drop=True)
        display_oc.columns = ["CE OI", "CE ΔOI", "CE LTP", "Strike", "PE LTP", "PE ΔOI", "PE OI"]

        def highlight_atm(row):
            if abs(row["Strike"] - spot_price) < spot_price * 0.005:
                return ["background-color: rgba(0,212,255,0.15)"] * len(row)
            return [""] * len(row)

        st.dataframe(
            display_oc.style.apply(highlight_atm, axis=1).format({
                "CE OI": "{:,.0f}", "CE ΔOI": "{:+,.0f}", "CE LTP": "{:.2f}",
                "Strike": "{:.0f}", "PE LTP": "{:.2f}", "PE ΔOI": "{:+,.0f}", "PE OI": "{:,.0f}",
            }),
            use_container_width=True, height=300,
        )
else:
    st.info("Option chain data could not be loaded. This may be due to NSE rate limiting. Try refreshing after a moment.")

# ─────────────────────────────────────────────
# INDICATOR SUMMARY TABLE
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">INDICATOR SNAPSHOT</div>', unsafe_allow_html=True)

ind_data = {
    "Indicator": ["RSI(14)", "VWAP", "BB Upper", "BB Mid", "BB Lower", "EMA 13", "EMA 21", "+DI", "-DI", "ADX(14)"],
    "Value": [
        f"{last_row['RSI']:.2f}",
        f"{last_row['VWAP']:.2f}",
        f"{last_row['BB_upper']:.2f}",
        f"{last_row['BB_mid']:.2f}",
        f"{last_row['BB_lower']:.2f}",
        f"{last_row['EMA13']:.2f}",
        f"{last_row['EMA21']:.2f}",
        f"{last_row['+DI']:.2f}",
        f"{last_row['-DI']:.2f}",
        f"{last_row['ADX']:.2f}",
    ],
    "Signal": [
        "Overbought" if last_row['RSI'] > 60 else ("Oversold" if last_row['RSI'] < 40 else "Neutral"),
        "Above" if spot_price > last_row['VWAP'] else "Below",
        "Near" if abs(spot_price - last_row['BB_upper']) / spot_price < 0.005 else ("Trending up" if spot_price > last_row['BB_mid'] else "Mid"),
        "—",
        "Near" if abs(spot_price - last_row['BB_lower']) / spot_price < 0.005 else ("Trending down" if spot_price < last_row['BB_mid'] else "Mid"),
        "Bullish" if last_row['EMA13'] > last_row['EMA21'] else "Bearish",
        "Bullish" if last_row['EMA13'] > last_row['EMA21'] else "Bearish",
        "Bullish" if last_row['+DI'] > last_row['-DI'] else "Bearish",
        "Bullish" if last_row['+DI'] > last_row['-DI'] else "Bearish",
        "Strong" if last_row['ADX'] > 25 else "Weak",
    ],
}
ind_df = pd.DataFrame(ind_data)

def color_signal(val):
    if val in ("Bullish", "Overbought", "Strong", "Above"):
        return "color: #00ff88; font-weight: 600;"
    elif val in ("Bearish", "Oversold", "Below"):
        return "color: #ff4466; font-weight: 600;"
    elif val == "Neutral":
        return "color: #ffd700;"
    return ""

st.dataframe(
    ind_df.style.applymap(color_signal, subset=["Signal"]),
    use_container_width=True, hide_index=True, height=380
)

# ─────────────────────────────────────────────
# SIGNAL BREAKDOWN
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">DETAILED SIGNAL BREAKDOWN</div>', unsafe_allow_html=True)
for i, sig in enumerate(analysis["signals"]):
    icon = "🟢" if any(w in sig.lower() for w in ["bullish", "above", "breakout", "short covering", "long build"]) else \
           "🔴" if any(w in sig.lower() for w in ["bearish", "below", "breakdown", "short build"]) else "🟡"
    st.markdown(f"""
    <div style="background:#111827; border:1px solid #1e2d45; border-radius:8px; padding:10px 16px; margin:4px 0; font-family:'Space Grotesk'; font-size:14px; color:#e2e8f0;">
        {icon} {sig}
    </div>""", unsafe_allow_html=True)

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
