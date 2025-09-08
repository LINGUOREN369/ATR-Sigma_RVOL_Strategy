
# ATR-Sigma_RVOL_Strategy
A modular Python framework to analyze and visualize stock data using Average True Range (ATR) and Relative Volume (RVOL) indicators. The project is structured into distinct components for configuration, data acquisition, processing, visualization, and image stitching.

## Project Structure
The project is organized into the following key modules:

1) config.py — central settings

Holds all knobs/paths used everywhere, e.g.
	•	STOCK_TICKER (e.g., "VOO")
	•	FIGURE_PATH (folder where individual charts/PNGs are saved)
	•	REPORT_PATH (folder where stitched/composite images go)
	•	Daily knobs: DAILY_DATE_RANGE, DAILY_ROLLING_WINDOW, ATR_DAILY_ROLLING_WINDOW
	•	Intraday knobs: INTRADAY_ROLLING_WINDOW, SHOW_N_DAYS
	•	Data paths like INTRADAY_FILEPATH if you save a derived CSV for hourly bars

Think of this as the single source of truth; all other scripts read from it.

⸻

2) download_data.py — get raw market data to CSV

Typical responsibilities:
	•	Fetch daily and intraday bars (from your data vendor/API)
	•	Normalize column names and write to ./data/{TICKER}_{interval}.csv
	•	Provide helpers like:
	•	fetch_data_to_csv(ticker, interval="1d"|"60min"|"15min"|...)
	•	Maybe small CLI in if __name__ == "__main__": to download for STOCK_TICKER

Output: CSV files under ./data/ for downstream processing.

⸻

3) daily_handler.py — clean & feature engineering for daily

Reads your daily CSV and returns tidy DataFrames ready for plotting:
	•	daily_data_handler(ticker, daterange) → DataFrame with tz-aware index
	•	daily_data_feature(df_daily, feature) → picks/renames feature columns (close/volume)
	•	daily_data_rvol(df_feature, look_back_days) → computes daily RVOL
	•	daily_data_atr(df_daily, lookback) → computes ATR (TR rolling mean)

Output: in-memory DataFrames for close/volume/RVOL/ATR that daily_viz.py will plot.

⸻

4) daily_viz.py — make daily charts

Consumes outputs from daily_handler.py and writes PNGs to FIGURE_PATH using standardized file names so the stitcher can discover them later.

You typically create:
	•	Daily close panels (e.g., 30/60/90 days):
	•	VOO_daily_close_30.png, VOO_daily_close_60.png, VOO_daily_close_90.png
	•	Daily volume panels: VOO_daily_volume_30.png, …
	•	Daily RVOL panels (lookback shown in title, file keyed by range): VOO_daily_rvol_30.png, …
	•	Daily ATR panels: VOO_daily_atr_30.png, …

Output: individual PNGs in FIGURE_PATH.

⸻

5) intraday_handler.py — clean & feature engineering for intraday

Works on your hourly (or 15/30min) CSV:
	•	Builds time-of-day pivots
	•	Computes intraday RVOL curves (per time slot vs historical average)
	•	Computes average by time of day for close and volume over rolling windows (5/10/20 days)

Output: tidy DataFrames for:
	•	average close by time (5/10/20-day look-back)
	•	average volume by time (5/10/20-day look-back)
	•	last SHOW_N_DAYS intraday RVOL lines (one line per day across hours)

⸻

6) intraday_viz.py — make intraday charts

Writes PNGs with specific patterns so the stitcher can group them:
	•	Average close:
	•	VOO_intraday_average_close_5_days_look_back.png
	•	VOO_intraday_average_close_10_days_look_back.png
	•	VOO_intraday_average_close_20_days_look_back.png
	•	Average volume:
	•	VOO_intraday_average_volume_5_days_look_back.png (and 10/20)
	•	Intraday RVOL (last N trading days, vary the lookback window used to compute expected volume):
	•	VOO_intraday_rvol_last_10_days_with_5_day_lookback.png
	•	VOO_intraday_rvol_last_10_days_with_10_day_lookback.png
	•	VOO_intraday_rvol_last_10_days_with_20_day_lookback.png

Output: individual PNGs in FIGURE_PATH.

⸻

7) image_stack_patch.py — stitch related PNGs into composites

Discovers images by filename pattern and stacks period variants vertically into a single composite for quick review.

It recognizes three families:
	1.	Daily:
^{TICKER}_(daily_[a-z0-9_]+)_(\d+)\.png$
	•	e.g., base = daily_close, periods = 30, 60, 90 → output
VOO_daily_close_30-60-90.png
	2.	Intraday averages (close/volume):
^{TICKER}_(intraday_average_(close|volume))_(\d+)_days_look_back\.png$
	•	e.g., base = intraday_average_close, periods = 5,10,20 →
VOO_intraday_average_close_5-10-20.png
	3.	Intraday RVOL (last N days, vary lookback):
^{TICKER}_intraday_rvol_last_(show)_days_with_(period)_day_lookback\.png
	•	grouped as base = intraday_rvol_last_{show}_days_with_lookback
	•	periods = 5,10,20 →
VOO_intraday_rvol_last_10_days_with_lookback_5-10-20.png

Saves composites to REPORT_PATH.

## Usage
Run test.py to execute the full pipeline:
    1.	Download daily and intraday data to CSV
    2.	Process daily data, generate daily charts
    3.	Process intraday data, generate intraday charts
    4.	Stitch related charts into composites for review

Example:
```bash
python test.py
```
This will create individual PNGs in FIGURE_PATH and stitched composites in REPORT_PATH.

## Dependencies
This project requires Python 3.9+ and the following libraries:
	•	Core libraries
	•	pandas → data manipulation
	•	numpy → numerical computations
	•	matplotlib → plotting daily & intraday charts
	•	Pillow (PIL) → image stacking (for image_stack_patch.py)
	•	re (built-in) → regex for filename parsing
	•	pathlib (built-in) → filesystem paths
	•	subprocess (built-in, optional) → if you use run_all.py
	•	Optional (if downloading market data automatically)
	•	alpha_vantage or other API client (depending on your source)