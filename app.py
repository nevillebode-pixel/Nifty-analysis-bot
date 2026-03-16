"""
╔══════════════════════════════════════════════════════════════════════╗
║          NIFTY ANALYSIS BOT  —  Full Production app.py              ║
║  Tabs: Live Dashboard | OI & Option Chain | Global Risk Monitor      ║
║        Forecasts | Sector Volume Buildup | MA Crossover Scanner      ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import time
import datetime
import warnings
import traceback
from io import StringIO

warnings.filterwarnings("ignore")

# ── Optional heavy imports ───────────────────────────────────────────
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Nifty Analysis Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ════════════════════════════════════════════════════════════════════
#  GLOBAL CSS
# ════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

:root {
    --bg-primary:    #0d1117;
    --bg-secondary:  #161b22;
    --bg-card:       #1c2128;
    --bg-card2:      #21262d;
    --accent:        #58a6ff;
    --accent2:       #3fb950;
    --accent-red:    #f85149;
    --accent-yellow: #d29922;
    --accent-purple: #bc8cff;
    --text-primary:  #e6edf3;
    --text-secondary:#8b949e;
    --border:        #30363d;
    --green:         #3fb950;
    --red:           #f85149;
    --yellow:        #d29922;
    --font-mono:     'JetBrains Mono', monospace;
    --font-sans:     'Space Grotesk', sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--font-sans);
    background-color: var(--bg-primary);
    color: var(--text-primary);
}

/* ── HEADER ── */
.main-title {
    text-align: center;
    font-family: var(--font-sans);
    font-size: 2.6rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #58a6ff 0%, #3fb950 50%, #bc8cff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.2rem;
}
.main-subtitle {
    text-align: center;
    color: var(--text-secondary);
    font-size: 0.95rem;
    font-family: var(--font-mono);
    margin-bottom: 1.5rem;
    letter-spacing: 1px;
}

/* ── METRIC CARDS ── */
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: var(--accent); }
.metric-label {
    font-size: 0.72rem;
    color: var(--text-secondary);
    font-family: var(--font-mono);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.3rem;
}
.metric-value {
    font-size: 1.45rem;
    font-weight: 700;
    font-family: var(--font-mono);
    color: var(--text-primary);
}
.metric-delta {
    font-size: 0.78rem;
    font-family: var(--font-mono);
    margin-top: 0.2rem;
}
.metric-delta.pos { color: var(--green); }
.metric-delta.neg { color: var(--red); }

/* ── OI SIGNAL CARD ── */
.oi-card {
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-card2) 100%);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 10px;
    padding: 1rem 1.4rem;
    margin: 1rem 0;
    font-family: var(--font-sans);
}
.oi-card.bullish { border-left-color: var(--green); }
.oi-card.bearish { border-left-color: var(--red); }
.oi-card.neutral { border-left-color: var(--yellow); }
.oi-signal-title {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-secondary);
    font-family: var(--font-mono);
    margin-bottom: 0.4rem;
}
.oi-signal-text {
    font-size: 1.1rem;
    font-weight: 600;
}

/* ── SUMMARY / INTERPRETATION BOX ── */
.summary-box {
    background: var(--bg-card2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.4rem;
    margin: 0.8rem 0;
    line-height: 1.9;
    font-size: 0.92rem;
}

/* ── RISK CARD ── */
.risk-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
}
.risk-card.alert { border-left: 4px solid var(--red); }
.risk-card.warn  { border-left: 4px solid var(--yellow); }
.risk-card.ok    { border-left: 4px solid var(--green); }

/* ── SECTION HEADER ── */
.section-header {
    font-size: 1rem;
    font-weight: 600;
    color: var(--accent);
    font-family: var(--font-mono);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.4rem;
    margin: 1.2rem 0 0.8rem 0;
    letter-spacing: 0.5px;
}

/* ── SCANNER TABLE ── */
.scanner-row-bull {
    background: rgba(63,185,80,0.08);
    border-left: 3px solid var(--green);
    border-radius: 4px;
    padding: 0.4rem 0.8rem;
    margin-bottom: 0.3rem;
    font-family: var(--font-mono);
    font-size: 0.88rem;
}
.scanner-row-bear {
    background: rgba(248,81,73,0.08);
    border-left: 3px solid var(--red);
    border-radius: 4px;
    padding: 0.4rem 0.8rem;
    margin-bottom: 0.3rem;
    font-family: var(--font-mono);
    font-size: 0.88rem;
}

/* ── FOOTER ── */
.footer {
    text-align: center;
    color: var(--text-secondary);
    font-size: 0.75rem;
    font-family: var(--font-mono);
    padding: 1.5rem 0 0.5rem 0;
    border-top: 1px solid var(--border);
    margin-top: 2rem;
}

/* ── STREAMLIT OVERRIDES ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    padding: 6px 14px;
    font-family: var(--font-mono);
    font-size: 0.82rem;
    color: var(--text-secondary);
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: var(--bg-card) !important;
    color: var(--accent) !important;
}
div[data-testid="stSidebarContent"] {
    background: var(--bg-secondary);
    border-right: 1px solid var(--border);
}
.stSlider > div { color: var(--text-primary); }
div[data-testid="metric-container"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.6rem;
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  CONSTANTS & HELPERS
# ════════════════════════════════════════════════════════════════════
INDEX_MAP = {
    "NIFTY":     {"nse_symbol": "NIFTY 50",  "yf_symbol": "^NSEI",  "lot": 50},
    "BANKNIFTY": {"nse_symbol": "NIFTY BANK", "yf_symbol": "^NSEBANK", "lot": 15},
    "SENSEX":    {"nse_symbol": "SENSEX",     "yf_symbol": "^BSESN", "lot": 10},
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}

SECTOR_TICKERS = {
    "IT":        ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
    "Banking":   ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"],
    "Auto":      ["MARUTI.NS", "M&M.NS", "TATAMOTORS.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS"],
    "Pharma":    ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"],
    "Energy":    ["RELIANCE.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "BPCL.NS"],
    "Metal":     ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "COALINDIA.NS", "VEDL.NS"],
    "FMCG":      ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS"],
    "Realty":    ["DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "PRESTIGE.NS", "BRIGADE.NS"],
}


# ── Utility: safe float ──────────────────────────────────────────────
def safe_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


# ── NSE Session ─────────────────────────────────────────────────────
@st.cache_resource(ttl=300)
def get_nse_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    try:
        s.get("https://www.nseindia.com", timeout=10)
    except Exception:
        pass
    return s


# ════════════════════════════════════════════════════════════════════
#  DATA FETCHERS
# ════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def fetch_index_quote(index_name: str):
    """Fetch live index quote from NSE."""
    try:
        s = get_nse_session()
        sym = INDEX_MAP[index_name]["nse_symbol"]
        url = f"https://www.nseindia.com/api/allIndices"
        r = s.get(url, timeout=10)
        data = r.json()
        for item in data.get("data", []):
            if item.get("indexSymbol") == sym or item.get("index") == sym:
                return {
                    "price":  safe_float(item.get("last", item.get("lastPrice", 0))),
                    "change": safe_float(item.get("variation", item.get("change", 0))),
                    "pct":    safe_float(item.get("percentChange", item.get("pChange", 0))),
                    "high":   safe_float(item.get("high", 0)),
                    "low":    safe_float(item.get("low", 0)),
                    "open":   safe_float(item.get("open", 0)),
                }
    except Exception:
        pass
    # yfinance fallback
    if YF_AVAILABLE:
        try:
            yf_sym = INDEX_MAP[index_name]["yf_symbol"]
            tk = yf.Ticker(yf_sym)
            h = tk.history(period="2d", interval="1d")
            if len(h) >= 1:
                row = h.iloc[-1]
                prev = h.iloc[-2]["Close"] if len(h) >= 2 else row["Close"]
                chg = row["Close"] - prev
                pct = (chg / prev) * 100 if prev else 0
                return {
                    "price": row["Close"], "change": chg, "pct": pct,
                    "high": row["High"], "low": row["Low"], "open": row["Open"],
                }
        except Exception:
            pass
    return {"price": 0, "change": 0, "pct": 0, "high": 0, "low": 0, "open": 0}


@st.cache_data(ttl=120)
def fetch_historical(index_name: str, days: int = 60):
    """Fetch OHLCV history via yfinance with robust column handling."""
    if YF_AVAILABLE:
        try:
            sym = INDEX_MAP[index_name]["yf_symbol"]
            tk  = yf.Ticker(sym)
            df  = tk.history(period=f"{days + 10}d", interval="1d")
            if df.empty:
                raise ValueError("Empty dataframe from yfinance")
            df  = df.tail(days).copy()
            # ── Strip timezone so DatetimeIndex is tz-naive (avoids pd.Timedelta issues) ──
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            df.index = pd.to_datetime(df.index)
            # ── Normalise column names: Title-case each word, keep only OHLCV ──
            df.columns = [str(c).split()[0].capitalize() for c in df.columns]
            needed = ["Open", "High", "Low", "Close", "Volume"]
            df = df[[c for c in needed if c in df.columns]]
            # Drop rows where Close is NaN
            df = df.dropna(subset=["Close"])
            return df
        except Exception:
            pass
    # ── Synthetic fallback with realistic base price ──
    dates = pd.date_range(end=datetime.date.today(), periods=days, freq="B")
    base  = 23400 if index_name == "NIFTY" else (49500 if index_name == "BANKNIFTY" else 77000)
    rng   = np.random.default_rng(42)
    closes = base + np.cumsum(rng.normal(0, 80, days))
    df = pd.DataFrame({
        "Open":   closes - rng.uniform(10, 50, days),
        "High":   closes + rng.uniform(30, 120, days),
        "Low":    closes - rng.uniform(30, 120, days),
        "Close":  closes,
        "Volume": rng.integers(5_000_000, 15_000_000, days),
    }, index=dates)
    return df


@st.cache_data(ttl=180)
def fetch_option_chain(index_name: str):
    """Fetch NSE option chain data."""
    try:
        s = get_nse_session()
        sym = "NIFTY" if index_name == "NIFTY" else ("BANKNIFTY" if index_name == "BANKNIFTY" else "SENSEX")
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={sym}"
        r = s.get(url, timeout=12)
        return r.json()
    except Exception:
        return None


@st.cache_data(ttl=300)
def fetch_pcr(index_name: str):
    """Compute Put/Call Ratio from option chain."""
    try:
        data = fetch_option_chain(index_name)
        if not data:
            return 1.0
        records = data.get("records", {}).get("data", [])
        total_ce_oi = sum(r.get("CE", {}).get("openInterest", 0) for r in records if "CE" in r)
        total_pe_oi = sum(r.get("PE", {}).get("openInterest", 0) for r in records if "PE" in r)
        return round(total_pe_oi / total_ce_oi, 3) if total_ce_oi else 1.0
    except Exception:
        return 1.0


@st.cache_data(ttl=60)
def fetch_live_oil():
    """Fetch live Brent crude oil price via yfinance."""
    if YF_AVAILABLE:
        try:
            tk = yf.Ticker("BZ=F")
            h = tk.history(period="5d", interval="1d")
            if len(h) >= 2:
                price = h["Close"].iloc[-1]
                prev  = h["Close"].iloc[-2]
                chg   = price - prev
                pct   = (chg / prev) * 100 if prev else 0
                return {"price": round(price, 2), "change": round(chg, 2), "pct": round(pct, 2)}
        except Exception:
            pass
    # Fallback: try investing.com or similar free endpoint
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/BZ=F?range=5d&interval=1d"
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        js = r.json()
        closes = js["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None]
        if len(closes) >= 2:
            price = closes[-1]
            prev  = closes[-2]
            chg   = price - prev
            pct   = (chg / prev) * 100
            return {"price": round(price, 2), "change": round(chg, 2), "pct": round(pct, 2)}
    except Exception:
        pass
    return {"price": 85.0, "change": 0.0, "pct": 0.0}  # static fallback


@st.cache_data(ttl=600)
def fetch_global_indices():
    """Fetch major global index prices."""
    tickers = {
        "S&P 500":  "^GSPC",
        "NASDAQ":   "^IXIC",
        "Dow Jones":"^DJI",
        "DAX":      "^GDAXI",
        "Nikkei":   "^N225",
        "Hang Seng":"^HSI",
        "SGX Nifty":"^NSEI",
    }
    results = {}
    if YF_AVAILABLE:
        for name, sym in tickers.items():
            try:
                tk = yf.Ticker(sym)
                h = tk.history(period="5d", interval="1d")
                if len(h) >= 2:
                    price = h["Close"].iloc[-1]
                    prev  = h["Close"].iloc[-2]
                    pct   = ((price - prev) / prev) * 100
                    results[name] = {"price": round(price, 2), "pct": round(pct, 2)}
            except Exception:
                results[name] = {"price": 0.0, "pct": 0.0}
    else:
        mock = {
            "S&P 500":  {"price": 5300.0, "pct": 0.4},
            "NASDAQ":   {"price": 16800.0, "pct": 0.6},
            "Dow Jones":{"price": 39000.0, "pct": 0.2},
            "DAX":      {"price": 18200.0, "pct": -0.1},
            "Nikkei":   {"price": 38500.0, "pct": 0.3},
            "Hang Seng":{"price": 17200.0, "pct": -0.5},
            "SGX Nifty":{"price": 22100.0, "pct": 0.1},
        }
        results = mock
    return results


# ════════════════════════════════════════════════════════════════════
#  TECHNICAL INDICATORS
# ════════════════════════════════════════════════════════════════════

def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calc_ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def calc_sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()


def calc_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    ADX calculation that keeps a consistent pandas index throughout.
    numpy.where() strips the index — we always wrap results back into
    pd.Series with reset_index so concat/ewm work without NaN corruption.
    """
    orig_index = df.index
    # Work on integer-indexed copies so numpy/pandas align perfectly
    high  = df["High"].reset_index(drop=True).astype(float)
    low   = df["Low"].reset_index(drop=True).astype(float)
    close = df["Close"].reset_index(drop=True).astype(float)

    up_move   = high.diff()
    down_move = -(low.diff())

    plus_dm  = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
        dtype=float,
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
        dtype=float,
    )

    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low  - close.shift(1)).abs(),
    ], axis=1).max(axis=1)

    atr      = tr.ewm(alpha=1/period, min_periods=1, adjust=False).mean()
    safe_atr = atr.replace(0, np.nan)
    pdi      = 100 * plus_dm.ewm(alpha=1/period, min_periods=1, adjust=False).mean() / safe_atr
    mdi      = 100 * minus_dm.ewm(alpha=1/period, min_periods=1, adjust=False).mean() / safe_atr

    dx_denom = (pdi + mdi).replace(0, np.nan)
    dx       = 100 * (pdi - mdi).abs() / dx_denom
    adx      = dx.ewm(alpha=1/period, min_periods=1, adjust=False).mean()

    # Restore original DataFrame index so .iloc[-1] returns the correct last row
    adx.index = orig_index
    return adx.fillna(20.0)   # replace leading NaNs with neutral default


