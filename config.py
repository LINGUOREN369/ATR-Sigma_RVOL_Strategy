"""
This module contains configuration constants for the ATR-Sigma RVOL Strategy.
"""



## Path of the folder to save figures
FIGURE_PATH = "./stock_image/"

## stock ticker to analyze
stock_ticker = "CRCL"


## intraday file path
INTRADAY_FILEPATH = f"./data/{stock_ticker}_60min.csv"

## Number of days of daily data to load
# •	30 days → very short-term view (good for testing, not for trend context).
# •	60–90 days → gives 2–3 months, enough to see recent trends.
# •	180+ days → better if you want context across rate cycles, IPO, or market phases.
# 60-90 is recommended for a balance of context and recency.
daily_date_range = 60


## Rolling window for daily features (ATR, RVOL, SMA, etc).
# 	•	14 → “classic” period (used in RSI, ATR, etc). Good for capturing 2–3 trading weeks.
# 	•	20 → roughly 1 month.
# 	•	30 → smoother, better for bigger swings.
# Swing trade 1-2 weeks: 14 is good to balance responsiveness and noise.
# Position trade 1 month+: 20 or 30 is better.
look_back_days_daily = 14


## Window for intraday (hourly) features.
# 	•	5 → very tight, only one trading week.
# 	•	10 → 2 trading weeks.
# 	•	20 → ~1 month.
# 10 is a good balance to capture short-term intraday trends without too much noise.
look_back_days_hourly = 10


## Lookback for ATR calculation (in days)
# ATR is often calculated over 14 days, but for a shorter-term view, 5 days can be used.
# If you want fast signal: keep 5. For swing stability: set 10–14.
atr_look_back_days = 10