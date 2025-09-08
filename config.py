"""
This module contains configuration constants for the ATR-Sigma RVOL Strategy.
"""

## stock ticker to analyze
STOCK_TICKER = "PYPL"


## Show plots when running test.py
SHOW_PLOTS = False

## Path of the folder to save figures
FIGURE_PATH = f"./stock_image/{STOCK_TICKER}/"
FIG_SIZE = (16,4)

## Number of days of daily data to load
# •	30 days → very short-term view (good for testing, not for trend context).
# •	60–90 days → gives 2–3 months, enough to see recent trends.
# •	180+ days → better if you want context across rate cycles, IPO, or market phases.
# 60-90 is recommended for a balance of context and recency.
DAILY_DATE_RANGE = [30, 60, 90]


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
ATR_DAILY_ROLLING_WINDOW = 10



## intraday file path
INTRADAY_FILEPATH = f"./data/{STOCK_TICKER}_60min.csv"


## Window for intraday (hourly) features.
# 	•	5 → very tight, only one trading week.
# 	•	10 → 2 trading weeks.
# 	•	20 → ~1 month.
# 10 is a good balance to capture short-term intraday trends without too much noise.
INTRADAY_ROLLING_WINDOW = [5,10,20]


## RVOL Figure show number of days
# How many recent days to show in the intraday RVOL plot.
# 	•	5 days → good for a quick look at the past week.
# 	•	10 days → gives more context over two weeks.
# 	•	20 days → shows a full month, useful for spotting patterns.
SHOW_N_DAYS = 10