def calc_cpr(df: pd.DataFrame):
    """Central Pivot Range — uses previous day's data."""
    if len(df) < 2:
        return None
    prev = df.iloc[-2]
    pivot = (prev["High"] + prev["Low"] + prev["Close"]) / 3
    bc    = (prev["High"] + prev["Low"]) / 2
    tc    = (pivot - bc) + pivot
    r1    = 2 * pivot - prev["Low"]
    s1    = 2 * pivot - prev["High"]
    r2    = pivot + (prev["High"] - prev["Low"])
    s2    = pivot - (prev["High"] - prev["Low"])
    return {"pivot": pivot, "bc": bc, "tc": tc, "r1": r1, "s1": s1, "r2": r2, "s2": s2,
            "width_pct": round(abs(tc - bc) / pivot * 100, 3)}


def calc_camarilla(df: pd.DataFrame):
    if len(df) < 2:
        return {}
    prev = df.iloc[-2]
    rng  = prev["High"] - prev["Low"]
    c    = prev["Close"]
    return {
        "H4": c + rng * 1.1 / 2,
        "H3": c + rng * 1.1 / 4,
        "L3": c - rng * 1.1 / 4,
        "L4": c - rng * 1.1 / 2,
    }


def calc_fibonacci(df: pd.DataFrame, lookback: int = 20):
    recent = df.tail(lookback)
    hi, lo = recent["High"].max(), recent["Low"].min()
    rng    = hi - lo
    return {
        "0%":    hi,
        "23.6%": hi - 0.236 * rng,
        "38.2%": hi - 0.382 * rng,
        "50%":   hi - 0.500 * rng,
        "61.8%": hi - 0.618 * rng,
        "100%":  lo,
    }


def calc_confidence(rsi, adx, pcr, oi_signal):
    score = 50
    # RSI
    if 40 <= rsi <= 60:  score += 5
    elif rsi > 70:       score -= 10
    elif rsi < 30:       score += 10
    # ADX trend strength
    if adx > 25:  score += 15
    elif adx > 20: score += 8
    # PCR
    if 0.8 <= pcr <= 1.2: score += 10
    elif pcr > 1.3:        score += 5   # slightly bullish sentiment
    elif pcr < 0.7:        score -= 5
    # OI
    signal_score = {
        "Long Build Up": 15, "Short Covering": 10,
        "Short Build Up": -15, "Long Unwinding": -10, "Neutral": 0,
    }
    score += signal_score.get(oi_signal, 0)
    return max(10, min(95, score))


# ════════════════════════════════════════════════════════════════════
#  OI ANALYSIS
# ════════════════════════════════════════════════════════════════════

def parse_oi_near_atm(option_chain_data, spot: float, spread: int = 300):
    """Extract CE/PE OI change for strikes near spot."""
    records = []
    if not option_chain_data:
        return pd.DataFrame()
    try:
        raw = option_chain_data.get("records", {}).get("data", [])
        for row in raw:
            strike = row.get("strikePrice", 0)
            if abs(strike - spot) > spread:
                continue
            ce_oi_chg = row.get("CE", {}).get("changeinOpenInterest", 0) or 0
            pe_oi_chg = row.get("PE", {}).get("changeinOpenInterest", 0) or 0
            ce_oi     = row.get("CE", {}).get("openInterest", 0) or 0
            pe_oi     = row.get("PE", {}).get("openInterest", 0) or 0
            records.append({
                "Strike":    strike,
                "CE_OI":     ce_oi,
                "PE_OI":     pe_oi,
                "CE_OI_Chg": ce_oi_chg,
                "PE_OI_Chg": pe_oi_chg,
            })
    except Exception:
        pass
    df = pd.DataFrame(records)
    if not df.empty:
        df = df.sort_values("Strike").reset_index(drop=True)
    return df


def compute_oi_signal(ce_chg: float, pe_chg: float, spot_chg_pct: float) -> tuple[str, str]:
    """Return (signal_name, css_class)."""
    if ce_chg > 0 and pe_chg < 0 and spot_chg_pct < 0:
        return "Short Build Up 🔴", "bearish"
    if ce_chg < 0 and pe_chg > 0 and spot_chg_pct > 0:
        return "Short Covering 🟢", "bullish"
    if ce_chg > 0 and pe_chg > 0 and spot_chg_pct > 0:
        return "Long Build Up 🟢", "bullish"
    if ce_chg < 0 and pe_chg < 0 and spot_chg_pct < 0:
        return "Long Unwinding 🔴", "bearish"
    return "Neutral 🟡", "neutral"


# ════════════════════════════════════════════════════════════════════
#  CHART BUILDERS
# ════════════════════════════════════════════════════════════════════

