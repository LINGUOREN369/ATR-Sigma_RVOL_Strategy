import pandas as pd
import numpy as np

def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """
    Average True Range (Wilder’s EMA). No lookahead handling here.
    """
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)

    tr = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)

    out = tr.ewm(span=window, min_periods=1, adjust=False).mean()
    return out.rename(f"ATR_{window}")

def rvol(df: pd.DataFrame, window: int = 20, method: str = "hybrid", alpha: float = 0.5) -> pd.Series:
    """
    Relative Volume (RVOL).
    method: 'sma' | 'ewm' | 'hybrid'
    alpha: weight for SMA in 'hybrid' (0 = pure EWM, 1 = pure SMA)
    """
    vol = df["Volume"]
    sma = vol.rolling(window).mean()
    ewm = vol.ewm(span=window, adjust=False).mean()

    if method == "sma":
        avg_vol = sma
    elif method == "ewm":
        avg_vol = ewm
    elif method == "hybrid":
        avg_vol = alpha * sma + (1 - alpha) * ewm
    else:
        raise ValueError("method must be 'sma', 'ewm', or 'hybrid'")

    out = vol / avg_vol.replace(0, np.nan)
    return out.rename(f"RVOL_{window}")

def price_deviation(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """
    Z-score of Close. No lookahead handling here.
    """
    mean = df["Close"].rolling(window).mean()
    std  = df["Close"].rolling(window).std()
    out = (df["Close"] - mean) / std
    return out.rename(f"PriceDev_{window}")