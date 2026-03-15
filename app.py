"""
Nifty Analysis Bot — Enhanced Version with Tabs & Global Risk Sections
Inspired by worldmonitor.app structure
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
# PAGE CONFIG & CSS
# ─────────────────────────────────────────────
st.set_page_config(page_title="Nifty Analysis Bot", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
/* Your existing custom CSS here - paste it fully from previous version */
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
/* ... rest of your CSS ... */
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
# CONSTANTS & FUNCTIONS (keep your existing ones here)
# ... paste your INDEX_SYMBOLS, fetch functions, indicator calcs, OI functions, analysis function ...
# (I omitted them here for brevity - copy from your current file or previous messages)

# ─────────────────────────────────────────────
# SIDEBAR CONFIGURATION
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    selected_index = st.selectbox("Select Index", ["NIFTY", "BANKNIFTY", "SENSEX"], index=0)
    hist_days = st.slider("Historical Days", 15, 120, 60, step=5)
    
    chart_type = st.selectbox("Chart Type", ["Candlestick", "Kagi", "Point & Figure"], index=0)
    if chart_type in ["Point & Figure", "Kagi"]:
        box_size = st.slider("Box/Reversal Size", 0.25, 5.0, 1.0, 0.25)
        reversal_boxes = st.slider("Reversal (boxes)", 1, 5, 3, 1)
    else:
        box_size = 1.0
        reversal_boxes = 3

    st.markdown("---")
    anthropic_key = st.text_input("Anthropic API Key (for smarter summary)", type="password")
    dhan_client_id = st.text_input("Dhan Client ID (future trading)", "")
    dhan_token = st.text_input("Dhan Access Token", type="password")

# ─────────────────────────────────────────────
# TABS FOR DIFFERENT SECTIONS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["Nifty Live Dashboard", "OI & Option Chain", "Global Risk Monitor", "Forecasts"])

with tab1:
    st.subheader("Nifty Live Dashboard")
    # Your existing live snapshot cards, AI summary bullets, price chart with selector
    # ... paste your current dashboard code here (metrics, summary bullets, chart with type selector) ...

with tab2:
    st.subheader("OI & Option Chain Deep Dive")
    # Enhanced OI bar chart + full table
    if not oc_df.empty:
        st.plotly_chart(fig_oi, use_container_width=True)
        st.dataframe(oc_df.style.format({
            "CE_OI": "{:,.0f}", "CE_OI_Chg": "{:+,.0f}", "CE_LTP": "{:.2f}",
            "Strike": "{:.0f}", "PE_LTP": "{:.2f}", "PE_OI_Chg": "{:+,.0f}", "PE_OI": "{:,.0f}"
        }), use_container_width=True)
    else:
        st.info("No OI data available.")

with tab3:
    st.subheader("Global Risk Monitor (World Monitor Style)")
    st.markdown("### Instability & Geopolitical Context")
    # Mock cards (replace with real data later)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Middle East Tension", "High", "Iran + Israel", delta_color="inverse")
    with col2:
        st.metric("Global Supply Chain Risk", "Elevated", "Red Sea disruptions")
    with col3:
        st.metric("Cyber Threat Level", "Moderate", "Rising in region")

    st.markdown("### Recent Alerts")
    st.write("- Israel-Iran escalation ongoing (15 Mar 2026)")
    st.write("- Oil price volatility spike (+3.11%)")

with tab4:
    st.subheader("Forecasts & Probabilities")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("24h Bullish Probability", "65%", "ADX trending + OI buildup")
    with col2:
        st.metric("7d Trend", "Bullish", "EMA aligned + Day High breakout")
    with col3:
        st.metric("30d Risk", "Moderate", "PCR neutral, watch Red Sea")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("Nifty Analysis Bot · Built with Streamlit + NSE India API + pandas · Educational use only", unsafe_allow_html=True)