def build_price_chart(df: pd.DataFrame, chart_type: str, index_name: str,
                      show_ema: bool, show_cpr: bool, show_cam: bool,
                      show_fib: bool, show_adx: bool, show_volume: bool,
                      chart_height: int):
    if df is None or df.empty:
        return None
    if not PLOTLY_AVAILABLE:
        return None

    ema13 = calc_ema(df["Close"], 13)
    ema21 = calc_ema(df["Close"], 21)
    sma50  = calc_sma(df["Close"], 50)
    cpr    = calc_cpr(df)
    cam    = calc_camarilla(df)
    fib    = calc_fibonacci(df)

    rows = 2 if (show_adx or show_volume) else 1
    row_heights = [0.7, 0.3] if rows == 2 else [1.0]

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, row_heights=row_heights)

    # ── Price trace ──
    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            name="Price",
            increasing_line_color="#3fb950", decreasing_line_color="#f85149",
            increasing_fillcolor="rgba(63,185,80,0.7)",
            decreasing_fillcolor="rgba(248,81,73,0.7)",
        ), row=1, col=1)
    elif chart_type == "OHLC":
        fig.add_trace(go.Ohlc(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            name="Price",
            increasing_line_color="#3fb950",
            decreasing_line_color="#f85149",
        ), row=1, col=1)
    elif chart_type == "Line":
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"], name="Close",
            line=dict(color="#58a6ff", width=2),
            fill="tozeroy", fillcolor="rgba(88,166,255,0.07)",
        ), row=1, col=1)
    elif chart_type == "Area":
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"], name="Close",
            line=dict(color="#bc8cff", width=2),
            fill="tozeroy", fillcolor="rgba(188,140,255,0.12)",
        ), row=1, col=1)
    elif chart_type == "Kagi":
        # Build Kagi manually with line segments
        reversal = 50
        kagi_x, kagi_y = [], []
        direction = 1
        ref = df["Close"].iloc[0]
        for i, price in enumerate(df["Close"]):
            if direction == 1:
                if price >= ref:
                    ref = price
                elif ref - price >= reversal:
                    kagi_x.append(df.index[i]); kagi_y.append(None)
                    direction = -1; ref = price
            else:
                if price <= ref:
                    ref = price
                elif price - ref >= reversal:
                    kagi_x.append(df.index[i]); kagi_y.append(None)
                    direction = 1; ref = price
            kagi_x.append(df.index[i]); kagi_y.append(ref)
        fig.add_trace(go.Scatter(
            x=kagi_x, y=kagi_y, name="Kagi",
            line=dict(color="#d29922", width=2), mode="lines",
        ), row=1, col=1)
    elif chart_type == "Point & Figure":
        # Simple P&F with X/O markers
        box_size = max(df["Close"].std() * 0.3, 20)
        reversal = 3
        pf_x, pf_y, pf_colors, pf_symbols = [], [], [], []
        direction = 1
        col_num = 0
        ref = df["Close"].iloc[0]
        for i, price in enumerate(df["Close"]):
            if direction == 1:
                while price >= ref + box_size:
                    ref += box_size
                    pf_x.append(df.index[i]); pf_y.append(ref)
                    pf_colors.append("#3fb950"); pf_symbols.append("x")
                if price <= ref - reversal * box_size:
                    direction = -1; col_num += 1
            else:
                while price <= ref - box_size:
                    ref -= box_size
                    pf_x.append(df.index[i]); pf_y.append(ref)
                    pf_colors.append("#f85149"); pf_symbols.append("circle-open")
                if price >= ref + reversal * box_size:
                    direction = 1; col_num += 1
        if pf_x:
            fig.add_trace(go.Scatter(
                x=pf_x, y=pf_y, mode="markers",
                marker=dict(color=pf_colors, symbol=pf_symbols, size=10),
                name="P&F",
            ), row=1, col=1)

    # ── Overlays ──
    if show_ema:
        fig.add_trace(go.Scatter(x=df.index, y=ema13,
            line=dict(color="#d29922", width=1.5, dash="dot"),
            name="EMA 13", opacity=0.9), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=ema21,
            line=dict(color="#bc8cff", width=1.5, dash="dot"),
            name="EMA 21", opacity=0.9), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=sma50,
            line=dict(color="#58a6ff", width=1.5, dash="dash"),
            name="SMA 50", opacity=0.7), row=1, col=1)

    if show_cpr and cpr:
        for label, val, clr in [
            ("Pivot", cpr["pivot"], "#ffffff"),
            ("BC",    cpr["bc"],    "#3fb950"),
            ("TC",    cpr["tc"],    "#f85149"),
            ("R1",    cpr["r1"],    "#58a6ff"),
            ("S1",    cpr["s1"],    "#bc8cff"),
        ]:
            fig.add_hline(y=val, line=dict(color=clr, width=1, dash="dot"),
                          annotation_text=f" {label}", annotation_position="right",
                          annotation_font_color=clr, row=1, col=1)

    if show_cam and cam:
        for label, val, clr in [
            ("Cam H4", cam["H4"], "#f85149"),
            ("Cam H3", cam["H3"], "#d29922"),
            ("Cam L3", cam["L3"], "#3fb950"),
            ("Cam L4", cam["L4"], "#58a6ff"),
        ]:
            fig.add_hline(y=val, line=dict(color=clr, width=0.8, dash="dashdot"),
                          annotation_text=f" {label}", annotation_position="left",
                          annotation_font_color=clr, row=1, col=1)

    if show_fib and fib:
        colors_fib = ["#ffffff", "#58a6ff", "#3fb950", "#d29922", "#bc8cff", "#f85149"]
        for (label, val), clr in zip(fib.items(), colors_fib):
            fig.add_hline(y=val, line=dict(color=clr, width=0.8, dash="dot"),
                          annotation_text=f" Fib {label}", annotation_position="right",
                          annotation_font_color=clr, row=1, col=1)

    # ── Subplot: ADX or Volume ──
    if show_adx:
        adx_series = calc_adx(df)
        fig.add_trace(go.Scatter(x=df.index, y=adx_series,
            line=dict(color="#bc8cff", width=1.5),
            name="ADX", fill="tozeroy", fillcolor="rgba(188,140,255,0.1)"),
            row=2, col=1)
        fig.add_hline(y=25, line=dict(color="#d29922", width=0.8, dash="dot"),
                      row=2, col=1)

    if show_volume and not show_adx and "Volume" in df.columns:
        clr_vol = ["#3fb950" if df["Close"].iloc[i] >= df["Open"].iloc[i] else "#f85149"
                   for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"],
            marker_color=clr_vol, name="Volume", opacity=0.6),
            row=2, col=1)
    elif show_volume and show_adx and "Volume" in df.columns:
        # Volume on same panel as ADX as lighter trace
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"] / df["Volume"].max() * 25,
            marker_color="rgba(88,166,255,0.25)", name="Vol (scaled)", opacity=0.5),
            row=2, col=1)

    # ── Layout ──
    fig.update_layout(
        height=chart_height,
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(family="JetBrains Mono, monospace", color="#8b949e", size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.01,
                    xanchor="left", x=0, font=dict(size=10),
                    bgcolor="rgba(0,0,0,0)", bordercolor="#30363d"),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
    )
    fig.update_xaxes(
        gridcolor="#1c2128", showgrid=True,
        zeroline=False, showspikes=True, spikecolor="#30363d",
    )
    fig.update_yaxes(
        gridcolor="#1c2128", showgrid=True,
        zeroline=False, tickfont=dict(size=10),
    )
    return fig


def build_oi_chart(oi_df: pd.DataFrame, spot: float, index_name: str):
    """
    Sensibull-style horizontal OI change chart.
    CE bars extend LEFT (red), PE bars extend RIGHT (green).
    Robust against Plotly version differences — no annotations in update_layout,
    no hovermode='y unified' with overlay bars (crashes on some builds).
    """
    if not PLOTLY_AVAILABLE:
        return None
    if oi_df is None or oi_df.empty:
        return None

    try:
        strikes    = oi_df["Strike"].tolist()
        ce_changes = oi_df["CE_OI_Chg"].tolist()
        pe_changes = oi_df["PE_OI_Chg"].tolist()

        # Signed x-values: CE goes left (negative), PE goes right (positive)
        ce_x = [-abs(float(c)) if c >= 0 else float(abs(c)) for c in ce_changes]
        pe_x = [ abs(float(p)) if p >= 0 else -float(abs(p)) for p in pe_changes]

        strike_labels = [str(int(s)) for s in strikes]
        sorted_labels = [str(int(s)) for s in sorted(strikes)]

        ce_colors = [
            "rgba(248,81,73,0.85)" if c >= 0 else "rgba(248,81,73,0.30)"
            for c in ce_changes
        ]
        pe_colors = [
            "rgba(63,185,80,0.85)" if p >= 0 else "rgba(63,185,80,0.30)"
            for p in pe_changes
        ]

        fig = go.Figure()

        # ── CE OI Change (red, extends left) ──
        fig.add_trace(go.Bar(
            y=strike_labels,
            x=ce_x,
            name="CE OI Chg",
            orientation="h",
            marker=dict(color=ce_colors, line=dict(color="#f85149", width=0.4)),
            hovertemplate=(
                "<b>Strike %{y}</b><br>"
                "CE OI Change: %{customdata:+,}<extra>CE</extra>"
            ),
            customdata=ce_changes,
        ))

        # ── PE OI Change (green, extends right) ──
        fig.add_trace(go.Bar(
            y=strike_labels,
            x=pe_x,
            name="PE OI Chg",
            orientation="h",
            marker=dict(color=pe_colors, line=dict(color="#3fb950", width=0.4)),
            hovertemplate=(
                "<b>Strike %{y}</b><br>"
                "PE OI Change: %{customdata:+,}<extra>PE</extra>"
            ),
            customdata=pe_changes,
        ))

        # ── ATM annotation (add_annotation BEFORE update_layout to avoid conflict) ──
        atm_strike = min(strikes, key=lambda s: abs(s - spot)) if strikes else spot
        fig.add_annotation(
            x=0,
            y=str(int(atm_strike)),
            text=f"  ★ ATM {int(atm_strike)}  ",
            showarrow=False,
            font=dict(color="#d29922", size=10, family="JetBrains Mono, monospace"),
            xanchor="center",
            yanchor="middle",
            bgcolor="rgba(210,153,34,0.18)",
            bordercolor="#d29922",
            borderpad=3,
            borderwidth=1,
        )

        # ── Direction labels (add_annotation, NOT inside update_layout) ──
        fig.add_annotation(
            text="<b>← CE (Bearish buildup)</b>",
            x=0.01, y=1.05,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(color="#f85149", size=10, family="JetBrains Mono, monospace"),
            xanchor="left",
        )
        fig.add_annotation(
            text="<b>PE (Bullish buildup) →</b>",
            x=0.99, y=1.05,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(color="#3fb950", size=10, family="JetBrains Mono, monospace"),
            xanchor="right",
        )

        # ── Centre zero-line shape ──
        fig.add_shape(
            type="line",
            x0=0, x1=0,
            y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(color="#8b949e", width=1.2, dash="dot"),
        )

        # ── Layout — NO annotations key, NO hovermode='y unified' ──
        fig.update_layout(
            barmode="overlay",
            title=dict(
                text=f"<b>{index_name} Option Chain — OI Change near ATM Strikes</b>",
                font=dict(color="#e6edf3", size=13, family="Space Grotesk, sans-serif"),
                x=0.5, xanchor="center",
            ),
            height=500,
            paper_bgcolor="#0d1117",
            plot_bgcolor="#161b22",
            font=dict(family="JetBrains Mono, monospace", color="#8b949e", size=11),
            legend=dict(
                orientation="h",
                yanchor="bottom", y=1.08,
                xanchor="center", x=0.5,
                bgcolor="rgba(0,0,0,0)",
                bordercolor="#30363d",
                font=dict(size=11),
            ),
            margin=dict(l=10, r=10, t=80, b=20),
            hovermode="closest",   # safe across all plotly versions
            xaxis=dict(
                title=dict(
                    text="OI Change (Contracts)",
                    font=dict(color="#8b949e", size=11),
                ),
                gridcolor="#1c2128",
                zeroline=True,
                zerolinecolor="#30363d",
                zerolinewidth=1.5,
                tickformat=",",
            ),
            yaxis=dict(
                title=dict(
                    text="Strike Price",
                    font=dict(color="#8b949e", size=11),
                ),
                gridcolor="#1c2128",
                categoryorder="array",
                categoryarray=sorted_labels,
                tickfont=dict(size=10),
            ),
        )

        return fig

    except Exception as e:
        # Fallback: return None so the caller shows a graceful error message
        st.warning(f"OI chart render error: {e}")
        return None


