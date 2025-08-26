import pandas as pd
import numpy as np

def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)

    tr = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)

    # Exact Wilder smoothing:
    atr_wilder = tr.ewm(alpha=1/window, min_periods=1, adjust=False).mean()
    return atr_wilder.rename(f"ATR_{window}")


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

