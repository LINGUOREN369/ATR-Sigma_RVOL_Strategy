import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import config


def daily_data_handler(stock_ticker: str, daterange: int) -> pd.DataFrame:
    """
    Processes raw daily data by renaming columns, localizing timezone, and setting the date as the index.
    """
    daily_raw_df = pd.read_csv(config.DATA_PATH / f"{stock_ticker}_daily.csv")
    df_daily = daily_raw_df.copy()
    df_daily.columns = ["date", "open", "high", "low", "close", "volume"]
    df_daily["date"] = pd.to_datetime(df_daily["date"]).dt.tz_localize("America/New_York")
    df_daily = df_daily.set_index("date")
    df_daily = df_daily.sort_index(ascending=True)

    return df_daily.tail(daterange).copy()


def daily_data_handler_full(stock_ticker: str) -> pd.DataFrame:
    """Load and normalize the full daily dataset for a ticker (no tail cut)."""
    daily_raw_df = pd.read_csv(config.DATA_PATH / f"{stock_ticker}_daily.csv")
    df_daily = daily_raw_df.copy()
    df_daily.columns = ["date", "open", "high", "low", "close", "volume"]
    df_daily["date"] = pd.to_datetime(df_daily["date"]).dt.tz_localize("America/New_York")
    df_daily = df_daily.set_index("date")
    df_daily = df_daily.sort_index(ascending=True)
    return df_daily.copy()



def daily_data_feature(df_daily: pd.DataFrame, feature: str) -> pd.DataFrame:
    """
    Computes and visualizes a specified feature from daily data with a given lookback period.

    Parameters:
    - df_daily (pd.DataFrame): DataFrame containing daily data with a DateTime index.
    - feature (str): The feature/column name to analyze.

    Returns:
    - pd.DataFrame: DataFrame containing the specified feature.
    """

    # Select relevant columns
    df_daily = df_daily.loc[:, [feature]].copy()

    # Extract feature as DataFrame
    df_feature = df_daily[[feature]]

    return df_feature.copy()



def daily_data_rvol(volume: pd.DataFrame, lookback: int, ema: bool) -> pd.DataFrame:
    """
    Compute RVOL from a dataframes of volume indexed by date.
    
    Parameters:
    - volume (pd.DataFrame): DataFrame containing volume data indexed by date.
    - lookback (int): Number of days to look back for computing the feature.

    Returns:
    - pd.DataFrame: DataFrame containing the RVOL feature.
    """
    if ema:
        volume["avgvol"] = volume["volume"].ewm(span=lookback, adjust=False).mean().shift(1)
    else:
        volume["avgvol"] = volume["volume"].rolling(window=lookback, min_periods=lookback).mean().shift(1)

    volume["rvol"] = volume["volume"] / volume["avgvol"]
    return volume[["rvol"]].copy()



def daily_data_atr(df: pd.DataFrame, lookback: int,
    method: str = "wilder",  # "sma" or "wilder"
) -> pd.Series:
    
    """
    Compute ATR (in price units) from OHLC data.

    Accepts either Alpha Vantage columns ("1. open", "2. high", ...)
    or standard columns ("Open","High","Low","Close"). Index should be
    datetime or a 'date' column must be present.
    """

    def pick(colnames):
        for name in colnames:
            if name in df.columns:
                return df[name]
        raise KeyError(f"None of {colnames} found in df.columns={list(df.columns)}")

    # Index handling
    if "date" in df.columns:
        idx = pd.to_datetime(df["date"])
    else:
        idx = pd.to_datetime(df.index)

    # Robust column selection
    high   = pick(["High", "high", "2. high"])
    low    = pick(["Low", "low", "3. low"])
    close  = pick(["Close", "close", "4. close"])

    # Ensure numeric
    high  = pd.to_numeric(high, errors="coerce")
    low   = pd.to_numeric(low, errors="coerce")
    close = pd.to_numeric(close, errors="coerce")

    # True Range
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    tr.index = idx

    # ATR
    method = method.lower()
    if method == "wilder":
        atr = tr.ewm(alpha=1 / lookback, adjust=False).mean()
    elif method == "sma":
        atr = tr.rolling(window=lookback, min_periods=lookback).mean()
    else:
        raise ValueError("method must be 'sma' or 'wilder'")

    atr.name = f"ATR_{method}_{lookback}"

    return atr.copy()
