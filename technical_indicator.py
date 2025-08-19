import pandas as pd
import numpy as np
from data_fetch import fetch 
from datetime import datetime

# ==========================
# Config Parameters
# ==========================
SYMBOL = "CRCL"
TZ = "America/New_York"

DATA_INTERVAL = "1d"
DATA_PERIOD   = "1y"
DATA_PREPOST  = False

ATR_LOOKBACK_DAYS      = 14
RVOL_LOOKBACK_DAYS     = 20
PRICEDEV_LOOKBACK_DAYS = 20

RVOL_ALPHA = 0.5   # weight for SMA in hybrid RVOL (0 = pure EWM, 1 = pure SMA)

# Display floats with 2 decimal places
pd.options.display.float_format = "{:.2f}".format


# ==========================
# Indicator Functions
# ==========================
def atr(df: pd.DataFrame, window: int = 14, mode: str = "backtest") -> pd.Series:
    """
    Compute Average True Range (ATR) using Wilder’s smoothing (EMA).
    This is the market-standard definition.

    Parameters
    ----------
    df : DataFrame with ['High','Low','Close']
    window : int, lookback period
    mode : 'backtest' → shift(1) to avoid lookahead
           'live'     → include current bar

    Returns
    -------
    pd.Series of ATR values
    """
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)

    tr = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)

    atr = tr.ewm(span=window, min_periods=1, adjust=False).mean()

    if mode == "backtest":
        atr = atr.shift(1)

    return atr.rename(f"ATR_{window}")


def rvol(df: pd.DataFrame, window: int = 20, method: str = "hybrid",
         alpha: float = 0.5, mode: str = "backtest") -> pd.Series:
    """
    Compute Relative Volume (RVOL).

    Parameters
    ----------
    df : DataFrame with ['Volume']
    window : int, lookback period
    method : "sma", "ewm", or "hybrid"
        - "sma"    : simple moving average
        - "ewm"    : exponential weighted mean
        - "hybrid" : blend of SMA and EWM
    alpha : float, 0..1, blending weight (SMA share in "hybrid").
            e.g. 0.7 = 70% SMA + 30% EWM
    mode : 'backtest' → shift(1) to avoid lookahead
           'live'     → include current bar

    Returns
    -------
    pd.Series of RVOL values
    """
    sma = df["Volume"].rolling(window).mean()
    ewm = df["Volume"].ewm(span=window, adjust=False).mean()

    if method == "sma":
        avg_vol = sma
    elif method == "ewm":
        avg_vol = ewm
    elif method == "hybrid":
        avg_vol = alpha * sma + (1 - alpha) * ewm
    else:
        raise ValueError("method must be 'sma', 'ewm', or 'hybrid'")

    if mode == "backtest":
        avg_vol = avg_vol.shift(1)

    rvol = df["Volume"] / avg_vol.replace(0, np.nan)
    return rvol.rename(f"RVOL_{window}")


def price_deviation(df: pd.DataFrame, window: int = 20,
                    mode: str = "backtest") -> pd.Series:
    """
    Calculate z-score style price deviation.

    Parameters
    ----------
    df : DataFrame with 'Close'
    window : int, lookback period
    mode : 'backtest' → exclude current bar
           'live'     → include current bar

    Returns
    -------
    pd.Series with deviation values
    """
    mean = df["Close"].rolling(window).mean()
    std  = df["Close"].rolling(window).std()

    if mode == "backtest":
        mean = mean.shift(1)
        std  = std.shift(1)

    return ((df["Close"] - mean) / std).rename(f"PriceDev_{window}")


# ==========================
# Build Indicators
# ==========================
def build_indicators(symbol: str, tz: str,
                     mode: str = "backtest") -> pd.DataFrame:
    """
    Fetch raw data and compute indicators: ATR, RVOL, Price Deviation.

    Returns
    -------
    DataFrame with columns [Close, Volume, ATR, RVOL, PriceDev]
    """
    raw_df = fetch(symbol, DATA_INTERVAL, period=DATA_PERIOD,
                   tz=tz, prepost=DATA_PREPOST)

    atr_series   = atr(raw_df, ATR_LOOKBACK_DAYS, mode=mode)
    rvol_series  = rvol(raw_df, RVOL_LOOKBACK_DAYS,
                        method="hybrid", alpha=RVOL_ALPHA, mode=mode)
    sigma_series = price_deviation(raw_df, PRICEDEV_LOOKBACK_DAYS, mode=mode)

    combined_df = pd.concat(
        [raw_df["Close"], raw_df["Volume"], atr_series,
         rvol_series, sigma_series],
        axis=1
    )
    combined_df.columns = ["Close", "Volume", "ATR", "RVOL", "Price_Sigma"]

    return combined_df


# ==========================
# Main
# ==========================
if __name__ == "__main__":
    for mode in ["backtest", "live"]:
        df = build_indicators(SYMBOL, TZ, mode=mode)
        print(f"\n=== {mode.upper()} mode ===")
        print(df.tail())

        # export csv
        df.to_csv(f"{datetime.today():%Y-%m-%d}_{SYMBOL}_{mode}_indicators.csv")