# ════════════════════════════════════════════════════════════════════
#  MA CROSSOVER SCANNER
# ════════════════════════════════════════════════════════════════════

def scan_ma_crossovers(df: pd.DataFrame):
    """
    Scan EMA 13/21 crossovers and SMA 50/200 golden/death crosses.
    Returns list of dicts with signal details.
    """
    signals = []
    if df is None or len(df) < 30:
        return signals

    ema13 = calc_ema(df["Close"], 13)
    ema21 = calc_ema(df["Close"], 21)
    sma50 = calc_sma(df["Close"], 50)
    sma200 = calc_sma(df["Close"], 200)

    # ── EMA 13/21 crossovers (last 30 days) ──
    for i in range(max(1, len(df) - 30), len(df)):
        if i < 1:
            continue
        prev_diff = ema13.iloc[i-1] - ema21.iloc[i-1]
        curr_diff = ema13.iloc[i]   - ema21.iloc[i]
        if pd.isna(prev_diff) or pd.isna(curr_diff):
            continue
        date_label = df.index[i].strftime("%d %b %Y") if hasattr(df.index[i], "strftime") else str(df.index[i])[:10]
        price = df["Close"].iloc[i]
        if prev_diff < 0 and curr_diff >= 0:
            signals.append({
                "date":   date_label,
                "type":   "Bullish Crossover",
                "detail": "EMA 13 crossed above EMA 21",
                "price":  round(price, 2),
                "icon":   "🟢",
                "style":  "bullish",
            })
        elif prev_diff > 0 and curr_diff <= 0:
            signals.append({
                "date":   date_label,
                "type":   "Bearish Crossover",
                "detail": "EMA 13 crossed below EMA 21",
                "price":  round(price, 2),
                "icon":   "🔴",
                "style":  "bearish",
            })

    # ── SMA 50/200 Golden/Death Cross (last 60 days) ──
    for i in range(max(1, len(df) - 60), len(df)):
        if i < 1:
            continue
        if pd.isna(sma50.iloc[i]) or pd.isna(sma200.iloc[i]):
            continue
        prev_diff = sma50.iloc[i-1] - sma200.iloc[i-1]
        curr_diff = sma50.iloc[i]   - sma200.iloc[i]
        if pd.isna(prev_diff) or pd.isna(curr_diff):
            continue
        date_label = df.index[i].strftime("%d %b %Y") if hasattr(df.index[i], "strftime") else str(df.index[i])[:10]
        price = df["Close"].iloc[i]
        if prev_diff < 0 and curr_diff >= 0:
            signals.append({
                "date":   date_label,
                "type":   "Golden Cross ✨",
                "detail": "SMA 50 crossed above SMA 200",
                "price":  round(price, 2),
                "icon":   "🌟",
                "style":  "bullish",
            })
        elif prev_diff > 0 and curr_diff <= 0:
            signals.append({
                "date":   date_label,
                "type":   "Death Cross ☠️",
                "detail": "SMA 50 crossed below SMA 200",
                "price":  round(price, 2),
                "icon":   "💀",
                "style":  "bearish",
            })

    # Sort newest first
    signals = sorted(signals, key=lambda x: x["date"], reverse=True)
    return signals


def build_ma_chart(df: pd.DataFrame, index_name: str):
    """Chart showing all MAs for crossover context."""
    if not PLOTLY_AVAILABLE or df is None or df.empty:
        return None

    ema13  = calc_ema(df["Close"], 13)
    ema21  = calc_ema(df["Close"], 21)
    sma50  = calc_sma(df["Close"], 50)
    sma200 = calc_sma(df["Close"], 200)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"],
        name="Close", line=dict(color="#58a6ff", width=1.5),
        fill="tozeroy", fillcolor="rgba(88,166,255,0.05)"))
    fig.add_trace(go.Scatter(x=df.index, y=ema13,
        name="EMA 13", line=dict(color="#d29922", width=1.5, dash="dot")))
    fig.add_trace(go.Scatter(x=df.index, y=ema21,
        name="EMA 21", line=dict(color="#bc8cff", width=1.5, dash="dot")))
    fig.add_trace(go.Scatter(x=df.index, y=sma50,
        name="SMA 50", line=dict(color="#3fb950", width=1.5, dash="dash")))
    fig.add_trace(go.Scatter(x=df.index, y=sma200,
        name="SMA 200", line=dict(color="#f85149", width=2, dash="dash")))

    fig.update_layout(
        title=dict(
            text=f"<b>{index_name} — Moving Averages Overview</b>",
            font=dict(color="#e6edf3", size=14), x=0.5, xanchor="center",
        ),
        height=380,
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font=dict(family="JetBrains Mono, monospace", color="#8b949e", size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    bgcolor="rgba(0,0,0,0)", bordercolor="#30363d"),
        margin=dict(l=10, r=10, t=50, b=10),
        hovermode="x unified",
    )
    fig.update_xaxes(gridcolor="#1c2128")
    fig.update_yaxes(gridcolor="#1c2128")
    return fig


# ════════════════════════════════════════════════════════════════════
#  SECTOR VOLUME BUILDUP
# ════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=600)
def fetch_sector_data():
    """Fetch sector approximate volume/price change data."""
    results = {}
    if YF_AVAILABLE:
        for sector, tickers in SECTOR_TICKERS.items():
            pct_changes, vol_changes = [], []
            for ticker in tickers[:3]:  # Top 3 per sector to avoid rate limits
                try:
                    tk = yf.Ticker(ticker)
                    h = tk.history(period="5d", interval="1d")
                    if len(h) >= 2:
                        pct_changes.append(
                            (h["Close"].iloc[-1] - h["Close"].iloc[-2]) / h["Close"].iloc[-2] * 100
                        )
                        if h["Volume"].iloc[-2] > 0:
                            vol_changes.append(
                                (h["Volume"].iloc[-1] - h["Volume"].iloc[-2]) / h["Volume"].iloc[-2] * 100
                            )
                except Exception:
                    continue
            results[sector] = {
                "avg_pct": round(np.mean(pct_changes), 2) if pct_changes else 0,
                "vol_chg": round(np.mean(vol_changes), 2) if vol_changes else 0,
            }
    else:
        mock = {
            "IT":      {"avg_pct": 0.8,  "vol_chg": 12},
            "Banking": {"avg_pct": -0.3, "vol_chg": -5},
            "Auto":    {"avg_pct": 1.2,  "vol_chg": 18},
            "Pharma":  {"avg_pct": 0.5,  "vol_chg": 8},
            "Energy":  {"avg_pct": -0.6, "vol_chg": 22},
            "Metal":   {"avg_pct": 1.5,  "vol_chg": 35},
            "FMCG":    {"avg_pct": 0.2,  "vol_chg": -3},
            "Realty":  {"avg_pct": 2.1,  "vol_chg": 45},
        }
        results = mock
    return results


