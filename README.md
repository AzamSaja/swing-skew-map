# Swing Options Skew Map

A production-grade **Options Skew Map** system built strictly according to the methodology, mathematical formulas, and trap protections in [Bert Trading's Guide: *Build Your Own Skew Map — How to See What Options Traders Are Actually Paying For*](https://yellow-cardinal-454.notion.site/Build-Your-Own-Skew-Map-How-to-See-What-Options-Traders-Are-Actually-Paying-For-and-the-Weekend-V-3c0a77cc65b681678b2cd9b3499eaa61#3fb0e7b0b1634c23993118f2ef37c1a7).


> 🚀 **Live Production Deployment**: [https://swing-skew-map.vercel.app](https://swing-skew-map.vercel.app)  
> 📦 **GitHub Repository**: [https://github.com/AzamSaja/swing-skew-map](https://github.com/AzamSaja/swing-skew-map)

---

## What Skew Is

Price tells you what a stock did. The options chain tells you what traders are paying to be protected from what it does next. That difference across strikes is **skew**:

$$\text{Normalized Skew} = \frac{\sigma_{\text{put, 25}\Delta} - \sigma_{\text{call, 25}\Delta}}{\sigma_{\text{ATM}}}$$

$$\text{Vol Points (Un-normalized)} = (\sigma_{\text{put, 25}\Delta} - \sigma_{\text{call, 25}\Delta}) \times 100$$

* **Positive Skew**: Puts cost more $\rightarrow$ Downside protection is bid (Hedging / Fear).
* **Negative Skew**: Calls cost more $\rightarrow$ Upside is bid (Traders paying up to be long).
* **Divided by ATM IV**: Normalizes across volatility regimes for ranking names **inside** a sector.
* **Vol Points**: Survives cross-sector comparison without low-volatility sector distortion (**Trap #2**).

---

## The 4 Quadrants (Part 2)

Plotting Skew against 1-Month Return produces 4 distinct positioning buckets:

| Quadrant | Positioning | What it's telling you | Action |
| :--- | :--- | :--- | :--- |
| 🔵 **CONTRARIAN BID** | Stock **DOWN**, Calls Bid | Price falling while somebody pays up for upside. Tape and options disagree. | **Watchlist** (Highest interest, fresh look) |
| 🟠 **CHASE** | Stock **UP**, Calls Bid | Everyone agrees. Price up and people paying for more up. | **Crowded** (Late, avoid chasing) |
| 🟡 **HEDGED RALLY** | Stock **UP**, Puts Bid | Price rising and people paying for crash insurance underneath. Rally not trusted. | **Tighten Stops** on existing holdings |
| 🔴 **FEAR** | Stock **DOWN**, Puts Bid | Falling, and downside protection getting more expensive. Everyone agrees bearishly. | **Leave Alone** (Not a bargain yet) |

---

## The 5 Traps Protected

1. **Trap #1 (No Tail-Distorted Index Put/Call)**: Calculates delta-sane equidistant 25-delta strikes; excludes deep tail (<0.10 delta) crash lottery tickets.
2. **Trap #2 (No Normalized Skew for Sector Comparisons)**: Uses raw **Vol Points** for sector-level bars and benchmark comparisons (SPY, QQQ, IWM) to prevent low-volatility sectors (Utilities, Staples) from artificially dominating fear rankings.
3. **Trap #3 (Sector Agreement Check)**: Calculates constituent consensus. If internal agreement is below 60%, flags a **Breadth Caveat** warning.
4. **Trap #4 (Sanity Ceiling & Chain Quality)**: Enforces hard ceilings ($|\text{Skew}| \le 1.25$, $|\text{Vol Pts}| \le 45$) to eliminate quote artifacts (such as single-leg bad marks), and filters thin chains.
5. **Trap #5 (Dated Catalyst / Earnings Flag)**: Detects earnings dates falling inside the target expiry window and explicitly flags elevated IV as **Event Premium** rather than structural positioning.

---

## Quickstart

### 1. Run a Live Scan via CLI
```bash
# Scan US universe (50 liquid stocks across all 11 sectors + benchmarks)
python cli.py scan --market us

# Scan IDX universe (30 liquid Indonesian blue chips + IHSG benchmark)
python cli.py scan --market idx

# Scan custom tickers
python cli.py scan --tickers BBCA.JK,BBRI.JK,BMRI.JK,TLKM.JK --market idx

# View daily terminal briefing
python cli.py report --market us
python cli.py report --market idx

# Export latest scan to CSV
python cli.py export-csv us_skew_map.csv --market us
python cli.py export-csv idx_skew_map.csv --market idx
```

### 2. Launch the Interactive Web Dashboard
```bash
python cli.py serve --port 8000
```
Open **`http://localhost:8000`** in your browser to access:

* 🌐 **Market Switcher (Top Bar)**:
  * 🇺🇸 **US Equities (NYSE/NASDAQ)**: 25-Delta options chain implied volatility skew.
  * 🇮🇩 **Indonesia (IDX / BEI)**: Mathematical realized downside vs. upside semi-variance volatility skew benchmarked against **IHSG (`^JKSE`)**.
* 📊 **Tab 1: Skew Map Desk**:
  * **KPI Ribbon**: Active coverage, vol median, most-hedged sector, benchmarks (SPY/QQQ/IWM or IHSG), caution counter.
  * **Today's Written Read**: Standardized prose summary with caution flags and contrarian bids.
  * **The Name Radar (4 Quadrants)**: Interactive scatter plot with 1M / 1W / 1D timeframes, vs SPY/IHSG toggle, sector filter chips, and hover tooltips generating the exact Part 5 sentence.
  * **Sector Skew Bars**: Horizontal vol points chart with benchmark reference lines and agreement % badges.
  * **The Action Board**: Ranked shortlists organized into the 4 buckets.
  * **Database Explorer**: Full 14-column sortable table with search, filters, modal detail view, and CSV export.
* 🧮 **Tab 2: Function Sandbox & Greeks Calculator**:
  * Interactive live Black-Scholes solver ($N(d_1)$ call and put deltas).
  * Live normalized Skew & raw Vol Points calculator.
  * Trap #4 sanity ceiling status detector (Pass vs Exceeded).
  * Instant generation of the Part 5 standardized readout sentence as parameters are tuned.
  * One-click presets: *Contrarian Bid*, *Caution Flag*, *Chase*, *Trap #4 Outlier*, *BBCA.JK*.
* 🧠 **Tab 3: System Architecture & 7 Decisions**:
  * Visual flowchart and technical breakdown of the 7 Decisions pipeline.
  * Interactive breakdown of the 5 Traps and the math behind each guardrail.
* ⚙️ **Tab 4: Threshold Tuner & Settings**:
  * Live interactive sliders for Target Delta, Sector Agreement % threshold, Max Sanity Ceiling, and DTE range.
  * Persist and update configuration at runtime.

---

## Test Suite

Run the full unit and integration test suite:
```bash
python -m unittest discover -s tests -p "test_*.py"
```
Ran 19 tests in 0.084s: OK


