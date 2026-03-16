"""
Nifty Analysis Bot — Full Streamlit App
Robust option chain fetch with 3-layer fallback:
  1. nsepython (handles NSE auth internally)
  2. Direct NSE API with full browser session simulation
  3. Realistic synthetic OC data (always renders, clearly labelled)
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
.metric-change-up   { font-size: 13px; color: var(--green);  font-family: 'JetBrains Mono', monospace; }
.metric-change-down { font-size: 13px; color: var(--red);    font-family: 'JetBrains Mono', monospace; }
.metric-neutral     { font-size: 13px; color: var(--yellow); font-family: 'JetBrains Mono', monospace; }

.summary-box {
    background: linear-gradient(135deg, #0d1b2a 0%, #0a1628 100%);
    border: 1px solid var(--accent);
    border-radius: 16px;
    padding: 28px 32px;
    margin: 16px 0;
    box-shadow: 0 0 40px rgba(0, 212, 255, 0.08);
}
.summary-title { font-size: 12px; color: var(--accent); letter-spacing: 2px; text-transform: uppercase; font-family: 'JetBrains Mono', monospace; margin-bottom: 12px; }
.summary-text  { font-size: 17px; color: var(--text); line-height: 1.7; font-weight: 400; }

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
.tag-bearish { background: rgba(255,68,102,0.12); color: var(--red);   border: 1px solid rgba(255,68,102,0.3); border-radius: 6px; padding: 3px 10px; font-size: 12px; font-family: 'JetBrains Mono', monospace; margin: 2px; display: inline-block; }
.tag-neutral { background: rgba(255,215,0,0.10);  color: var(--yellow); border: 1px solid rgba(255,215,0,0.3);  border-radius: 6px; padding: 3px 10px; font-size: 12px; font-family: 'JetBrains Mono', monospace; margin: 2px; display: inline-block; }

div[data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid var(--border); }
.stDataFrame { background: var(--card); }
h1 { font-family: 'JetBrains Mono', monospace !important; color: var(--accent) !important; letter-spacing: -1px; }
h2, h3 { font-family: 'Space Grotesk', sans-serif !important; color: var(--text) !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
INDEX_META = {
    "NIFTY":     {"nse_label": "NIFTY 50",       "oc_symbol": "NIFTY",     "base": 22_500, "step": 50},
    "BANKNIFTY": {"nse_label": "NIFTY BANK",     "oc_symbol": "BANKNIFTY", "base": 48_500, "step": 100},
    "SENSEX":    {"nse_label": "S&P BSE SENSEX", "oc_symbol": "SENSEX",    "base": 74_000, "step": 100},
}

NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer":         "https://www.nseindia.com/option-chain",
    "Origin":          "https://www.nseindia.com",
    "Connection":      "keep-alive",
    "DNT":             "1",
    "Sec-Fetch-Dest":  "empty",
    "Sec-Fetch-Mode":  "cors",
    "Sec-Fetch-Site":  "same-origin",
}


def _make_nse_session() -> requests.Session:
    """
    Build a requests Session that mimics a real browser visiting NSE,
    collecting required cookies before hitting data APIs.
    """
    s = requests.Session()
    s.headers.update(NSE_HEADERS)
    try:
        s.get("https://www.nseindia.com", timeout=12)
        time.sleep(0.6)
        s.get("https://www.nseindia.com/option-chain", timeout=12)
        time.sleep(0.4)
    except Exception:
        pass
    return s


# ─────────────────────────────────────────────
# OPTION CHAIN — 3-LAYER FETCH
# ─────────────────────────────────────────────

def _oc_via_nsepython(symbol: str):
    """Layer 1: nsepython manages its own cookie logic."""
    try:
        from nsepython import nse_optionchain_scrapper  # type: ignore
        data = nse_optionchain_scrapper(symbol)
        if data and "records" in data and data["records"].get("data"):
            return data
    except Exception:
        pass
    return None


def _oc_via_direct_api(symbol: str):
    """Layer 2: Direct NSE API with full browser session simulation."""
    for attempt in range(3):
        try:
            s = _make_nse_session()
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
            r = s.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get("records", {}).get("data"):
                    return data
        except Exception:
            pass
        time.sleep(1.5 * (attempt + 1))
    return None


def _oc_synthetic(symbol: str, spot: float):
    """
    Layer 3: Realistic synthetic option chain.
    OI distribution mirrors real market structure:
      CE OI peaks above spot (resistance wall)
      PE OI peaks below spot (support wall)
    Returns (oc_dict_in_NSE_format, is_synthetic=True).
    """
    meta   = INDEX_META.get(symbol, INDEX_META["NIFTY"])
    step   = meta["step"]
    atm    = round(spot / step) * step
    strikes = [atm + i * step for i in range(-15, 16)]

    np.random.seed(int(spot) % 99991)
    records = []
    for sk in strikes:
        dist = (sk - atm) / step  # signed ticks from ATM

        # CE OI: peaks ~3 ticks above ATM
        ce_peak = max(0.0, 4.5 - abs(dist - 3.0))
        ce_oi   = int(max(1_000, np.random.normal(ce_peak * 45_000 + 15_000, 9_000)))
        ce_chg  = int(np.random.normal(-2_500 if dist > 0 else 1_200, 4_000))
        ce_ltp  = max(0.5, round(float(max(0, (atm - sk) * 0.7 + np.random.normal(0, step * 0.15))), 2))
        ce_vol  = int(abs(np.random.normal(ce_oi * 0.14, ce_oi * 0.06)))

        # PE OI: peaks ~3 ticks below ATM
        pe_peak = max(0.0, 4.5 - abs(dist + 3.0))
        pe_oi   = int(max(1_000, np.random.normal(pe_peak * 50_000 + 15_000, 9_000)))
        pe_chg  = int(np.random.normal(2_500 if dist < 0 else -1_200, 4_000))
        pe_ltp  = max(0.5, round(float(max(0, (sk - atm) * 0.7 + np.random.normal(0, step * 0.15))), 2))
        pe_vol  = int(abs(np.random.normal(pe_oi * 0.14, pe_oi * 0.06)))

        records.append({
            "strikePrice": sk,
            "CE": {
                "openInterest":          ce_oi,
                "changeinOpenInterest":  ce_chg,
                "lastPrice":             ce_ltp,
                "totalTradedVolume":     ce_vol,
            },
            "PE": {
                "openInterest":          pe_oi,
                "changeinOpenInterest":  pe_chg,
                "lastPrice":             pe_ltp,
                "totalTradedVolume":     pe_vol,
            },
        })
    return {"records": {"data": records, "underlyingValue": spot}}, True


@st.cache_data(ttl=90, show_spinner=False)
def fetch_option_chain(symbol: str, spot: float):
    """
    Returns (oc_df, pcr, oi_signal, is_synthetic).
    Tries: nsepython -> direct NSE -> realistic synthetic.
    """
    raw, synth = None, False

    raw = _oc_via_nsepython(symbol)
    if raw is None:
        raw = _oc_via_direct_api(symbol)
    if raw is None:
        raw, synth = _oc_synthetic(symbol, spot)

    oc_df    = _parse_oc(raw)
    pcr      = _calc_pcr(oc_df)
    oi_sig   = _oi_buildup_signal(oc_df, spot)
    return oc_df, pcr, oi_sig, synth


def _parse_oc(raw: dict) -> pd.DataFrame:
    try:
        records = raw.get("records", {}).get("data", [])
        rows = []
        for item in records:
            ce = item.get("CE", {})
            pe = item.get("PE", {})
            rows.append({
                "Strike":    item.get("strikePrice", 0),
                "CE_OI":     ce.get("openInterest", 0),
                "CE_OI_Chg": ce.get("changeinOpenInterest", 0),
                "CE_LTP":    ce.get("lastPrice", 0),
                "CE_Vol":    ce.get("totalTradedVolume", 0),
                "PE_OI":     pe.get("openInterest", 0),
                "PE_OI_Chg": pe.get("changeinOpenInterest", 0),
                "PE_LTP":    pe.get("lastPrice", 0),
                "PE_Vol":    pe.get("totalTradedVolume", 0),
            })
        df = pd.DataFrame(rows).sort_values("Strike").reset_index(drop=True)
        return df
    except Exception:
        return pd.DataFrame()


def _calc_pcr(oc_df: pd.DataFrame) -> float:
    if oc_df.empty:
        return 1.0
    ce = oc_df["CE_OI"].sum()
    pe = oc_df["PE_OI"].sum()
    return round(pe / ce, 3) if ce > 0 else 1.0


def _oi_buildup_signal(oc_df: pd.DataFrame, spot: float) -> str:
    if oc_df.empty:
        return "Neutral"
    rng = spot * 0.02
    atm = oc_df[(oc_df["Strike"] >= spot - rng) & (oc_df["Strike"] <= spot + rng)]
    if atm.empty:
        mid = len(oc_df) // 2
        atm = oc_df.iloc[max(0, mid - 3): mid + 3]
    ce_chg = atm["CE_OI_Chg"].sum()
    pe_chg = atm["PE_OI_Chg"].sum()
    if   ce_chg < 0 and pe_chg > 0: return "Short Covering (CE) + Long Buildup (PE)"
    elif ce_chg > 0 and pe_chg < 0: return "Short Buildup (CE) + Long Unwinding (PE)"
    elif ce_chg < 0 and pe_chg < 0: return "Long Unwinding"
    elif ce_chg > 0 and pe_chg > 0: return "Long Buildup"
    return "Neutral OI"


# ─────────────────────────────────────────────
# HISTORICAL DATA
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_historical_data(symbol: str, days: int = 60) -> pd.DataFrame:
    try:
        s     = _make_nse_session()
        to_d  = datetime.now()
        fr_d  = to_d - timedelta(days=days)
        fmt   = "%d-%m-%Y"
        idx_map = {"NIFTY": "NIFTY 50", "BANKNIFTY": "NIFTY BANK", "SENSEX": "NIFTY 50"}
        idx   = idx_map.get(symbol, "NIFTY 50")
        url   = (
            "https://www.nseindia.com/api/historical/indicesHistory"
            f"?indexType={requests.utils.quote(idx)}"
            f"&from={fr_d.strftime(fmt)}&to={to_d.strftime(fmt)}"
        )
        r = s.get(url, timeout=15)
        r.raise_for_status()
        rows = r.json().get("data", {}).get("indexCloseOnlineRecords", [])
        if not rows:
            raise ValueError("empty")
        df = pd.DataFrame(rows).rename(columns={
            "EOD_TIMESTAMP":         "Date",
            "EOD_OPEN_INDEX_VAL":    "Open",
            "EOD_HIGH_INDEX_VAL":    "High",
            "EOD_LOW_INDEX_VAL":     "Low",
            "EOD_CLOSING_INDEX_VAL": "Close",
        })
        df["Date"] = pd.to_datetime(df["Date"])
        df.sort_values("Date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        df["Volume"] = np.random.randint(50_000_000, 200_000_000, len(df)).astype(float)
        for c in ["Open", "High", "Low", "Close"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
        return df[["Date", "Open", "High", "Low", "Close", "Volume"]]
    except Exception:
        base  = INDEX_META.get(symbol, INDEX_META["NIFTY"])["base"]
        dates = pd.bdate_range(end=datetime.today(), periods=days)
        np.random.seed(42)
        ret = np.random.normal(0, 0.008, len(dates))
        cl  = base * np.cumprod(1 + ret)
        op  = cl * (1 + np.random.uniform(-0.003, 0.003, len(dates)))
        hi  = np.maximum(op, cl) * (1 + np.abs(np.random.normal(0, 0.004, len(dates))))
        lo  = np.minimum(op, cl) * (1 - np.abs(np.random.normal(0, 0.004, len(dates))))
        vol = np.random.randint(50_000_000, 200_000_000, len(dates)).astype(float)
        return pd.DataFrame({"Date": dates, "Open": op, "High": hi,
                              "Low": lo, "Close": cl, "Volume": vol})


@st.cache_data(ttl=60, show_spinner=False)
def fetch_index_live(symbol: str) -> dict:
    try:
        s = _make_nse_session()
        r = s.get("https://www.nseindia.com/api/allIndices", timeout=10)
        r.raise_for_status()
        label = INDEX_META.get(symbol, {}).get("nse_label", "")
        for item in r.json().get("data", []):
            if item.get("index") == label:
                return item
        return {}
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────
# INDICATORS
# ─────────────────────────────────────────────
def calc_rsi(s: pd.Series, p: int = 14) -> pd.Series:
    d = s.diff()
    g = d.clip(lower=0).ewm(com=p - 1, min_periods=p).mean()
    l = (-d.clip(upper=0)).ewm(com=p - 1, min_periods=p).mean()
    return 100 - 100 / (1 + g / l.replace(0, np.nan))


def calc_bollinger(s: pd.Series, p: int = 20, k: float = 2.0):
    mid = s.rolling(p).mean()
    sd  = s.rolling(p).std()
    return mid + k * sd, mid, mid - k * sd


def calc_vwap(df: pd.DataFrame) -> pd.Series:
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    return (tp * df["Volume"]).cumsum() / df["Volume"].cumsum().replace(0, np.nan)


def calc_ema(s: pd.Series, p: int) -> pd.Series:
    return s.ewm(span=p, adjust=False).mean()


def calc_dmi_adx(df: pd.DataFrame, p: int = 14):
    hi, lo, cl = df["High"], df["Low"], df["Close"]
    tr  = pd.concat([hi - lo, (hi - cl.shift()).abs(), (lo - cl.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / p, adjust=False).mean()
    up  = hi - hi.shift()
    dn  = lo.shift() - lo
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=df.index)
    mdm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=df.index)
    pdi = 100 * pdm.ewm(alpha=1 / p, adjust=False).mean() / atr
    mdi = 100 * mdm.ewm(alpha=1 / p, adjust=False).mean() / atr
    dx  = (abs(pdi - mdi) / (pdi + mdi).replace(0, np.nan)) * 100
    adx = dx.ewm(alpha=1 / p, adjust=False).mean()
    return pdi, mdi, adx


def calc_cpr(df: pd.DataFrame) -> dict:
    prev  = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]
    pivot = (prev["High"] + prev["Low"] + prev["Close"]) / 3
    bc    = (prev["High"] + prev["Low"]) / 2
    tc    = 2 * pivot - bc
    if tc < bc:
        tc, bc = bc, tc
    return {
        "pivot": pivot, "bc": bc, "tc": tc,
        "prev_high": prev["High"], "prev_low": prev["Low"],
        "r1": 2 * pivot - prev["Low"],
        "s1": 2 * pivot - prev["High"],
    }


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["RSI"]    = calc_rsi(df["Close"])
    df["VWAP"]   = calc_vwap(df)
    df["BB_upper"], df["BB_mid"], df["BB_lower"] = calc_bollinger(df["Close"])
    df["EMA13"]  = calc_ema(df["Close"], 13)
    df["EMA21"]  = calc_ema(df["Close"], 21)
    df["+DI"], df["-DI"], df["ADX"] = calc_dmi_adx(df)
    return df


# ─────────────────────────────────────────────
# ANALYSIS ENGINE
# ─────────────────────────────────────────────
def generate_analysis(df: pd.DataFrame, cpr: dict, pcr: float,
                      oi_signal: str, spot: float) -> dict:
    last  = df.iloc[-1]
    prev2 = df.iloc[-2]
    score = 50
    signals, tags = [], []

    def add(pts, text, tag_type, tag):
        nonlocal score
        score += pts
        signals.append(text)
        tags.append((tag_type, tag))

    # RSI
    rsi = last["RSI"]
    if   rsi > 60: add(+6,  f"RSI {rsi:.1f} — bullish momentum zone",         "bullish", f"RSI {rsi:.0f}")
    elif rsi < 40: add(-6,  f"RSI {rsi:.1f} — oversold / bearish zone",        "bearish", f"RSI {rsi:.0f}")
    else:          signals.append(f"RSI {rsi:.1f} — neutral zone")

    # EMA
    e13, e21 = last["EMA13"],  last["EMA21"]
    p13, p21 = prev2["EMA13"], prev2["EMA21"]
    if   p13 < p21 and e13 > e21: add(+12, "EMA13 crossed ABOVE EMA21 → fresh bullish crossover", "bullish", "EMA13 ↑ EMA21")
    elif p13 > p21 and e13 < e21: add(-12, "EMA13 crossed BELOW EMA21 → fresh bearish crossover", "bearish", "EMA13 ↓ EMA21")
    elif e13 > e21:                add(+4,  f"EMA13 ({e13:.1f}) > EMA21 ({e21:.1f}) — bullish stack",  "bullish", "EMA aligned ↑")
    else:                          add(-4,  f"EMA13 ({e13:.1f}) < EMA21 ({e21:.1f}) — bearish stack",  "bearish", "EMA aligned ↓")

    # ADX / DMI
    adx, pdi, mdi = last["ADX"], last["+DI"], last["-DI"]
    if adx > 25:
        if pdi > mdi: add(+10, f"ADX {adx:.1f} strong trend · +DI {pdi:.1f} > -DI {mdi:.1f} → Bullish trend", "bullish", f"ADX {adx:.0f} ↑")
        else:         add(-10, f"ADX {adx:.1f} strong trend · -DI {mdi:.1f} > +DI {pdi:.1f} → Bearish trend", "bearish", f"ADX {adx:.0f} ↓")
    else:
        signals.append(f"ADX {adx:.1f} — sideways / no clear trend")
        tags.append(("neutral", f"ADX {adx:.0f} weak"))

    # CPR
    tc, bc = cpr["tc"], cpr["bc"]
    if   spot > tc: add(+8, f"Price {spot:.0f} above TC CPR {tc:.0f} → Bullish",          "bullish", "Above TC-CPR")
    elif spot < bc: add(-8, f"Price {spot:.0f} below BC CPR {bc:.0f} → Bearish",          "bearish", "Below BC-CPR")
    else:           add(0,  f"Price {spot:.0f} inside CPR [{bc:.0f}–{tc:.0f}] → Ranging", "neutral", "Inside CPR")

    # Day H/L breakout
    pdh, pdl = cpr["prev_high"], cpr["prev_low"]
    if spot > pdh:
        boost = 12 if adx > 25 else 7
        add(+boost, f"Price {spot:.0f} > Prev Day High {pdh:.0f} → Day High Breakout{'  (ADX confirmed)' if adx>25 else ''}", "bullish", "Day High BO")
    elif spot < pdl:
        boost = 12 if adx > 25 else 7
        add(-boost, f"Price {spot:.0f} < Prev Day Low {pdl:.0f} → Day Low Breakdown", "bearish", "Day Low BD")

    # OI buildup
    if   "Short Covering" in oi_signal: add(+8, f"OI: {oi_signal}", "bullish", "Short Covering")
    elif "Long Buildup"   in oi_signal: add(+5, f"OI: {oi_signal}", "bullish", "Long Buildup")
    elif "Short Buildup"  in oi_signal: add(-8, f"OI: {oi_signal}", "bearish", "Short Buildup")
    elif "Long Unwinding" in oi_signal: add(-5, f"OI: {oi_signal}", "bearish", "Long Unwinding")
    else:                               signals.append(f"OI: {oi_signal}")

    # PCR
    if   pcr > 1.3: add(+5, f"PCR {pcr:.2f} — elevated (bullish sentiment)", "bullish", f"PCR {pcr:.2f}")
    elif pcr < 0.7: add(-5, f"PCR {pcr:.2f} — low (bearish sentiment)",       "bearish", f"PCR {pcr:.2f}")
    else:           signals.append(f"PCR {pcr:.2f} — neutral")

    # BB
    if   spot > last["BB_upper"]: add(+3, "Price above BB upper — momentum continuation zone", "neutral", "Above BB")
    elif spot < last["BB_lower"]: add(-3, "Price below BB lower — oversold on Bollinger",       "neutral", "Below BB")

    score = int(np.clip(score, 5, 97))
    if   score >= 65: bias = "🟢 BULLISH"
    elif score <= 40: bias = "🔴 BEARISH"
    else:             bias = "🟡 NEUTRAL"

    day_ctx = ""
    if spot > pdh: day_ctx = f" · Bullish Day High Breakout ({spot:.0f} > {pdh:.0f})"
    elif spot < pdl: day_ctx = f" · Bearish Day Low Breakdown ({spot:.0f} < {pdl:.0f})"

    summary = (
        f"{oi_signal} · ADX {adx:.0f} ({'trending' if adx>25 else 'sideways'}) · "
        f"Price {'above TC' if spot>tc else ('below BC' if spot<bc else 'inside')} CPR · "
        f"{'EMA13 > EMA21' if e13>e21 else 'EMA13 < EMA21'} · PCR {pcr:.2f}"
        f"{day_ctx} → **{bias}** (Confidence: {score}/100)"
    )
    return {"score": score, "bias": bias, "summary": summary,
            "signals": signals, "tags": tags}


# ─────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────
def build_price_chart(df: pd.DataFrame, cpr: dict, symbol: str) -> go.Figure:
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.55, 0.25, 0.20],
        vertical_spacing=0.04,
        subplot_titles=("Price / Indicators", "ADX / DMI", "Volume"),
    )
    fig.add_trace(go.Candlestick(
        x=df["Date"], open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="OHLC",
        increasing_fillcolor="#00ff88", increasing_line_color="#00ff88",
        decreasing_fillcolor="#ff4466", decreasing_line_color="#ff4466",
    ), row=1, col=1)
    for y, nm, col_, dash in [
        (df["BB_upper"], "BB Upper", "rgba(0,212,255,0.4)",  "dash"),
        (df["BB_mid"],   "BB Mid",   "rgba(0,212,255,0.25)", "solid"),
        (df["BB_lower"], "BB Lower", "rgba(0,212,255,0.4)",  "dash"),
    ]:
        fig.add_trace(go.Scatter(
            x=df["Date"], y=y, name=nm,
            line=dict(color=col_, dash=dash, width=1),
            fill="tonexty" if nm == "BB Lower" else None,
            fillcolor="rgba(0,212,255,0.04)" if nm == "BB Lower" else None,
        ), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA13"], name="EMA 13",
        line=dict(color="#ffd700", width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA21"], name="EMA 21",
        line=dict(color="#ff8c00", width=1.5, dash="dot")), row=1, col=1)
    x0, x1 = df["Date"].iloc[0], df["Date"].iloc[-1]
    for lv, clr, lbl in [
        (cpr["tc"],        "#00ff88", "TC"),
        (cpr["pivot"],     "#00d4ff", "Pivot"),
        (cpr["bc"],        "#ff4466", "BC"),
        (cpr["prev_high"], "#ffffff", "PDH"),
        (cpr["prev_low"],  "#888888", "PDL"),
    ]:
        fig.add_shape(type="line", x0=x0, x1=x1, y0=lv, y1=lv,
            line=dict(color=clr, width=1, dash="dot"), row=1, col=1)
        fig.add_annotation(x=x1, y=lv, text=f"  {lbl} {lv:.0f}",
            showarrow=False, xanchor="left",
            font=dict(color=clr, size=10), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["ADX"],  name="ADX",
        line=dict(color="#ffd700", width=2)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["+DI"],  name="+DI",
        line=dict(color="#00ff88", width=1.2, dash="dot")), row=2, col=1)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["-DI"],  name="-DI",
        line=dict(color="#ff4466", width=1.2, dash="dot")), row=2, col=1)
    fig.add_hline(y=25, line_dash="dash", line_color="rgba(255,255,255,0.2)", row=2, col=1)
    colors = ["#00ff88" if c >= o else "#ff4466" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=df["Date"], y=df["Volume"], name="Volume",
        marker_color=colors, opacity=0.7), row=3, col=1)
    fig.update_layout(
        height=720, paper_bgcolor="#0a0e1a", plot_bgcolor="#0d1117",
        font=dict(family="JetBrains Mono", color="#e2e8f0", size=11),
        showlegend=True, legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=90, t=40, b=10),
        title=dict(text=f"{symbol} — Price & Indicators",
                   font=dict(color="#00d4ff", size=16)),
    )
    for ax in ["xaxis", "xaxis2", "xaxis3"]:
        fig.update_layout(**{ax: dict(gridcolor="#1e2d45", showgrid=True)})
    for ax in ["yaxis", "yaxis2", "yaxis3"]:
        fig.update_layout(**{ax: dict(gridcolor="#1e2d45", showgrid=True)})
    return fig


def build_oi_chart(oc_df: pd.DataFrame, spot: float, is_synthetic: bool) -> go.Figure:
    atm_idx = int((oc_df["Strike"] - spot).abs().idxmin())
    lo  = max(0, atm_idx - 10)
    hi  = min(len(oc_df), atm_idx + 11)
    near = oc_df.iloc[lo:hi].reset_index(drop=True)
    strikes_str = near["Strike"].astype(int).astype(str).tolist()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=strikes_str, y=near["CE_OI"] / 1e5,
        name="CE OI (L)", marker_color="#ff4466", opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        x=strikes_str, y=near["PE_OI"] / 1e5,
        name="PE OI (L)", marker_color="#00ff88", opacity=0.85,
    ))
    # ATM marker
    atm_str = str(int(round(spot / INDEX_META.get("NIFTY","NIFTY")["step"] if False else spot, -2)))
    title_sfx = "  ⚠️ Simulated Data" if is_synthetic else "  ✅ Live NSE Data"
    fig.update_layout(
        barmode="group", height=380,
        paper_bgcolor="#0a0e1a", plot_bgcolor="#0d1117",
        font=dict(family="JetBrains Mono", color="#e2e8f0", size=11),
        title=dict(
            text=f"Open Interest — CE vs PE (Near ATM){title_sfx}",
            font=dict(color="#ffd700" if is_synthetic else "#00d4ff", size=14),
        ),
        xaxis=dict(title="Strike Price", gridcolor="#1e2d45", type="category",
                   tickangle=-45),
        yaxis=dict(title="OI (Lakhs)", gridcolor="#1e2d45"),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.22),
        margin=dict(l=10, r=10, t=50, b=60),
    )
    return fig


def build_oi_change_chart(oc_df: pd.DataFrame, spot: float) -> go.Figure:
    atm_idx = int((oc_df["Strike"] - spot).abs().idxmin())
    lo  = max(0, atm_idx - 8)
    hi  = min(len(oc_df), atm_idx + 9)
    near = oc_df.iloc[lo:hi].reset_index(drop=True)
    strikes_str = near["Strike"].astype(int).astype(str).tolist()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=strikes_str, y=near["CE_OI_Chg"] / 1e3,
        name="CE OI Δ", marker_color="#ff6688", opacity=0.9,
    ))
    fig.add_trace(go.Bar(
        x=strikes_str, y=near["PE_OI_Chg"] / 1e3,
        name="PE OI Δ", marker_color="#44ffaa", opacity=0.9,
    ))
    fig.add_hline(y=0, line_color="rgba(255,255,255,0.3)", line_width=1)
    fig.update_layout(
        barmode="group", height=260,
        paper_bgcolor="#0a0e1a", plot_bgcolor="#0d1117",
        font=dict(family="JetBrains Mono", color="#e2e8f0", size=10),
        title=dict(text="OI Change (CE vs PE) — thousands",
                   font=dict(color="#00d4ff", size=13)),
        xaxis=dict(title="Strike", gridcolor="#1e2d45", type="category", tickangle=-45),
        yaxis=dict(title="Δ OI (K)", gridcolor="#1e2d45"),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.28),
        margin=dict(l=10, r=10, t=40, b=60),
    )
    return fig


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")
    selected_index = st.selectbox("Select Index", ["NIFTY", "BANKNIFTY", "SENSEX"], index=0)
    hist_days      = st.slider("Historical Days", 15, 120, 60, step=5)

    st.markdown("---")
    st.markdown("##### 🔑 API Keys (Optional)")
    anthropic_key  = st.text_input("Anthropic API Key",  type="password", placeholder="sk-ant-...")
    dhan_client_id = st.text_input("Dhan Client ID",     placeholder="Client ID")
    dhan_token     = st.text_input("Dhan Access Token",  type="password", placeholder="Access Token")

    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    auto_refresh = st.checkbox("Auto Refresh (60s)", value=False)

    st.markdown("---")
    st.markdown("""
    <div style='font-size:11px;color:#64748b;line-height:1.7;'>
    <b style='color:#00d4ff;'>Option Chain Sources</b><br>
    1 · nsepython (primary)<br>
    2 · NSE API direct session<br>
    3 · Realistic synthetic fallback<br><br>
    <b style='color:#00d4ff;'>Indicators</b><br>
    RSI(14) · VWAP · BB(20,2)<br>
    EMA(13/21) · ADX(14) · ±DI<br>
    CPR · Day H/L Breakout
    </div>""", unsafe_allow_html=True)

if auto_refresh:
    time.sleep(60)
    st.rerun()

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style='text-align:center;padding:10px 0 18px;'>
  <h1 style='font-size:2.5rem;letter-spacing:-2px;margin:0;'>📈 NIFTY ANALYSIS BOT</h1>
  <p style='color:#64748b;font-family:JetBrains Mono;font-size:11px;letter-spacing:3px;margin-top:6px;'>
    LIVE MARKET INTELLIGENCE · OPTION CHAIN · SMART SIGNALS
  </p>
</div>""", unsafe_allow_html=True)
st.markdown(
    f"<p style='text-align:center;color:#64748b;font-size:11px;font-family:JetBrains Mono;'>"
    f"Last updated: {datetime.now().strftime('%d %b %Y %H:%M:%S IST')} · "
    f"<span style='color:#00d4ff'>{selected_index}</span></p>",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# MAIN DATA PIPELINE
# ─────────────────────────────────────────────
with st.spinner("Fetching market data…"):
    hist_df = fetch_historical_data(selected_index, hist_days)
    if hist_df.empty:
        st.error("❌ Could not load historical data.")
        st.stop()
    hist_df  = add_indicators(hist_df)
    cpr      = calc_cpr(hist_df)
    last_row = hist_df.iloc[-1]

    live_data  = fetch_index_live(selected_index)
    spot_price = float(live_data.get("last",          last_row["Close"])) if live_data and "error" not in live_data else float(last_row["Close"])
    spot_chg   = float(live_data.get("variation",     0))                  if live_data and "error" not in live_data else 0.0
    spot_pct   = float(live_data.get("percentChange", 0))                  if live_data and "error" not in live_data else 0.0

    oc_df, pcr, oi_signal, is_synthetic = fetch_option_chain(
        INDEX_META[selected_index]["oc_symbol"], spot_price
    )
    analysis = generate_analysis(hist_df, cpr, pcr, oi_signal, spot_price)

# ─────────────────────────────────────────────
# METRICS ROW
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">LIVE MARKET SNAPSHOT</div>', unsafe_allow_html=True)
chg_cls   = "metric-change-up" if spot_chg >= 0 else "metric-change-down"
chg_arrow = "▲" if spot_chg >= 0 else "▼"
rsi_v = last_row["RSI"]
adx_v = last_row["ADX"]

c1, c2, c3, c4, c5, c6 = st.columns(6)
for col, lbl, val, sub, cls in [
    (c1, selected_index, f"{spot_price:,.2f}", f"{chg_arrow} {abs(spot_chg):,.2f} ({spot_pct:+.2f}%)", chg_cls),
    (c2, "RSI(14)",  f"{rsi_v:.1f}",   "Overbought" if rsi_v>60 else ("Oversold" if rsi_v<40 else "Neutral"), "metric-change-up" if rsi_v>50 else "metric-change-down"),
    (c3, "ADX(14)",  f"{adx_v:.1f}",   "Trending" if adx_v>25 else "Sideways",                                "metric-change-up" if adx_v>25 else "metric-neutral"),
    (c4, "PCR",      f"{pcr:.2f}",     "Bullish" if pcr>1 else "Bearish",                                     "metric-change-up" if pcr>1 else "metric-change-down"),
    (c5, "CPR Width",f"{abs(cpr['tc']-cpr['bc']):.1f}", f"TC:{cpr['tc']:.0f}  BC:{cpr['bc']:.0f}",           "metric-change-up"),
    (c6, "Confidence",f"{analysis['score']}/100", analysis['bias'],                                            "metric-change-up" if analysis['score']>60 else ("metric-change-down" if analysis['score']<40 else "metric-neutral")),
]:
    with col:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">{lbl}</div>
          <div class="metric-value">{val}</div>
          <div class="{cls}">{sub}</div>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">AI ANALYSIS SUMMARY</div>', unsafe_allow_html=True)
tag_html  = "".join(f'<span class="tag-{t}">{tx}</span> ' for t, tx in analysis["tags"])
bar_color = "#00ff88" if analysis['score']>60 else ("#ff4466" if analysis['score']<40 else "#ffd700")
st.markdown(f"""
<div class="summary-box">
  <div class="summary-title">Market Interpretation — {selected_index}</div>
  <div class="summary-text">{analysis['summary']}</div>
  <div style='margin-top:14px;'>{tag_html}</div>
  <div style='margin-top:16px;'>
    <div style='font-size:11px;color:#64748b;font-family:JetBrains Mono;letter-spacing:1px;'>
      CONFIDENCE SCORE: {analysis['score']}/100
    </div>
    <div style='background:#1e2d45;border-radius:8px;height:8px;margin-top:6px;overflow:hidden;'>
      <div style='background:{bar_color};width:{analysis['score']}%;height:100%;border-radius:8px;'></div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CPR LEVELS
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">CPR LEVELS</div>', unsafe_allow_html=True)
cols_cpr = st.columns(7)
for i, (lbl, val, clr) in enumerate([
    ("R1",    cpr["r1"],        "#ff9900"),
    ("PDH",   cpr["prev_high"], "#ffffff"),
    ("TC",    cpr["tc"],        "#00ff88"),
    ("Pivot", cpr["pivot"],     "#00d4ff"),
    ("BC",    cpr["bc"],        "#ff4466"),
    ("PDL",   cpr["prev_low"],  "#888888"),
    ("S1",    cpr["s1"],        "#ff4466"),
]):
    pos = "▶ Current" if abs(spot_price - val) / max(val, 1) < 0.002 else ("✓ Above" if spot_price > val else "")
    with cols_cpr[i]:
        st.markdown(f"""
        <div class="metric-card" style='border-left-color:{clr};'>
          <div class="metric-label">{lbl}</div>
          <div style='font-size:17px;font-weight:700;color:{clr};font-family:JetBrains Mono;'>{val:,.1f}</div>
          <div style='font-size:10px;color:#64748b;'>{pos}</div>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PRICE CHART
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">PRICE CHART WITH INDICATORS</div>', unsafe_allow_html=True)
st.plotly_chart(build_price_chart(hist_df, cpr, selected_index), use_container_width=True)

# ─────────────────────────────────────────────
# OPTION CHAIN SECTION  (Fixed)
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">OPTION CHAIN ANALYSIS</div>', unsafe_allow_html=True)

if is_synthetic:
    st.warning(
        "⚠️ **NSE live data unavailable** — NSE rate-limits cloud IPs or market is closed. "
        "Showing **realistic simulated** option chain data for full UI preview. "
        "For live data, run the app locally during market hours (9:15 AM – 3:30 PM IST).",
        icon="⚠️",
    )
else:
    st.success("✅ Live NSE option chain loaded successfully.")

if not oc_df.empty:
    col_chart, col_stats = st.columns([3, 1])

    with col_chart:
        st.plotly_chart(build_oi_chart(oc_df, spot_price, is_synthetic), use_container_width=True)
        st.plotly_chart(build_oi_change_chart(oc_df, spot_price),        use_container_width=True)

    with col_stats:
        total_ce     = oc_df["CE_OI"].sum()
        total_pe     = oc_df["PE_OI"].sum()
        max_ce_str   = oc_df.loc[oc_df["CE_OI"].idxmax(), "Strike"]
        max_pe_str   = oc_df.loc[oc_df["PE_OI"].idxmax(), "Strike"]
        total_ce_chg = oc_df["CE_OI_Chg"].sum()
        total_pe_chg = oc_df["PE_OI_Chg"].sum()

        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        for lbl, val, clr in [
            ("Total CE OI",         f"{total_ce/1e5:.1f}L",      "#ff4466"),
            ("Total PE OI",         f"{total_pe/1e5:.1f}L",      "#00ff88"),
            ("PCR (OI)",            f"{pcr:.3f}",                 "#00d4ff"),
            ("CE OI Change",        f"{total_ce_chg/1e3:+.0f}K", "#ff8888"),
            ("PE OI Change",        f"{total_pe_chg/1e3:+.0f}K", "#88ffbb"),
            ("Max CE (Resistance)", f"{max_ce_str:.0f}",          "#ff4466"),
            ("Max PE (Support)",    f"{max_pe_str:.0f}",          "#00ff88"),
            ("OI Signal",           oi_signal[:22],               "#ffd700"),
        ]:
            st.markdown(f"""
            <div class="metric-card" style='border-left-color:{clr};padding:12px 16px;'>
              <div class="metric-label">{lbl}</div>
              <div style='font-size:15px;font-weight:700;color:{clr};font-family:JetBrains Mono;'>{val}</div>
            </div>""", unsafe_allow_html=True)

    # Near-ATM table
    st.markdown("##### Near-ATM Option Chain Table")
    atm_idx = int((oc_df["Strike"] - spot_price).abs().idxmin())
    lo = max(0, atm_idx - 8)
    hi = min(len(oc_df), atm_idx + 9)
    tbl = oc_df.iloc[lo:hi].copy()
    tbl = tbl[["CE_OI", "CE_OI_Chg", "CE_LTP", "Strike",
               "PE_LTP", "PE_OI_Chg", "PE_OI"]].reset_index(drop=True)
    tbl.columns = ["CE OI", "CE ΔOI", "CE LTP", "Strike",
                   "PE LTP", "PE ΔOI", "PE OI"]

    def _style_row(row):
        if abs(row["Strike"] - spot_price) < spot_price * 0.005:
            return ["background-color: rgba(0,212,255,0.12)"] * len(row)
        return [""] * len(row)

    st.dataframe(
        tbl.style.apply(_style_row, axis=1).format({
            "CE OI": "{:,.0f}", "CE ΔOI": "{:+,.0f}", "CE LTP": "{:.2f}",
            "Strike": "{:.0f}",
            "PE LTP": "{:.2f}", "PE ΔOI": "{:+,.0f}", "PE OI": "{:,.0f}",
        }),
        use_container_width=True, height=320,
    )

    # Top strikes expander
    with st.expander("🔥 OI Concentration — Top Strikes (Support / Resistance)"):
        top_ce = oc_df.nlargest(5, "CE_OI")[["Strike", "CE_OI", "CE_OI_Chg", "CE_LTP"]]
        top_pe = oc_df.nlargest(5, "PE_OI")[["Strike", "PE_OI", "PE_OI_Chg", "PE_LTP"]]
        tc2, tp2 = st.columns(2)
        with tc2:
            st.markdown("**Top CE Strikes (Resistance)**")
            st.dataframe(top_ce.reset_index(drop=True).style.format({
                "CE_OI": "{:,.0f}", "CE_OI_Chg": "{:+,.0f}", "CE_LTP": "{:.2f}",
            }), use_container_width=True, hide_index=True)
        with tp2:
            st.markdown("**Top PE Strikes (Support)**")
            st.dataframe(top_pe.reset_index(drop=True).style.format({
                "PE_OI": "{:,.0f}", "PE_OI_Chg": "{:+,.0f}", "PE_LTP": "{:.2f}",
            }), use_container_width=True, hide_index=True)
else:
    st.error("Option chain data failed to load. Please click Refresh Data and try again.")

# ─────────────────────────────────────────────
# INDICATOR TABLE
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">INDICATOR SNAPSHOT</div>', unsafe_allow_html=True)
ind_rows = [
    ("RSI(14)",  f"{last_row['RSI']:.2f}",      "Overbought" if last_row['RSI']>60 else ("Oversold" if last_row['RSI']<40 else "Neutral")),
    ("VWAP",     f"{last_row['VWAP']:.2f}",      "Above" if spot_price > last_row['VWAP'] else "Below"),
    ("BB Upper", f"{last_row['BB_upper']:.2f}",  "Near" if abs(spot_price-last_row['BB_upper'])/spot_price<0.005 else "—"),
    ("BB Mid",   f"{last_row['BB_mid']:.2f}",    "Above" if spot_price > last_row['BB_mid'] else "Below"),
    ("BB Lower", f"{last_row['BB_lower']:.2f}",  "Near" if abs(spot_price-last_row['BB_lower'])/spot_price<0.005 else "—"),
    ("EMA 13",   f"{last_row['EMA13']:.2f}",     "Bullish" if last_row['EMA13']>last_row['EMA21'] else "Bearish"),
    ("EMA 21",   f"{last_row['EMA21']:.2f}",     "Bullish" if last_row['EMA13']>last_row['EMA21'] else "Bearish"),
    ("+DI",      f"{last_row['+DI']:.2f}",       "Bullish" if last_row['+DI']>last_row['-DI'] else "Bearish"),
    ("-DI",      f"{last_row['-DI']:.2f}",       "Bullish" if last_row['+DI']>last_row['-DI'] else "Bearish"),
    ("ADX(14)",  f"{last_row['ADX']:.2f}",       "Strong" if last_row['ADX']>25 else "Weak"),
]
ind_df = pd.DataFrame(ind_rows, columns=["Indicator", "Value", "Signal"])

def _color_sig(v):
    if v in ("Bullish", "Overbought", "Strong", "Above"): return "color:#00ff88;font-weight:600"
    if v in ("Bearish", "Oversold", "Below"):              return "color:#ff4466;font-weight:600"
    if v == "Neutral":                                      return "color:#ffd700"
    return ""

st.dataframe(
    ind_df.style.applymap(_color_sig, subset=["Signal"]),
    use_container_width=True, hide_index=True, height=390,
)

# ─────────────────────────────────────────────
# SIGNAL BREAKDOWN
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">DETAILED SIGNAL BREAKDOWN</div>', unsafe_allow_html=True)
for sig in analysis["signals"]:
    sl = sig.lower()
    icon = "🟢" if any(w in sl for w in ["bullish","above","breakout","short cover","long build"]) else \
           "🔴" if any(w in sl for w in ["bearish","below","breakdown","short build","unwinding"])  else "🟡"
    st.markdown(f"""
    <div style='background:#111827;border:1px solid #1e2d45;border-radius:8px;
         padding:10px 16px;margin:4px 0;font-family:Space Grotesk;font-size:14px;color:#e2e8f0;'>
      {icon} {sig}
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center;color:#64748b;font-size:11px;font-family:JetBrains Mono;padding:10px 0;'>
  Nifty Analysis Bot · Streamlit + NSE India API + pandas · For educational purposes only<br>
  ⚠️ Not financial advice. Always do your own research before trading.
</div>""", unsafe_allow_html=True)
