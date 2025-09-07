import numpy as np
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
import config
from pathlib import Path


# Functions here handle reading, parsing, and standardizing input data.

def intraday_read_csv_correct_time(file_path, assume="ET"):
    """
    Pass a csv file from apache data api and turn that into a dataframe that has
    accurate timezone (NYC) with close and volume columns.
    """
    df = pd.read_csv(file_path)

    # Parse the column into datetimes
    ts = pd.to_datetime(df["date"], errors="raise")

    # Build a tz-aware DatetimeIndex in America/New_York
    if hasattr(ts, "dt") and ts.dt.tz is not None:
        # Already tz-aware → just convert to NY
        idx = ts.dt.tz_convert("America/New_York")
        idx = idx.tz_localize(None) 
    else:
        # Naive timestamps → decide what they mean
        if assume.upper() == "UTC":
            idx = pd.DatetimeIndex(ts, tz="UTC").tz_convert("America/New_York")
            idx = idx.tz_localize(None)   # strips it off
        else:  # assume they are already Eastern local time
            idx = pd.DatetimeIndex(ts, tz="America/New_York")
            idx = idx.tz_localize(None)   # strips it off

    # Use the tz-aware index
    df = df.set_index(idx)
    # Optional: drop the original column
    df = df.drop(df.columns[0], axis=1)

    # Filter to Regular Trading Hours
    df_rth = df.between_time("09:30", "16:00")
    df_rth = df_rth[["4. close", "5. volume"]]  # keep only close and volume
    df_rth.columns = ["close", "volume"]

    return df_rth



def intraday_feature_trend(df, feature, look_back_days):
    """
    Visualize the trend of a specific feature by time of day over a look-back period.
    Returns the *sorted* average-by-time series used in the plot.
    """
    # Build pivot: rows = date, cols = time-of-day
    date_column = df.index.date
    time_column = df.index.time
    df_pivot = df.pivot_table(index=date_column, columns=time_column, values=feature)

    # Average over last N days
    tail_block = df_pivot.tail(look_back_days)
    avg_feature_by_time = tail_block.mean(axis=0)
    avg_feature_by_time.name = f"Average {feature.capitalize()}"

    # Robust sort by time-of-day
    times = pd.Index(avg_feature_by_time.index)
    seconds = np.array([t.hour * 3600 + t.minute * 60 + getattr(t, "second", 0) for t in times])
    order = np.argsort(seconds)

    # Sorted x/y for plotting
    # tick_labels = times.astype(str).to_numpy()[order]
    avg_sorted = avg_feature_by_time.iloc[order]
    
    return avg_sorted


def intraday_expected_cum_rvol(df_time_volume, look_back_days):
    cum_vol_df = df_time_volume.copy().sort_index()
    cum_vol_df["Date"] = cum_vol_df.index.date
    cum_vol_df["Time"] = cum_vol_df.index.time
    cum_vol_df["Cumulative_Volume"] = cum_vol_df.groupby("Date")["volume"].cumsum()
    pivot_cum = cum_vol_df.pivot_table(index="Date", columns="Time", values="Cumulative_Volume")
    # Not include the volume from the current day
    exp_curve = pivot_cum.rolling(window=look_back_days).mean().shift(1)
    exp_curve_long = exp_curve.stack().reset_index(name="Expected_Cumulative_Volume")
    exp_curve_long["Datetime"] = pd.to_datetime(exp_curve_long["Date"].astype(str) + " " + exp_curve_long["Time"].astype(str))
    exp_curve_long = exp_curve_long.drop(columns=["Date", "Time"])
    exp_curve_long = exp_curve_long.set_index("Datetime").sort_index()
    return exp_curve_long


def intraday_rvol(min_df: pd.DataFrame, exp_cum_df: pd.DataFrame, look_back_days) -> pd.DataFrame:
    """
    Computes Intraday_RVOL_cum = CumVolume / Exp_CumVolume.
    """
    df = min_df[["close", "volume"]].copy().sort_index()
    df["CumVolume"] = df.groupby(df.index.date)["volume"].cumsum()
    joined = df.join(exp_cum_df, how="left")
    joined["Intraday_RVOL_cum"] = joined["CumVolume"] / joined["Expected_Cumulative_Volume"]
    return joined
