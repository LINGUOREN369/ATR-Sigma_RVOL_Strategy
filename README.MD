Got it — here’s your project README rewritten cleanly in Markdown (easy to copy-paste into README.md):

# ATR-Sigma RVOL Strategy

A modular Python framework to analyze and visualize stock data using **Average True Range (ATR)** and **Relative Volume (RVOL)** indicators.  
The project is organized into distinct components for configuration, data acquisition, processing, visualization, and image stitching.

---

## Project Structure

### `config.py` — Central Settings
Holds all knobs/paths used everywhere (single source of truth):

- `STOCK_TICKER` (e.g., `"VOO"`)
- `FIGURE_PATH` → folder where individual charts/PNGs are saved  
- `REPORT_PATH` → folder where stitched/composite images go  
- **Daily knobs**: `DAILY_DATE_RANGE`, `DAILY_ROLLING_WINDOW`, `ATR_DAILY_ROLLING_WINDOW`  
- **Intraday knobs**: `INTRADAY_ROLLING_WINDOW`, `SHOW_N_DAYS`  
- **Data paths**: e.g., `INTRADAY_FILEPATH` if you save derived CSVs for hourly bars  

---

### `download_data.py` — Get Raw Market Data
Responsible for fetching daily and intraday bars (from your vendor/API).

- Fetches daily & intraday data  
- Normalizes column names  
- Writes to:  
  - `./data/{TICKER}_daily.csv`  
  - `./data/{TICKER}_{interval}.csv`  

**Helpers:**
- `fetch_data_to_csv(ticker, interval="1d"|"60min"|"15min"|...)`  
- Optional CLI via `if __name__ == "__main__":`  

**Output:** CSV files in `./data/` for downstream processing.

---

### `daily_handler.py` — Daily Data Processing
Cleans raw daily data and builds features for plotting.

- `daily_data_handler(ticker, daterange)` → returns DataFrame with tz-aware index  
- `daily_data_feature(df, feature)` → extracts features (close, volume, etc.)  
- `daily_data_rvol(df, look_back_days)` → computes daily RVOL  
- `daily_data_atr(df, lookback)` → computes ATR (True Range rolling mean)  

**Output:** DataFrames for close, volume, RVOL, and ATR.

---

### `daily_viz.py` — Daily Charts
Generates daily PNG charts (saved to `FIGURE_PATH`) with standardized names.

- Daily close → `VOO_daily_close_30.png`, `VOO_daily_close_60.png`, `VOO_daily_close_90.png`  
- Daily volume → `VOO_daily_volume_30.png`, …  
- Daily RVOL → `VOO_daily_rvol_30.png`, …  
- Daily ATR → `VOO_daily_atr_30.png`, …  

**Output:** PNG charts for each daily feature.

---

### `intraday_handler.py` — Intraday Data Processing
Processes intraday (hourly/15min/30min) CSVs.

- Builds time-of-day pivots  
- Computes intraday RVOL curves vs. historical average  
- Computes time-of-day averages for close & volume (lookbacks: 5, 10, 20 days)  

**Output:** DataFrames for:
- Average close by time  
- Average volume by time  
- Last `SHOW_N_DAYS` intraday RVOL lines  

---

### `intraday_viz.py` — Intraday Charts
Creates intraday PNG charts (saved to `FIGURE_PATH`).

- Average close →  
  - `VOO_intraday_average_close_5_days_look_back.png`  
  - `VOO_intraday_average_close_10_days_look_back.png`  
  - `VOO_intraday_average_close_20_days_look_back.png`  

- Average volume →  
  - `VOO_intraday_average_volume_5_days_look_back.png` (also 10/20)  

- Intraday RVOL (last N days, varying lookback):  
  - `VOO_intraday_rvol_last_10_days_with_5_day_lookback.png`  
  - `VOO_intraday_rvol_last_10_days_with_10_day_lookback.png`  
  - `VOO_intraday_rvol_last_10_days_with_20_day_lookback.png`  

**Output:** Intraday PNG charts.

---

### `image_stack_patch.py` — Image Stitcher
Discovers related PNGs and stitches period variants vertically into composites.

**Recognized families:**
1. **Daily**  

{TICKER}daily{feature}_{period}.png
→ VOO_daily_close_30-60-90.png

2. **Intraday averages (close/volume)**  

{TICKER}intraday_average_close{period}_days_look_back.png
→ VOO_intraday_average_close_5-10-20.png

3. **Intraday RVOL**  

{TICKER}intraday_rvol_last{show}days_with{period}_day_lookback.png
→ VOO_intraday_rvol_last_10_days_with_lookback_5-10-20.png

**Output:** Stitched composites saved in `REPORT_PATH`.

---

## Usage

Run the full pipeline (example with `test.py`):

1. Download daily & intraday data to CSV  
2. Process daily data and generate daily charts  
3. Process intraday data and generate intraday charts  
4. Stitch charts into composites for review  

```bash
python download_data.py
python test.py

	•	Individual PNGs → FIGURE_PATH
	•	Stitched composites → REPORT_PATH

⸻

Dependencies

Requires Python 3.9+ and:

Core:
	•	pandas → data manipulation
	•	numpy → numerical computations
	•	matplotlib → plotting
	•	Pillow (PIL) → image stitching
	•	re (built-in) → regex for filename parsing
	•	pathlib (built-in) → filesystem paths
	•	subprocess (built-in, optional for batch running)

Optional:
	•	alpha_vantage or other market-data API client

Install via pip:

pip install pandas numpy matplotlib pillow alpha_vantage

Or use a requirements.txt:

pandas
numpy
matplotlib
pillow
alpha_vantage

---

Do you want me to also make a **shorter “Quick Start” version** (just install + run) for the top of the README, so new users don’t have to read the whole structure section first?
