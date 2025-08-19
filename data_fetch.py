import pandas as pd
import numpy as np
import yfinance as yf
import re
from pathlib import Path


def _pick_symbol_level(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    If yfinance returns MultiIndex columns (common when requesting multiple tickers),
    reduce to a single level for `symbol`.

    Supports both layouts:
      - Level 0 = symbol, Level 1 = field (Open/High/...)
      - Level 0 = field,  Level 1 = symbol

    If no clear match is found, we fall back to flattening the columns.

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame as returned by yfinance.
    symbol : str
        Ticker to select from MultiIndex columns.

    Returns
    -------
    pd.DataFrame
        DataFrame reduced to a single symbol with simple columns.
    """
    if not isinstance(df.columns, pd.MultiIndex):
        return df

    lv0 = df.columns.get_level_values(0)
    lv1 = df.columns.get_level_values(1)

    if symbol in lv0:
        return df.xs(symbol, axis=1, level=0)
    if symbol in lv1:
        return df.xs(symbol, axis=1, level=1)

    # Fallback: flatten into single strings like "Open AAPL" or "AAPL Open".
    out = df.copy()
    out.columns = [' '.join([str(p) for p in tup if p]).strip() for tup in df.columns]
    return out


def _coerce_ohlcv(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Force the DataFrame into canonical OHLCV columns:
    ['Open', 'High', 'Low', 'Close', 'Volume'].

    yfinance sometimes returns odd cases:
      - 'Adj Close'
      - lowercase names
      - prefixed with the ticker (e.g., 'AAPL Close')

    We normalize heuristically and error out if we cannot find
    a 1:1 mapping to the 5 columns.

    Parameters
    ----------
    df : pd.DataFrame
        Input with some superset/variant of OHLCV columns.
    symbol : str
        Ticker symbol used to strip any ticker tokens from column names.

    Returns
    -------
    pd.DataFrame
        Exact columns ['Open','High','Low','Close','Volume'] (in that order).

    Raises
    ------
    RuntimeError
        If we cannot identify all 5 desired columns.
    """
    # Fast path: already correct
    if all(c in df.columns for c in ["Open","High","Low","Close","Volume"]):
        return df[["Open","High","Low","Close","Volume"]]

    sym_low = symbol.lower()
    norm = {}
    for c in df.columns:
        # Remove the ticker token and keep only letters to simplify comparisons
        s = re.sub(rf"{re.escape(sym_low)}", "", str(c).lower())
        s = re.sub(r"[^a-z]", "", s)
        norm[c] = s

    # Accepted normalized keys for each target column
    wants = {
        "Open":   {"open"},
        "High":   {"high"},
        "Low":    {"low"},
        "Close":  {"close", "adjclose"},
        "Volume": {"volume", "vol"},
    }

    chosen, used = {}, set()
    for target, keys in wants.items():
        for orig, n in norm.items():
            if orig in used:
                continue
            if n in keys:
                chosen[target] = orig
                used.add(orig)
                break

    if len(chosen) == 5:
        out = df[list(chosen.values())].copy()
        out.columns = ["Open","High","Low","Close","Volume"]
        return out

    raise RuntimeError(
        "Expected OHLCV columns not found after normalization.\n"
        f"Raw columns: {list(df.columns)}\n"
        f"Normalized (first 10 map): {dict(list(norm.items())[:10])}"
    )

# ==============================================================================
# Data Fetch (REAL DATA)
# ==============================================================================

def fetch(symbol: str, interval: str, period: str, tz: str, prepost: bool) -> pd.DataFrame:
    """
    Download OHLCV data from yfinance and normalize columns.

    Parameters
    ----------
    symbol : str
        Ticker to download (e.g., "AAPL").
    interval : str
        yfinance interval string, e.g., "1m", "15m", "1h", "1d".
    period : str
        yfinance period string, e.g., "5d", "1mo", "6mo".
    tz : str
        IANA timezone name for the output index, e.g., "America/New_York".
    prepost : bool
        Include pre/after-market bars for intraday intervals.

    Returns
    -------
    pd.DataFrame
        Normalized OHLCV DataFrame indexed by timezone-aware timestamps.

    Raises
    ------
    RuntimeError
        If no data is returned.
    """
    df = yf.download(
        symbol,
        interval=interval,
        period=period,
        auto_adjust=True,                                 # Adjust prices for splits/dividends
        prepost=prepost if interval != "1d" else False,   # yfinance ignores pre/post for daily
        progress=False,
    )
    if df.empty:
        raise RuntimeError(f"No data returned for {symbol} [{period}/{interval}]")

    # Ensure tz-aware index in the requested timezone
    df.index = pd.to_datetime(df.index, utc=True).tz_convert(tz)

    # Handle possible MultiIndex columns and odd names
    df = _pick_symbol_level(df, symbol)

    # Title-case simple names to a consistent format
    if not isinstance(df.columns, pd.MultiIndex):
        df = df.rename(columns={c: str(c).title() for c in df.columns})

    return _coerce_ohlcv(df, symbol)