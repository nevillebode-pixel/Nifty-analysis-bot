You are an expert Streamlit developer specializing in financial/trading dashboards for the Indian stock market.

I have a working Nifty Analysis Bot on Streamlit. It fetches live NSE data, calculates indicators (RSI, EMA13/21, ADX, CPR, Camarilla, Fibonacci), shows OI buildup signals (Long Build Up, Short Build Up, Short Covering, Long Unwinding), confidence score, bullet-point market interpretation with colored icons, dynamic chart types (Candlestick, Kagi, Point & Figure), sector volume buildup tab, and a global risk monitor tab.

The code already has:
- Dark modern theme with custom CSS (JetBrains Mono + Space Grotesk fonts, accent colors, metric cards, summary box, etc.)
- Big centered title at the top: "📈 NIFTY ANALYSIS BOT" with subtitle
- Sidebar with index selection (NIFTY, BANKNIFTY, SENSEX), historical days slider, chart type selector + size/reversal sliders, optional API keys (Anthropic, Dhan), refresh & auto-refresh checkbox
- Live snapshot metrics row (price, RSI, ADX, PCR, CPR width, confidence)
- OI Interpretation card with 🟢/🔴 icon + signal text
- Open Interest Representation section with bar chart (CE vs PE OI change near ATM) + current signal summary
- Market Interpretation as colored bullet list (🟢/🔴/🟡 icons)
- Dynamic price chart with selected type + overlays (EMA, CPR, Cam/Fib lines, ADX, volume)
- Weekend/holiday fallback for OI data
- Sector Volume Buildup tab with approximate data
- Global Risk Monitor tab with static/mock cards and alerts
- Footer disclaimer

The current OI chart in the "NIFTY OI & Option Chain" tab is not rendering properly or looks empty (especially for ATM strikes).

Your task:
Rewrite the ENTIRE app.py file so that:
1. It includes ALL SIX tabs exactly in this order and with these exact titles (including emojis):
   - 📈 NIFTY Live Dashboard   (make this tab title dynamic: e.g. 📈 BANKNIFTY Live Dashboard when BANKNIFTY is selected)
   - 📊 NIFTY OI & Option Chain
   - 🌍 Global Risk Monitor
   - 🔮 NIFTY Forecasts
   - 🏭 Sector Volume Buildup
   - 🎯 MA Crossover Scanner

2. Improve the "📊 NIFTY OI & Option Chain" tab to look more like Sensibull:
   - Horizontal or vertical bars showing CE OI Change (red) and PE OI Change (green) for strikes near spot (±200–300 points)
   - Vertical dashed line at current spot price
   - Clear labels, legend, title
   - Handle empty/fallback data gracefully with message
   - Keep the current OI signal card below the chart

3. For the "🌍 Global Risk Monitor" tab, add LIVE DATA where possible:
   - Fetch live Brent crude oil price (BZ=F via yfinance or free API)
   - Show current oil price and % change with color (red if rising sharply)
   - Add a simple "Oil Impact Alert" card: if oil > $90, show warning for Nifty energy sector
   - Keep the existing mock cards/alerts but make them dynamic where feasible (e.g., pull real news headlines via RSS if possible)

4. For the new "🎯 MA Crossover Scanner" tab:
   - Simple table or cards showing recent EMA13/21 crossovers (bullish/bearish) on the selected index
   - Or scan for other popular MAs (e.g., 50/200 SMA golden/death cross)
   - Use historical data from the selected index

5. Keep ALL existing functionality: live metrics, OI fallback, bullet interpretation, price chart with type selector, sector tab, sidebar, CSS, title, footer, etc.
6. Fix any potential NameError, scoping, or undefined variable issues (ensure functions are defined before use, variables in scope)
7. Ensure the code is complete, self-contained, runs without errors, and is production-ready style
8. Add yfinance to imports if needed for live oil price or sector data (assume it's in requirements.txt)

Output the FULL updated app.py code in one single markdown code block.
Do NOT remove or simplify any existing feature. Only enhance the OI chart, add live oil data to Global Risk Monitor, and implement the MA scanner tab.
