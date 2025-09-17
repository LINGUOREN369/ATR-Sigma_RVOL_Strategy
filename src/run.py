import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from pathlib import Path
import config

from src.daily_handler import (
    daily_data_handler, 
    daily_data_feature, 
    daily_data_rvol, 
    daily_data_atr)

from src.daily_viz import (
    daily_data_feature_viz, 
    daily_data_atr_viz, 
    daily_data_rvol_viz)

from src.intraday_handler import (
	intraday_read_csv_correct_time,
	intraday_feature_trend,
	intraday_expected_cum_rvol,
	intraday_rvol
)

from src.intraday_viz import (
	intraday_feature_trend_viz,
	intraday_rvol_viz,
)

from src.cli import configure_from_cli

def _clean_pngs(directory: Path) -> None:
    if directory.exists() and directory.is_dir():
        for file in directory.glob("*.png"):
            file.unlink()


def run_pipeline() -> None:
    stock_ticker = config.STOCK_TICKER

    daily_rolling_window = config.DAILY_ROLLING_WINDOW
    atr_daily_rolling_window = config.ATR_DAILY_ROLLING_WINDOW
    daily_range = config.DAILY_DATE_RANGE

    figure_path = Path(config.FIGURE_PATH)
    report_path = Path(config.REPORT_PATH)

    _clean_pngs(figure_path)
    _clean_pngs(report_path)

    for daily_date_range in daily_range:
        df_daily = daily_data_handler(stock_ticker, daily_date_range)
        volume_df = daily_data_feature(df_daily, "volume")
        close_df = daily_data_feature(df_daily, "close")
        daily_rvol_df = daily_data_rvol(volume_df, daily_rolling_window, ema=True)
        atr_df = daily_data_atr(df_daily, atr_daily_rolling_window, method="wilder")

        daily_data_feature_viz(close_df, "close")
        daily_data_feature_viz(volume_df, "volume")
        daily_data_atr_viz(atr_df, atr_daily_rolling_window)
        daily_data_rvol_viz(daily_rvol_df, daily_rolling_window)

    intraday_rolling_windows = config.INTRADAY_ROLLING_WINDOW
    intraday_filepath = config.INTRADAY_FILEPATH
    n_days = config.SHOW_N_DAYS

    for window in intraday_rolling_windows:
        df_rth = intraday_read_csv_correct_time(intraday_filepath)
        intraday_volume_df = intraday_feature_trend(df_rth, "volume", window, ema=True)
        intraday_close_df = intraday_feature_trend(df_rth, "close", window, ema=True)
        intraday_expected_cum_rvol_df = intraday_expected_cum_rvol(df_rth, window, ema=True)
        intraday_rvol_df = intraday_rvol(df_rth, intraday_expected_cum_rvol_df, window)

        intraday_feature_trend_viz(intraday_volume_df)
        intraday_feature_trend_viz(intraday_close_df)
        intraday_rvol_viz(intraday_rvol_df, window, show_n_days=n_days)

    import importlib

    image_stack_patch = importlib.import_module("src.image_stack_patch")
    importlib.reload(image_stack_patch)
    image_stack_patch.patch_images()


def main(argv=None) -> None:
    configure_from_cli(argv)
    run_pipeline()


if __name__ == "__main__":
    main()
