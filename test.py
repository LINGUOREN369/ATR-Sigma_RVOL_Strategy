import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from pathlib import Path
import config
import runpy

from daily_handler import (
    daily_data_handler, 
    daily_data_feature, 
    daily_data_rvol, 
    daily_data_atr)

from daily_viz import (
    daily_data_feature_viz, 
    daily_data_atr_viz, 
    daily_data_rvol_viz)

from intraday_handler import (
	intraday_read_csv_correct_time,
	intraday_feature_trend,
	intraday_expected_cum_rvol,
	intraday_rvol
)

from intraday_viz import (
	intraday_feature_trend_viz,
	intraday_rvol_viz,
)

from image_stack_patch import patch_images

## Load and process daily data
# Both daily and intraday
stock_ticker = config.STOCK_TICKER

# Load and process daily data
# Iterate through different daily date ranges to cover various contexts
daily_rolling_window = config.DAILY_ROLLING_WINDOW
atr_daily_rolling_window = config.ATR_DAILY_ROLLING_WINDOW
daily_range = config.DAILY_DATE_RANGE

for daily_date_range in daily_range:
    # Load daily data and compute features
    df_daily = daily_data_handler(stock_ticker, daily_date_range)
    volume_df = daily_data_feature(df_daily, "volume")
    close_df = daily_data_feature(df_daily, "close")
    daily_rvol_df = daily_data_rvol(volume_df, daily_rolling_window)
    atr_df = daily_data_atr(df_daily, atr_daily_rolling_window)

    # Visualize daily data
    daily_data_feature_viz(close_df, "close")
    daily_data_feature_viz(volume_df, "volume")
    daily_data_atr_viz(atr_df, atr_daily_rolling_window)
    daily_data_rvol_viz(daily_rvol_df, daily_rolling_window)


## Load and process intraday data
intraday_rolling_windows = config.INTRADAY_ROLLING_WINDOW
intraday_filepath = config.INTRADAY_FILEPATH
n_days = config.SHOW_N_DAYS

# Read and correct intraday data
for window in intraday_rolling_windows:
    # Load intraday data and compute features
    df_rth = intraday_read_csv_correct_time(intraday_filepath)
    intraday_volume_df = intraday_feature_trend(df_rth, "volume", window)
    intraday_close_df = intraday_feature_trend(df_rth, "close",window)
    intraday_expected_cum_rvol_df = intraday_expected_cum_rvol(df_rth, window)
    intraday_rvol_df = intraday_rvol(df_rth, intraday_expected_cum_rvol_df, window)
    
    # Visualize intraday data
    intraday_feature_trend_viz(intraday_volume_df)
    intraday_feature_trend_viz(intraday_close_df)
    intraday_rvol_viz(intraday_rvol_df, window, show_n_days=n_days)


# Patch images
patch_images()