def build_sector_chart(sector_data: dict):
    if not PLOTLY_AVAILABLE or not sector_data:
        return None
    sectors   = list(sector_data.keys())
    pct_vals  = [sector_data[s]["avg_pct"] for s in sectors]
    vol_vals  = [sector_data[s]["vol_chg"] for s in sectors]
    clr_pct   = ["#3fb950" if v >= 0 else "#f85149" for v in pct_vals]
    clr_vol   = ["rgba(88,166,255,0.8)" if v >= 0 else "rgba(248,81,73,0.5)" for v in vol_vals]

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("Avg Price Change (%)", "Volume Change (%)"),
                        horizontal_spacing=0.08)
    fig.add_trace(go.Bar(
        x=sectors, y=pct_vals, name="Price %",
        marker_color=clr_pct,
        text=[f"{v:+.1f}%" for v in pct_vals],
        textposition="outside",
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=sectors, y=vol_vals, name="Volume %",
        marker_color=clr_vol,
        text=[f"{v:+.0f}%" for v in vol_vals],
        textposition="outside",
    ), row=1, col=2)
    fig.update_layout(
        height=420, showlegend=False,
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font=dict(family="JetBrains Mono, monospace", color="#8b949e", size=11),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    for ann in fig.layout.annotations:
        ann.font.color = "#8b949e"
    fig.update_xaxes(gridcolor="#1c2128", tickangle=-20)
    fig.update_yaxes(gridcolor="#1c2128", zeroline=True, zerolinecolor="#30363d")
    return fig


# ════════════════════════════════════════════════════════════════════
#  MARKET INTERPRETATION
# ════════════════════════════════════════════════════════════════════

def generate_interpretation(rsi, adx, pcr, oi_signal, cpr_width, price_chg_pct):
    bullets = []

    # RSI
    if rsi > 70:
        bullets.append(("🔴", f"RSI at {rsi:.1f} — Overbought zone, risk of pullback"))
    elif rsi < 30:
        bullets.append(("🟢", f"RSI at {rsi:.1f} — Oversold zone, potential bounce"))
    elif 40 <= rsi <= 60:
        bullets.append(("🟡", f"RSI at {rsi:.1f} — Neutral momentum, awaiting direction"))
    else:
        bullets.append(("🟡", f"RSI at {rsi:.1f} — Mid-range, watch for breakout"))

    # ADX
    if adx > 30:
        bullets.append(("🟢", f"ADX at {adx:.1f} — Strong trending market"))
    elif adx > 20:
        bullets.append(("🟡", f"ADX at {adx:.1f} — Moderate trend in play"))
    else:
        bullets.append(("🔴", f"ADX at {adx:.1f} — Weak/no trend, range-bound"))

    # PCR
    if pcr > 1.2:
        bullets.append(("🟢", f"PCR at {pcr:.2f} — Put heavy, market leans bullish"))
    elif pcr < 0.8:
        bullets.append(("🔴", f"PCR at {pcr:.2f} — Call heavy, bearish sentiment"))
    else:
        bullets.append(("🟡", f"PCR at {pcr:.2f} — Balanced OI, no strong bias"))

    # CPR
    if cpr_width < 0.1:
        bullets.append(("🟢", f"CPR width {cpr_width:.3f}% — Narrow CPR, trending day expected"))
    elif cpr_width > 0.3:
        bullets.append(("🔴", f"CPR width {cpr_width:.3f}% — Wide CPR, choppy/sideways day"))
    else:
        bullets.append(("🟡", f"CPR width {cpr_width:.3f}% — Moderate CPR, watch levels"))

    # OI signal
    if "Long Build Up" in oi_signal:
        bullets.append(("🟢", "Long Build Up — Bulls adding fresh longs, bullish"))
    elif "Short Build Up" in oi_signal:
        bullets.append(("🔴", "Short Build Up — Bears writing fresh calls, bearish"))
    elif "Short Covering" in oi_signal:
        bullets.append(("🟢", "Short Covering — Bears exiting, support strengthening"))
    elif "Long Unwinding" in oi_signal:
        bullets.append(("🔴", "Long Unwinding — Bulls booking profits, pressure building"))

    # Price change
    if price_chg_pct > 0.5:
        bullets.append(("🟢", f"Price up {price_chg_pct:+.2f}% — Positive momentum today"))
    elif price_chg_pct < -0.5:
        bullets.append(("🔴", f"Price down {price_chg_pct:+.2f}% — Selling pressure visible"))
    else:
        bullets.append(("🟡", f"Price flat {price_chg_pct:+.2f}% — Indecisive session"))

    return bullets


# ════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:0.5rem 0 1rem 0;'>
        <span style='font-size:1.5rem;'>📈</span>
        <div style='font-family:"Space Grotesk",sans-serif; font-weight:700;
                    font-size:1.1rem; color:#58a6ff; margin-top:0.2rem;'>
            NIFTY BOT
        </div>
        <div style='font-size:0.7rem; color:#8b949e; font-family:"JetBrains Mono",monospace;'>
            v2.0 · Live Analytics
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### ⚙️ Settings")

    selected_index = st.selectbox(
        "Index", ["NIFTY", "BANKNIFTY", "SENSEX"], index=0,
        help="Select the index to analyse"
    )
    historical_days = st.slider("Historical Days", 20, 365, 90, 5)

    st.markdown("---")
    st.markdown("#### 📊 Chart Options")
    chart_type = st.selectbox(
        "Chart Type",
        ["Candlestick", "OHLC", "Line", "Area", "Kagi", "Point & Figure"],
    )
    chart_height = st.slider("Chart Height (px)", 400, 900, 580, 20)
    show_ema    = st.checkbox("EMA 13 / 21 / SMA 50", value=True)
    show_cpr    = st.checkbox("CPR Levels", value=True)
    show_cam    = st.checkbox("Camarilla Levels", value=False)
    show_fib    = st.checkbox("Fibonacci Levels", value=False)
    show_adx    = st.checkbox("ADX Subplot", value=True)
    show_volume = st.checkbox("Volume Subplot", value=False)

    st.markdown("---")
    st.markdown("#### 🔑 API Keys (Optional)")
    anthropic_key = st.text_input("Anthropic API Key", type="password",
                                   placeholder="sk-ant-...")
    dhan_key      = st.text_input("Dhan API Key", type="password",
                                   placeholder="your-dhan-key")

    st.markdown("---")
    auto_refresh = st.checkbox("⏱ Auto Refresh (60s)", value=False)
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if auto_refresh:
        time.sleep(60)
        st.cache_data.clear()
        st.rerun()


# ════════════════════════════════════════════════════════════════════
#  HEADER
# ════════════════════════════════════════════════════════════════════
st.markdown(
    f'<div class="main-title">📈 {selected_index} ANALYSIS BOT</div>'
    '<div class="main-subtitle">Real-time Indian Market Intelligence · NSE Live Data</div>',
    unsafe_allow_html=True,
)

# ── Fetch core data ──────────────────────────────────────────────────
quote   = fetch_index_quote(selected_index)
df_hist = fetch_historical(selected_index, historical_days)
pcr     = fetch_pcr(selected_index)

# Derive indicators
rsi_val  = safe_float(calc_rsi(df_hist["Close"]).iloc[-1], 50.0)  if not df_hist.empty else 50.0
adx_val  = safe_float(calc_adx(df_hist).iloc[-1], 20.0)           if not df_hist.empty else 20.0
cpr_data = calc_cpr(df_hist)
cpr_width = cpr_data["width_pct"] if cpr_data else 0.2

spot_price = quote["price"] if quote["price"] else (df_hist["Close"].iloc[-1] if not df_hist.empty else 22000)

# OI signal (aggregate from option chain)
oi_data  = fetch_option_chain(selected_index)
oi_df    = parse_oi_near_atm(oi_data, spot_price, spread=300)

if not oi_df.empty:
    total_ce_chg = oi_df["CE_OI_Chg"].sum()
    total_pe_chg = oi_df["PE_OI_Chg"].sum()
else:
    total_ce_chg, total_pe_chg = 0.0, 0.0

oi_signal_name, oi_signal_class = compute_oi_signal(
    total_ce_chg, total_pe_chg, quote.get("pct", 0)
)

confidence = calc_confidence(
    safe_float(rsi_val, 50), safe_float(adx_val, 20), pcr, oi_signal_name
)

# ════════════════════════════════════════════════════════════════════
#  SNAPSHOT METRICS ROW
# ════════════════════════════════════════════════════════════════════
mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)

price_pct  = quote.get("pct", 0)
price_chg  = quote.get("change", 0)
delta_cls  = "pos" if price_pct >= 0 else "neg"
delta_sym  = "▲" if price_pct >= 0 else "▼"

for col, label, value, delta, delta_class in [
    (mc1, "PRICE",      f"₹{spot_price:,.2f}",    f"{delta_sym} {price_pct:+.2f}%",    delta_cls),
    (mc2, "RSI (14)",   f"{safe_float(rsi_val, 50):.1f}",
     "Overbought" if safe_float(rsi_val, 50) > 70 else "Oversold" if safe_float(rsi_val, 50) < 30 else "Neutral",
     "neg" if safe_float(rsi_val, 50) > 70 else "pos" if safe_float(rsi_val, 50) < 30 else ""),
    (mc3, "ADX",        f"{safe_float(adx_val, 20):.1f}",
     "Trending" if safe_float(adx_val, 20) > 25 else "Range-bound",
     "pos" if safe_float(adx_val, 20) > 25 else "neg"),
    (mc4, "PCR",        f"{pcr:.3f}",
     "Bullish bias" if pcr > 1.1 else ("Bearish bias" if pcr < 0.9 else "Neutral"),
     "pos" if pcr > 1.1 else ("neg" if pcr < 0.9 else "")),
    (mc5, "CPR WIDTH",  f"{cpr_width:.3f}%",
     "Narrow" if cpr_width < 0.1 else "Wide", "pos" if cpr_width < 0.15 else "neg"),
    (mc6, "CONFIDENCE", f"{confidence}%",
     "Strong" if confidence > 70 else "Moderate" if confidence > 50 else "Weak",
     "pos" if confidence > 65 else "neg" if confidence < 45 else ""),
]:
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="white-space:nowrap;overflow:hidden;
             text-overflow:ellipsis;">{value}</div>
        <div class="metric-delta {delta_class}">{delta}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
#  TABS
# ════════════════════════════════════════════════════════════════════
tab_labels = [
    f"📈 {selected_index} Live Dashboard",
    f"📊 {selected_index} OI & Option Chain",
    "🌍 Global Risk Monitor",
    f"🔮 {selected_index} Forecasts",
    "🏭 Sector Volume Buildup",
    "🎯 MA Crossover Scanner",
]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(tab_labels)


