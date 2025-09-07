import pandas as pd
from alpha_vantage.timeseries import TimeSeries
from pathlib import Path
import argparse
import os

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

def fetch_alpha(symbol: str, interval: str = "1min", outputsize: str = "full") -> pd.DataFrame:
    """
    Fetch intraday OHLCV data from Alpha Vantage.

    Parameters
    ----------
    symbol : str
        Stock ticker (e.g., "AAPL")
    interval : str
        Interval string: "1min", "5min", "15min", "30min", "60min"
    outputsize : str
        "compact" (last 100 points) or "full" (up to 30 days for intraday)

    Returns
    -------
    pd.DataFrame
        DataFrame with ['Open', 'High', 'Low', 'Close', 'Volume'], sorted by datetime.
    """
    ts = TimeSeries(key=API_KEY, output_format="pandas")

    df, meta = ts.get_intraday(
        symbol=symbol,
        interval=interval,
        outputsize=outputsize
    )

    # Rename columns to match your OHLCV format

    # Convert index to datetime and sort
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    return df


## write a one to fetch daily data using time_series_daily

def fetch_daily_data(symbol: str, outputsize: str = "full") -> pd.DataFrame:
    """
    Fetch daily OHLCV data from Alpha Vantage.

    Parameters
    ----------
    symbol : str
        Stock ticker (e.g., "AAPL")
    outputsize : str
        "compact" (last 100 points) or "full" (up to 30 days for intraday)

    Returns
    -------
    pd.DataFrame
        DataFrame with ['Open', 'High', 'Low', 'Close', 'Volume'], sorted by datetime.
    """
    ts = TimeSeries(key=API_KEY, output_format="pandas")

    df, meta = ts.get_daily(
        symbol=symbol,
        outputsize=outputsize
    )

    # Rename columns to match your OHLCV format

    # Convert index to datetime and sort
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    return df


def fetch_data_to_csv(symbol: str, interval: str = "60min", outputsize: str = "full"):
    """
    Fetch both intraday and daily data and save to CSV files.
    """
    intraday_df = fetch_alpha(symbol, interval=interval, outputsize=outputsize)
    daily_df = fetch_daily_data(symbol, outputsize=outputsize)
    intraday_df.to_csv(f"data/{symbol}_{interval}.csv")
    daily_df.to_csv(f"data/{symbol}_daily.csv")

    print(f"Saved intraday data: {intraday_df.shape}")
    print(f"Saved daily data: {daily_df.shape}")

if __name__ == "__main__":
    stock_ticker_list = ["PYPL",
                     "CRCL",
                     "NVDA",
                     "VOO",
                     "RUM",
                     "COIN"]

    for stock_ticker in stock_ticker_list:
        fetch_data_to_csv(stock_ticker, interval="60min", outputsize="full")