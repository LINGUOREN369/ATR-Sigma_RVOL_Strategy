"""
This module contains configuration constants for the ATR-Sigma RVOL Strategy.
"""

from pathlib import Path

## Base paths
DATA_PATH = Path("/Users/linguoren/Documents/Market_Research/stock_data")
REPORT_BASE_PATH = Path("/Users/linguoren/Documents/Market_Research/stock_report")

## Download data
# Stock ticker list to fetch data into csv file in data folder
DOWNLOAD_STOCK_TICKER_LIST = [
                     "CRCL",
                     "VOO",
                     "RUM"]
                    #  "RUM",
                    #  "COIN"]

# Interval desired 
INTRADAY_INTERVAL = "60min"  # intraday interval

# Stock_Outputsize
# "compact" (last 100 points) or "full" (up to 30 days for intraday)
OUTPUTSIZE = "full"



## stock ticker to analyze
STOCK_TICKER = "RUM"


## Show plots when running test.py
SHOW_PLOTS = False

## Path of the folder to save figures
FIGURE_BASE_PATH = Path("./stock_image")
FIGURE_PATH = FIGURE_BASE_PATH / STOCK_TICKER
FIG_SIZE = (20,6)


## Report Path (compiled images, etc)
REPORT_PATH = REPORT_BASE_PATH / STOCK_TICKER

## Number of days of daily data to load
# •	30 days → very short-term view (good for testing, not for trend context).
# •	60–90 days → gives 2–3 months, enough to see recent trends.
# •	180+ days → better if you want context across rate cycles, IPO, or market phases.
# 60-90 is recommended for a balance of context and recency.
DAILY_DATE_RANGE = [30, 60, 120]


## Rolling window for daily features (ATR, RVOL, SMA, etc).
# 	•	14 → “classic” period (used in RSI, ATR, etc). Good for capturing 2–3 trading weeks.
# 	•	20 → roughly 1 month.
# 	•	30 → smoother, better for bigger swings.
# Swing trade 1-2 weeks: 14 is good to balance responsiveness and noise.
# Position trade 1 month+: 20 or 30 is better.
DAILY_ROLLING_WINDOW = 14


## Lookback for ATR calculation (in days)
# ATR is often calculated over 14 days, but for a shorter-term view, 5 days can be used.
# If you want fast signal: keep 5. For swing stability: set 10–14.
ATR_DAILY_ROLLING_WINDOW = 14



## intraday file path
INTRADAY_FILEPATH = DATA_PATH / f"{STOCK_TICKER}_{INTRADAY_INTERVAL}.csv"


## Window for intraday (hourly) features.
# 	•	5 → very tight, only one trading week.
# 	•	10 → 2 trading weeks.
# 	•	20 → ~1 month.
# 10 is a good balance to capture short-term intraday trends without too much noise.
INTRADAY_ROLLING_WINDOW = [10,20,30]


## SIGMA rolling window (in days) for RVOL Intraday Calculation
SIGMA_ROLLING_WINDOW = 20

## RVOL Figure show number of days
# How many recent days to show in the intraday RVOL plot.
# 	•	5 days → good for a quick look at the past week.
# 	•	10 days → gives more context over two weeks.
# 	•	20 days → shows a full month, useful for spotting patterns.
SHOW_N_DAYS = 5


def _refresh_runtime_paths() -> None:
    """Recompute derived paths after updates."""
    global FIGURE_PATH, REPORT_PATH, INTRADAY_FILEPATH
    FIGURE_PATH = FIGURE_BASE_PATH / STOCK_TICKER
    REPORT_PATH = REPORT_BASE_PATH / STOCK_TICKER
    INTRADAY_FILEPATH = DATA_PATH / f"{STOCK_TICKER}_{INTRADAY_INTERVAL}.csv"


def apply_runtime_overrides(
    *,
    stock_ticker: str | None = None,
    data_path: str | Path | None = None,
    report_base_path: str | Path | None = None,
    figure_base_path: str | Path | None = None,
) -> None:
    """Mutate config values for ad-hoc runs (e.g., CLI overrides)."""
    global STOCK_TICKER, DATA_PATH, REPORT_BASE_PATH, FIGURE_BASE_PATH

    if stock_ticker is not None:
        STOCK_TICKER = stock_ticker
    if data_path is not None:
        DATA_PATH = Path(data_path)
    if report_base_path is not None:
        REPORT_BASE_PATH = Path(report_base_path)
    if figure_base_path is not None:
        FIGURE_BASE_PATH = Path(figure_base_path)

    _refresh_runtime_paths()