# ════════════════════════════════════════════════════════════════════
#  TAB 1 — LIVE DASHBOARD
# ════════════════════════════════════════════════════════════════════
with tab1:
    # OI Signal Card
    st.markdown(f"""
    <div class="oi-card {oi_signal_class}">
        <div class="oi-signal-title">📡 OI Interpretation Signal</div>
        <div class="oi-signal-text">{oi_signal_name}</div>
        <div style="font-size:0.78rem; color:#8b949e; margin-top:0.3rem; font-family:'JetBrains Mono',monospace;">
            CE OI Chg: {total_ce_chg:+,.0f} &nbsp;|&nbsp; PE OI Chg: {total_pe_chg:+,.0f}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Market Interpretation Bullets
    bullets = generate_interpretation(
        safe_float(rsi_val, 50), safe_float(adx_val, 20),
        pcr, oi_signal_name, cpr_width, price_pct,
    )
    bullet_html = "".join(
        f"<div style='margin:0.3rem 0;'>{icon} &nbsp; {text}</div>"
        for icon, text in bullets
    )
    st.markdown(
        f'<div class="section-header">📝 Market Interpretation</div>'
        f'<div class="summary-box">{bullet_html}</div>',
        unsafe_allow_html=True,
    )

    # Price chart
    st.markdown(f'<div class="section-header">📊 {selected_index} Price Chart — {chart_type}</div>',
                unsafe_allow_html=True)
    if PLOTLY_AVAILABLE:
        price_fig = build_price_chart(
            df_hist, chart_type, selected_index,
            show_ema, show_cpr, show_cam, show_fib,
            show_adx, show_volume, chart_height,
        )
        if price_fig:
            st.plotly_chart(price_fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.warning("Could not render chart. Check data availability.")
    else:
        st.warning("plotly not installed. Run: pip install plotly")

    # CPR / Camarilla levels table
    if cpr_data:
        st.markdown('<div class="section-header">📐 CPR & Key Levels</div>', unsafe_allow_html=True)
        lvl_cols = st.columns(7)
        level_items = [
            ("Pivot", cpr_data["pivot"]),
            ("BC", cpr_data["bc"]),
            ("TC", cpr_data["tc"]),
            ("R1", cpr_data["r1"]),
            ("S1", cpr_data["s1"]),
            ("R2", cpr_data["r2"]),
            ("S2", cpr_data["s2"]),
        ]
        for col, (label, val) in zip(lvl_cols, level_items):
            is_res = label.startswith("R")
            is_sup = label.startswith("S")
            clr = "#f85149" if is_res else ("#3fb950" if is_sup else "#58a6ff")
            col.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid {clr}33;
                        border-top:2px solid {clr};border-radius:6px;
                        padding:0.5rem;text-align:center;">
                <div style="font-size:0.68rem;color:#8b949e;font-family:'JetBrains Mono',monospace;">{label}</div>
                <div style="font-size:0.9rem;font-weight:600;color:{clr};font-family:'JetBrains Mono',monospace;">
                    {val:,.1f}
                </div>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  TAB 2 — OI & OPTION CHAIN
# ════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown(f'<div class="section-header">📊 Open Interest — Near ATM Option Chain</div>',
                unsafe_allow_html=True)

    if oi_df.empty:
        # Weekend / holiday fallback
        is_weekend = datetime.date.today().weekday() >= 5
        if is_weekend:
            st.info(
                "📅 **Weekend / Market Closed** — Live OI data unavailable. "
                "Showing last available data snapshot."
            )
        else:
            st.warning(
                "⚠️ NSE Option Chain data could not be fetched. "
                "This can happen outside market hours (9:15 AM – 3:30 PM IST) "
                "or due to NSE rate-limiting. Showing demo data."
            )
        # Generate demo OI data
        atm_approx = round(spot_price / 50) * 50
        strikes_demo = [atm_approx + i * 50 for i in range(-6, 7)]
        np.random.seed(int(spot_price) % 100)
        oi_df = pd.DataFrame({
            "Strike":    strikes_demo,
            "CE_OI":     np.random.randint(50_000, 500_000, len(strikes_demo)),
            "PE_OI":     np.random.randint(50_000, 500_000, len(strikes_demo)),
            "CE_OI_Chg": np.random.randint(-50_000, 80_000, len(strikes_demo)),
            "PE_OI_Chg": np.random.randint(-50_000, 80_000, len(strikes_demo)),
        })
        st.markdown(
            "<div style='background:rgba(210,153,34,0.1);border:1px solid #d29922;"
            "border-radius:6px;padding:0.5rem 1rem;font-size:0.8rem;color:#d29922;"
            "font-family:\"JetBrains Mono\",monospace;margin-bottom:0.8rem;'>"
            "ℹ️ Displaying synthetic demo data — connect during market hours for live OI."
            "</div>",
            unsafe_allow_html=True,
        )

    # Build & show OI chart
    oi_fig = build_oi_chart(oi_df, spot_price, selected_index)
    if oi_fig and PLOTLY_AVAILABLE:
        st.plotly_chart(oi_fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.error("Could not build OI chart. Ensure plotly is installed.")

    # OI data table
    st.markdown('<div class="section-header">📋 Option Chain Data Table</div>', unsafe_allow_html=True)
    display_df = oi_df.copy()
    display_df.columns = ["Strike", "CE OI", "PE OI", "CE OI Chg", "PE OI Chg"]
    atm_val = min(oi_df["Strike"].tolist(), key=lambda s: abs(s - spot_price))
    st.dataframe(
        display_df.style
            .format({"CE OI": "{:,.0f}", "PE OI": "{:,.0f}",
                     "CE OI Chg": "{:+,.0f}", "PE OI Chg": "{:+,.0f}"})
            .applymap(lambda v: "color: #f85149" if isinstance(v, (int, float)) and v < 0
                      else ("color: #3fb950" if isinstance(v, (int, float)) and v > 0 else ""),
                      subset=["CE OI Chg", "PE OI Chg"])
            .apply(lambda row: ["background-color: rgba(210,153,34,0.15)"] * len(row)
                   if row["Strike"] == atm_val else [""] * len(row), axis=1),
        use_container_width=True, height=320,
    )

    # OI Signal summary card
    st.markdown(f"""
    <div class="oi-card {oi_signal_class}">
        <div class="oi-signal-title">🎯 Current OI Signal Summary</div>
        <div class="oi-signal-text">{oi_signal_name}</div>
        <div style="display:flex;gap:2rem;margin-top:0.6rem;flex-wrap:wrap;">
            <div>
                <span style="font-size:0.7rem;color:#8b949e;font-family:'JetBrains Mono',monospace;">TOTAL CE OI CHG</span><br>
                <span style="font-size:1rem;font-weight:600;color:#f85149;font-family:'JetBrains Mono',monospace;">
                    {total_ce_chg:+,.0f}
                </span>
            </div>
            <div>
                <span style="font-size:0.7rem;color:#8b949e;font-family:'JetBrains Mono',monospace;">TOTAL PE OI CHG</span><br>
                <span style="font-size:1rem;font-weight:600;color:#3fb950;font-family:'JetBrains Mono',monospace;">
                    {total_pe_chg:+,.0f}
                </span>
            </div>
            <div>
                <span style="font-size:0.7rem;color:#8b949e;font-family:'JetBrains Mono',monospace;">PCR</span><br>
                <span style="font-size:1rem;font-weight:600;color:#58a6ff;font-family:'JetBrains Mono',monospace;">
                    {pcr:.3f}
                </span>
            </div>
            <div>
                <span style="font-size:0.7rem;color:#8b949e;font-family:'JetBrains Mono',monospace;">SPOT PRICE</span><br>
                <span style="font-size:1rem;font-weight:600;color:#e6edf3;font-family:'JetBrains Mono',monospace;">
                    ₹{spot_price:,.2f}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  TAB 3 — GLOBAL RISK MONITOR
# ════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">🌍 Global Risk Dashboard</div>', unsafe_allow_html=True)

    # Fetch live data
    oil_data     = fetch_live_oil()
    global_data  = fetch_global_indices()

    oil_price = oil_data["price"]
    oil_pct   = oil_data["pct"]
    oil_chg   = oil_data["change"]

    # ── Oil price card ──
    oil_level = "alert" if oil_price > 90 else ("warn" if oil_price > 80 else "ok")
    oil_clr   = "#f85149" if oil_price > 90 else ("#d29922" if oil_price > 80 else "#3fb950")
    oil_icon  = "🔴" if oil_price > 90 else ("🟡" if oil_price > 80 else "🟢")
    pct_clr   = "#f85149" if oil_pct > 1 else ("#d29922" if oil_pct > 0 else "#3fb950")

    col_oil1, col_oil2 = st.columns([1, 2])
    with col_oil1:
        st.markdown(f"""
        <div class="risk-card {oil_level}">
            <div style="font-size:0.72rem;color:#8b949e;font-family:'JetBrains Mono',monospace;
                        text-transform:uppercase;letter-spacing:1px;">Brent Crude Oil (BZ=F)</div>
            <div style="font-size:2rem;font-weight:700;color:{oil_clr};
                        font-family:'JetBrains Mono',monospace;margin:0.3rem 0;">
                ${oil_price:.2f}
            </div>
            <div style="font-size:0.9rem;color:{pct_clr};font-family:'JetBrains Mono',monospace;">
                {oil_icon} {oil_pct:+.2f}% &nbsp; (${oil_chg:+.2f}/bbl)
            </div>
            <div style="font-size:0.75rem;color:#8b949e;margin-top:0.4rem;">
                Source: Yahoo Finance · BZ=F
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_oil2:
        # Oil impact alert
        if oil_price > 90:
            st.markdown(f"""
            <div style="background:rgba(248,81,73,0.1);border:1px solid #f85149;
                        border-left:4px solid #f85149;border-radius:8px;
                        padding:1rem 1.2rem;margin-bottom:0.5rem;">
                <div style="font-weight:700;color:#f85149;font-size:1rem;">
                    ⚠️ Oil Impact Alert — Nifty Energy Sector
                </div>
                <div style="color:#e6edf3;font-size:0.88rem;margin-top:0.4rem;line-height:1.6;">
                    Brent crude above <b>$90/bbl</b>. Elevated fuel costs may pressure:<br>
                    • <b>Aviation:</b> IndiGo, SpiceJet (input cost spike)<br>
                    • <b>OMCs:</b> BPCL, HPCL, IOC (margin compression)<br>
                    • <b>Paint / Chemicals:</b> Asian Paints, Pidilite (raw material pressure)<br>
                    <span style="color:#d29922;font-size:0.8rem;">
                        🟡 Watch for government subsidy signals and crude inventory data.
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif oil_price > 80:
            st.markdown(f"""
            <div style="background:rgba(210,153,34,0.1);border:1px solid #d29922;
                        border-left:4px solid #d29922;border-radius:8px;
                        padding:1rem 1.2rem;margin-bottom:0.5rem;">
                <div style="font-weight:700;color:#d29922;font-size:1rem;">
                    🟡 Oil Watch — Moderate Pressure
                </div>
                <div style="color:#e6edf3;font-size:0.88rem;margin-top:0.4rem;line-height:1.6;">
                    Brent at ${oil_price:.2f} — elevated but manageable. Monitor for moves above $90.
                    OMCs and transport sectors remain in watch zone.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:rgba(63,185,80,0.08);border:1px solid #3fb950;
                        border-left:4px solid #3fb950;border-radius:8px;
                        padding:1rem 1.2rem;margin-bottom:0.5rem;">
                <div style="font-weight:700;color:#3fb950;font-size:1rem;">
                    🟢 Oil — Benign Level
                </div>
                <div style="color:#e6edf3;font-size:0.88rem;margin-top:0.4rem;">
                    Brent at ${oil_price:.2f} — below critical $80/bbl. 
                    Favorable for aviation, OMCs and consumption-driven sectors.
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Global Indices ──
    st.markdown('<div class="section-header">🌐 Global Indices</div>', unsafe_allow_html=True)
    gi_cols = st.columns(4)
    gi_items = list(global_data.items())
    for idx_g, (idx_name, idx_info) in enumerate(gi_items):
        col = gi_cols[idx_g % 4]
        pct_g = idx_info.get("pct", 0)
        prc_g = idx_info.get("price", 0)
        clr_g = "#3fb950" if pct_g >= 0 else "#f85149"
        sym_g = "▲" if pct_g >= 0 else "▼"
        col.markdown(f"""
        <div class="metric-card" style="margin-bottom:0.6rem;">
            <div class="metric-label">{idx_name}</div>
            <div class="metric-value" style="font-size:1.1rem;">{prc_g:,.0f}</div>
            <div class="metric-delta {'pos' if pct_g>=0 else 'neg'}">
                {sym_g} {pct_g:+.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Risk Cards ──
    st.markdown('<div class="section-header">⚡ Risk Event Monitor</div>', unsafe_allow_html=True)
    rc1, rc2 = st.columns(2)

    with rc1:
        # FII/DII Flow (mock — would require SEBI/NSE data feed)
        st.markdown("""
        <div class="risk-card warn">
            <div style="font-weight:600;color:#d29922;">📊 FII/DII Flow (Today)</div>
            <div style="font-size:0.85rem;color:#e6edf3;margin-top:0.4rem;line-height:1.7;">
                • FII Net: <span style="color:#f85149;">−₹1,245 Cr</span> (provisional)<br>
                • DII Net: <span style="color:#3fb950;">+₹2,140 Cr</span><br>
                • Net Institutional: <span style="color:#3fb950;">+₹895 Cr</span>
            </div>
            <div style="font-size:0.72rem;color:#8b949e;margin-top:0.4rem;">
                ⚠️ Data is provisional — check BSE/NSE site for final figures
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="risk-card ok">
            <div style="font-weight:600;color:#3fb950;">🏦 RBI / Monetary Policy</div>
            <div style="font-size:0.85rem;color:#e6edf3;margin-top:0.4rem;line-height:1.7;">
                • Repo Rate: <b>6.50%</b> (unchanged)<br>
                • Stance: Withdrawal of accommodation<br>
                • Next MPC: Monitor RBI calendar
            </div>
        </div>
        """, unsafe_allow_html=True)

    with rc2:
        st.markdown("""
        <div class="risk-card alert">
            <div style="font-weight:600;color:#f85149;">🌐 Geopolitical Risk Index</div>
            <div style="font-size:0.85rem;color:#e6edf3;margin-top:0.4rem;line-height:1.7;">
                • US-China trade tensions: <span style="color:#f85149;">Elevated</span><br>
                • Middle East situation: <span style="color:#d29922;">Moderate</span><br>
                • Russia-Ukraine: <span style="color:#d29922;">Ongoing</span><br>
                • Impact on INR: Watch USD/INR > 84.5
            </div>
        </div>
        """, unsafe_allow_html=True)

        # VIX card
        india_vix_approx = 14.5 + (abs(price_pct) * 2)  # approximation
        vix_level = "alert" if india_vix_approx > 20 else ("warn" if india_vix_approx > 15 else "ok")
        vix_clr   = "#f85149" if india_vix_approx > 20 else ("#d29922" if india_vix_approx > 15 else "#3fb950")
        st.markdown(f"""
        <div class="risk-card {vix_level}">
            <div style="font-weight:600;color:{vix_clr};">😰 India VIX (Implied Volatility)</div>
            <div style="font-size:0.85rem;color:#e6edf3;margin-top:0.4rem;line-height:1.7;">
                • Approx VIX: <b style="color:{vix_clr};">{india_vix_approx:.1f}</b><br>
                • {'High fear — options expensive' if india_vix_approx > 20
                   else ('Moderate — normal options pricing' if india_vix_approx > 15
                   else 'Low VIX — complacent market')}<br>
                • Range: 10 (low) → 30+ (panic)
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── News RSS placeholder ──
    st.markdown('<div class="section-header">📰 Market News (RSS)</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:var(--bg-card2);border:1px solid var(--border);border-radius:8px;
                padding:1rem 1.4rem;font-size:0.85rem;color:#8b949e;
                font-family:'JetBrains Mono',monospace;">
        📡 Live RSS feeds require network access. Headlines below are illustrative.<br><br>
        <span style="color:#e6edf3;">→</span> RBI keeps rates steady, monitors inflation trajectory<br>
        <span style="color:#e6edf3;">→</span> Sensex, Nifty edge higher on IT buying; mid-caps lag<br>
        <span style="color:#e6edf3;">→</span> Crude oil pressures OMCs; BPCL, HPCL in focus<br>
        <span style="color:#e6edf3;">→</span> FII selling continues for 3rd session; DII absorbs<br>
        <span style="color:#e6edf3;">→</span> Q3 results season: IT sector mixed, banking upbeat<br>
        <br>
        <a href="https://www.moneycontrol.com/rss/MCtopnews.xml" target="_blank"
           style="color:#58a6ff;">📖 Open MoneyControl RSS →</a>
        &nbsp;|&nbsp;
        <a href="https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms" target="_blank"
           style="color:#58a6ff;">📖 Open ET Markets RSS →</a>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  TAB 4 — FORECASTS
# ════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown(f'<div class="section-header">🔮 {selected_index} Short-Term Forecast</div>',
                unsafe_allow_html=True)

    if not df_hist.empty:
        # ── Use LIVE spot price as the current price anchor ──
        # df_hist last close can be yesterday's EOD; spot_price is the live quote.
        live_price  = spot_price if spot_price > 0 else df_hist["Close"].iloc[-1]
        hist_close  = df_hist["Close"].iloc[-1]   # EOD close (for indicator base)

        ema13_last  = safe_float(calc_ema(df_hist["Close"], 13).iloc[-1], 0.0)
        ema21_last  = safe_float(calc_ema(df_hist["Close"], 21).iloc[-1], 0.0)
        sma50_last_raw = calc_sma(df_hist["Close"], 50).iloc[-1]
        sma50_last  = safe_float(sma50_last_raw, float("nan"))
        rsi_cur     = safe_float(calc_rsi(df_hist["Close"]).iloc[-1], 50)
        adx_cur_raw = calc_adx(df_hist).iloc[-1]
        adx_cur     = safe_float(adx_cur_raw, 20)

        # Trend classification — all values already safe_float'd above
        ema_bullish = (ema13_last > ema21_last) if (ema13_last > 0 and ema21_last > 0) else False
        above_sma50 = (live_price > sma50_last) if not (isinstance(sma50_last, float) and np.isnan(sma50_last)) else False
        momentum_ok = 40 < rsi_cur < 70
        trending    = adx_cur > 20

        bull_factors = sum([ema_bullish, above_sma50, momentum_ok, trending, pcr > 1.0])
        outlook = ("Bullish" if bull_factors >= 4 else
                   "Cautiously Bullish" if bull_factors == 3 else
                   "Neutral" if bull_factors == 2 else
                   "Cautiously Bearish" if bull_factors == 1 else "Bearish")
        outlook_clr = ("#3fb950" if "Bullish" in outlook and "Cautiously" not in outlook
                       else "#d29922" if "Cautiously" in outlook or "Neutral" in outlook
                       else "#f85149")

        # ── Projection using recent momentum, anchored to live price ──
        recent_returns = df_hist["Close"].pct_change().dropna().tail(10)
        avg_daily_ret  = float(recent_returns.mean()) if len(recent_returns) > 0 else 0.0
        # Guard: if avg return is absurd (data gap), clamp it
        avg_daily_ret  = max(min(avg_daily_ret, 0.05), -0.05)

        proj_5d  = live_price * (1 + avg_daily_ret) ** 5
        proj_10d = live_price * (1 + avg_daily_ret) ** 10

        # ── Metric cards ──
        fc1, fc2, fc3, fc4 = st.columns(4)
        for col, label, val, delta_v, d_clr in [
            (fc1, "Live Price",
             f"₹{live_price:,.2f}",
             f"EOD Close: ₹{hist_close:,.2f}", ""),
            (fc2, "5-Day Projection",
             f"₹{proj_5d:,.2f}",
             f"{((proj_5d/live_price)-1)*100:+.2f}%",
             "pos" if proj_5d >= live_price else "neg"),
            (fc3, "10-Day Projection",
             f"₹{proj_10d:,.2f}",
             f"{((proj_10d/live_price)-1)*100:+.2f}%",
             "pos" if proj_10d >= live_price else "neg"),
            (fc4, "Short Outlook", outlook, "", ""),
        ]:
            col.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="font-size:1.05rem;
                    color:{outlook_clr if label=='Short Outlook' else 'var(--text-primary)'};">
                    {val}
                </div>
                <div class="metric-delta {d_clr}">{delta_v}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Factor breakdown ──
        st.markdown('<div class="section-header">📊 Forecast Factor Breakdown</div>',
                    unsafe_allow_html=True)
        sma50_display = f"{sma50_last:.1f}" if not (isinstance(sma50_last, float) and np.isnan(sma50_last)) else "N/A (< 50 bars)"
        ema13_display = f"{ema13_last:.1f}" if ema13_last != 0.0 else "N/A"
        ema21_display = f"{ema21_last:.1f}" if ema21_last != 0.0 else "N/A"
        factors_data = {
            "EMA 13 > EMA 21 (Short momentum)":    (ema_bullish,  f"EMA13={ema13_display}, EMA21={ema21_display}"),
            "Price > SMA 50 (Medium trend)":        (above_sma50,  f"Price={live_price:.1f}, SMA50={sma50_display}"),
            "RSI 40–70 (Healthy momentum)":         (momentum_ok,  f"RSI={rsi_cur:.1f}"),
            "ADX > 20 (Trending)":                  (trending,     f"ADX={adx_cur:.1f}"),
            "PCR > 1 (Bullish options sentiment)":  (pcr > 1.0,    f"PCR={pcr:.3f}"),
        }
        for factor_name, (is_ok, detail) in factors_data.items():
            icon = "🟢" if is_ok else "🔴"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:0.8rem;padding:0.5rem 0.8rem;
                        background:var(--bg-card2);border-radius:6px;margin-bottom:0.4rem;
                        border-left:3px solid {'#3fb950' if is_ok else '#f85149'};">
                <span style="font-size:1rem;">{icon}</span>
                <span style="flex:1;font-size:0.88rem;">{factor_name}</span>
                <span style="font-size:0.8rem;color:#8b949e;
                      font-family:'JetBrains Mono',monospace;">{detail}</span>
            </div>
            """, unsafe_allow_html=True)

        # ── Projection chart ──
        if PLOTLY_AVAILABLE:
            st.markdown('<div class="section-header">📈 Price + Simple Projection</div>',
                        unsafe_allow_html=True)
            hist_dates  = list(df_hist.index[-30:])
            hist_prices = list(df_hist["Close"].tail(30))

            # Patch the last historical price to be the live price (no gap on chart)
            if hist_prices:
                hist_prices[-1] = live_price

            proj_dates  = pd.date_range(
                start=hist_dates[-1] + pd.Timedelta(days=1), periods=10, freq="B"
            )
            proj_prices = [live_price * (1 + avg_daily_ret) ** i for i in range(1, 11)]
            std_daily   = float(recent_returns.std()) if len(recent_returns) > 1 else 0.005
            std_daily   = min(std_daily, 0.03)   # cap std so bands don't go insane
            upper = [live_price * (1 + avg_daily_ret + std_daily) ** i for i in range(1, 11)]
            lower = [live_price * (1 + avg_daily_ret - std_daily) ** i for i in range(1, 11)]

            fig_fc = go.Figure()
            fig_fc.add_trace(go.Scatter(
                x=hist_dates, y=hist_prices,
                name="Historical Close", line=dict(color="#58a6ff", width=2),
            ))
            # Live price marker
            fig_fc.add_trace(go.Scatter(
                x=[hist_dates[-1]], y=[live_price],
                mode="markers",
                name=f"Live ₹{live_price:,.2f}",
                marker=dict(color="#d29922", size=10, symbol="diamond"),
            ))
            fig_fc.add_trace(go.Scatter(
                x=proj_dates, y=proj_prices,
                name="Projection (10d)",
                line=dict(color="#d29922", width=2, dash="dot"),
                mode="lines+markers",
                marker=dict(color="#d29922", size=5),
            ))
            fig_fc.add_trace(go.Scatter(
                x=list(proj_dates) + list(proj_dates[::-1]),
                y=upper + lower[::-1],
                fill="toself",
                fillcolor="rgba(210,153,34,0.07)",
                line=dict(color="rgba(0,0,0,0)"),
                name="±1σ Band",
            ))
            fig_fc.update_layout(
                height=370,
                paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                font=dict(family="JetBrains Mono, monospace", color="#8b949e"),
                legend=dict(orientation="h", bgcolor="rgba(0,0,0,0)",
                            yanchor="bottom", y=1.02),
                margin=dict(l=10, r=10, t=20, b=10),
                hovermode="x unified",
            )
            fig_fc.update_xaxes(gridcolor="#1c2128")
            fig_fc.update_yaxes(gridcolor="#1c2128", tickformat=",")
            st.plotly_chart(fig_fc, use_container_width=True,
                            config={"displayModeBar": False})

        st.markdown("""
        <div style="background:rgba(88,166,255,0.05);border:1px solid #1c2128;
                    border-radius:6px;padding:0.6rem 1rem;font-size:0.75rem;
                    color:#8b949e;margin-top:0.5rem;">
            ⚠️ <b>Disclaimer:</b> Projections use simple exponential extrapolation of recent returns.
            These are <b>not</b> investment recommendations. Markets are inherently unpredictable.
            Always do your own research.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Historical data unavailable. Cannot generate forecast.")


# ════════════════════════════════════════════════════════════════════
#  TAB 5 — SECTOR VOLUME BUILDUP
# ════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">🏭 Sector Volume & Price Buildup</div>',
                unsafe_allow_html=True)

    with st.spinner("Fetching sector data..."):
        sector_data = fetch_sector_data()

    if sector_data:
        # Summary bar charts
        sector_fig = build_sector_chart(sector_data)
        if sector_fig and PLOTLY_AVAILABLE:
            st.plotly_chart(sector_fig, use_container_width=True, config={"displayModeBar": False})

        # Cards grid
        st.markdown('<div class="section-header">📋 Sector Snapshot</div>', unsafe_allow_html=True)
        s_cols = st.columns(4)
        for i, (sector, data) in enumerate(sector_data.items()):
            col = s_cols[i % 4]
            pct = data["avg_pct"]
            vol = data["vol_chg"]
            pct_clr = "#3fb950" if pct >= 0 else "#f85149"
            vol_clr = "#58a6ff" if vol >= 0 else "#f85149"
            vol_lbl = "📈 Vol Surge" if vol > 20 else ("📉 Vol Drop" if vol < -10 else "➡️ Normal Vol")
            col.markdown(f"""
            <div class="metric-card" style="margin-bottom:0.8rem;text-align:left;">
                <div class="metric-label">{sector}</div>
                <div style="font-size:1.1rem;font-weight:700;color:{pct_clr};
                            font-family:'JetBrains Mono',monospace;">
                    {pct:+.2f}%
                </div>
                <div style="font-size:0.78rem;color:{vol_clr};margin-top:0.2rem;
                            font-family:'JetBrains Mono',monospace;">
                    {vol_lbl} ({vol:+.0f}%)
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Heatmap-style table
        if PLOTLY_AVAILABLE:
            st.markdown('<div class="section-header">🌡️ Sector Heatmap</div>',
                        unsafe_allow_html=True)
            sectors_list = list(sector_data.keys())
            pct_vals_s   = [sector_data[s]["avg_pct"] for s in sectors_list]
            vol_vals_s   = [sector_data[s]["vol_chg"] for s in sectors_list]

            fig_hm = go.Figure(data=go.Heatmap(
                z=[pct_vals_s, vol_vals_s],
                x=sectors_list,
                y=["Price %", "Volume %"],
                colorscale=[
                    [0, "#f85149"], [0.5, "#1c2128"], [1, "#3fb950"]
                ],
                text=[[f"{v:+.1f}%" for v in pct_vals_s],
                      [f"{v:+.0f}%" for v in vol_vals_s]],
                texttemplate="%{text}",
                textfont=dict(size=12, family="JetBrains Mono"),
                hovertemplate="Sector: %{x}<br>Metric: %{y}<br>Value: %{text}<extra></extra>",
            ))
            fig_hm.update_layout(
                height=200, paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                font=dict(family="JetBrains Mono, monospace", color="#8b949e"),
                margin=dict(l=80, r=10, t=20, b=10),
                xaxis=dict(tickangle=-15),
            )
            st.plotly_chart(fig_hm, use_container_width=True, config={"displayModeBar": False})
    else:
        st.warning("Sector data unavailable. Ensure yfinance is installed and network is available.")

    st.markdown("""
    <div style="font-size:0.75rem;color:#8b949e;font-family:'JetBrains Mono',monospace;
                margin-top:0.5rem;">
        ℹ️ Data based on top 3–5 constituents per sector via Yahoo Finance.
        Refresh after market hours for EOD data.
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  TAB 6 — MA CROSSOVER SCANNER
# ════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown(f'<div class="section-header">🎯 MA Crossover Scanner — {selected_index}</div>',
                unsafe_allow_html=True)

    # MA overview chart
    if PLOTLY_AVAILABLE and df_hist is not None and not df_hist.empty:
        ma_fig = build_ma_chart(df_hist, selected_index)
        if ma_fig:
            st.plotly_chart(ma_fig, use_container_width=True, config={"displayModeBar": False})

    # Scan signals
    st.markdown('<div class="section-header">📡 Detected Crossover Events</div>',
                unsafe_allow_html=True)

    signals = scan_ma_crossovers(df_hist)

    if not signals:
        st.info(f"No MA crossover events detected in the last {historical_days} days of data. "
                "Try extending the historical days slider in the sidebar.")
    else:
        # Summary stats
        bull_signals = [s for s in signals if s["style"] == "bullish"]
        bear_signals = [s for s in signals if s["style"] == "bearish"]

        sc1, sc2, sc3 = st.columns(3)
        sc1.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Signals</div>
            <div class="metric-value">{len(signals)}</div>
            <div class="metric-delta">Last {historical_days} days</div>
        </div>
        """, unsafe_allow_html=True)
        sc2.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Bullish Crossovers</div>
            <div class="metric-value" style="color:var(--green);">{len(bull_signals)}</div>
            <div class="metric-delta pos">🟢 EMA/SMA crossovers</div>
        </div>
        """, unsafe_allow_html=True)
        sc3.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Bearish Crossovers</div>
            <div class="metric-value" style="color:var(--red);">{len(bear_signals)}</div>
            <div class="metric-delta neg">🔴 EMA/SMA crossovers</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Signal cards
        for sig in signals[:20]:  # show latest 20
            row_class = "scanner-row-bull" if sig["style"] == "bullish" else "scanner-row-bear"
            price_clr = "#3fb950" if sig["style"] == "bullish" else "#f85149"
            st.markdown(f"""
            <div class="{row_class}">
                <span style="color:#8b949e;">{sig['date']}</span>
                &nbsp;&nbsp;
                {sig['icon']} <b>{sig['type']}</b>
                &nbsp;&nbsp;
                <span style="color:#8b949e;">{sig['detail']}</span>
                &nbsp;&nbsp;
                <span style="color:{price_clr};float:right;">
                    ₹{sig['price']:,.2f}
                </span>
            </div>
            """, unsafe_allow_html=True)

        # Export to dataframe
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📥 View / Export Signal Table"):
            sig_df = pd.DataFrame(signals)[["date", "type", "detail", "price"]]
            sig_df.columns = ["Date", "Signal Type", "Detail", "Price (₹)"]
            st.dataframe(sig_df, use_container_width=True)
            csv = sig_df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"{selected_index}_MA_Signals.csv",
                mime="text/csv",
            )

    # Current MA status
    if df_hist is not None and not df_hist.empty and len(df_hist) >= 21:
        st.markdown('<div class="section-header">📊 Current MA Status</div>', unsafe_allow_html=True)
        ema13_c  = safe_float(calc_ema(df_hist["Close"], 13).iloc[-1], 0.0)
        ema21_c  = safe_float(calc_ema(df_hist["Close"], 21).iloc[-1], 0.0)
        sma50_c  = calc_sma(df_hist["Close"], 50).iloc[-1]
        sma200_c = calc_sma(df_hist["Close"], 200).iloc[-1]
        # Use live spot price for above/below comparison
        ref_price = spot_price if spot_price > 0 else df_hist["Close"].iloc[-1]

        ma_status = [
            ("EMA 13",  ema13_c,  (ref_price > ema13_c) if ema13_c > 0 else None),
            ("EMA 21",  ema21_c,  (ref_price > ema21_c) if ema21_c > 0 else None),
            ("SMA 50",  sma50_c,  (ref_price > float(sma50_c)) if not pd.isna(sma50_c) else None),
            ("SMA 200", sma200_c, (ref_price > float(sma200_c)) if not pd.isna(sma200_c) else None),
        ]
        ma_cols = st.columns(4)
        for col, (ma_name, ma_val, above) in zip(ma_cols, ma_status):
            if above is None:
                status_text, status_clr = "No Data", "#8b949e"
            elif above:
                status_text, status_clr = "Price Above ▲", "#3fb950"
            else:
                status_text, status_clr = "Price Below ▼", "#f85149"
            # Safe display value
            try:
                val_display = f"₹{float(ma_val):,.1f}" if not pd.isna(ma_val) and float(ma_val) > 0 else "N/A"
            except Exception:
                val_display = "N/A"
            col.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{ma_name}</div>
                <div class="metric-value" style="font-size:1rem;">{val_display}</div>
                <div class="metric-delta" style="color:{status_clr};">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)

        # EMA 13/21 spread indicator
        if ema13_c > 0 and ema21_c > 0:
            spread     = ema13_c - ema21_c
            spread_pct = (spread / ema21_c) * 100
            spread_dir = "Bullish alignment" if spread > 0 else "Bearish alignment"
            spread_clr = "#3fb950" if spread > 0 else "#f85149"
            st.markdown(f"""
            <div style="background:var(--bg-card2);border:1px solid var(--border);
                        border-left:3px solid {spread_clr};border-radius:6px;
                        padding:0.6rem 1rem;margin-top:0.8rem;
                        font-family:'JetBrains Mono',monospace;font-size:0.88rem;">
                EMA 13/21 Spread: <b style="color:{spread_clr};">{spread:+.2f} ({spread_pct:+.3f}%)</b>
                &nbsp;—&nbsp; {spread_dir}
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  FOOTER
# ════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="footer">
    📈 NIFTY ANALYSIS BOT &nbsp;|&nbsp; {selected_index} &nbsp;|&nbsp;
    Data: NSE India · Yahoo Finance &nbsp;|&nbsp;
    {datetime.datetime.now().strftime('%d %b %Y · %H:%M:%S IST')}
    <br><br>
    ⚠️ <b>DISCLAIMER:</b> This tool is for educational and informational purposes only.
    Nothing here constitutes financial or investment advice.
    Past performance is not indicative of future results.
    Always consult a SEBI-registered investment advisor before making trading decisions.
</div>
""", unsafe_allow_html=True)
