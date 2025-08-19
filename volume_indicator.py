# price_volume_analysis.py
"""
Intraday price/volume analysis utilities built on yfinance.

What this script does (high level):
1) Downloads OHLCV data for a single symbol at the requested interval/period.
2) Normalizes the columns (handles MultiIndex and odd column names from yfinance).
3) Computes:
   - Typical Price (TP)
   - Per-session intraday VWAP
   - Price–volume profile (histogram of volume by price bins)
   - “Range fraction” features (where today’s TP sits inside day’s High–Low range)
   - Up/Down volume split (proxy for buying/selling pressure)
   - Daily RVOL (today’s volume vs. rolling average)
4) Prints a compact textual summary and writes CSVs for further analysis.

Notes:
- All intraday timestamps are converted to the provided timezone (`TZ`).
- Daily bars from yfinance are midnight-stamped UTC; we cosmetically shift them to 16:00 ET
  to match market close so your outputs line up with intuition.
"""

from __future__ import annotations
from datetime import datetime
from data_fetch import fetch
import re
import numpy as np
import pandas as pd
import yfinance as yf
from pathlib import Path

# ------------------------ User-configurable parameters ------------------------
SYMBOL   = "CRCL"        # Ticker to analyze (string)
INTERVAL = "1d"          # One of: '1m','2m','5m','15m','30m','1h','1d'
PERIOD   = "100d"          # One of: '1d','5d','1mo','3mo','6mo','1y'
TZ       = "America/New_York"  # Output timezone for intraday bars
INCLUDE_EXTENDED = False # If True (and intraday), include pre/after-market bars
N_PRICE_BINS = 40        # Number of price bins for the volume profile
RVOL_LOOKBACK_DAYS = 20  # Rolling window used for RVOL on daily bars

# Directory where CSV outputs will be saved
OUT_DIR = Path.cwd() / "volume_indicator_csv"  # change to Path(__file__).parent / "csv" if you prefer script-relative



# ==============================================================================
# Core Features
# ==============================================================================

def typical_price(df: pd.DataFrame) -> pd.Series:
    """
    Typical Price (TP) = (High + Low + Close) / 3

    Rationale: TP is a common proxy for “where trading happened”
    within the bar (more robust than just the close).

    Returns
    -------
    pd.Series
        Typical price per bar (float).
    """
    return (df["High"] + df["Low"] + df["Close"]) / 3.0


def vwap_by_day(df: pd.DataFrame) -> pd.Series:
    """
    Intraday Volume Weighted Average Price computed per *session* (resets each day).

    VWAP_t = cumulative( TP_t * Vol_t ) / cumulative( Vol_t ), grouped by day.

    Implementation detail:
    - We group by the UTC date (naive date) of each timestamp to avoid DST
      slicing issues; each “trading day” stays intact.

    Returns
    -------
    pd.Series
        Per-bar VWAP values (aligned to df.index) named "VWAP".
    """
    typical_price_series = typical_price(df)
    # Stable group key: naive UTC date for each bar
    day_group_keys = df.index.tz_convert("UTC").tz_localize(None).date

    cumulative_price_volume = (typical_price_series * df["Volume"]).groupby(day_group_keys).cumsum()
    cumulative_volume = df["Volume"].groupby(day_group_keys).cumsum().replace(0, np.nan)

    vwap = cumulative_price_volume / cumulative_volume
    vwap.name = "VWAP"
    return vwap


def volume_profile(df: pd.DataFrame, bins: int = 40) -> pd.DataFrame:
    """
    Aggregate traded volume into price bins based on each bar’s Typical Price.

    For each bar:
      - Find the price bin where its TP falls.
      - Add the bar’s volume to that bin.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with at least ['High','Low','Close','Volume'] columns.
    bins : int
        Number of equally-spaced price bins between min(TP) and max(TP).

    Returns
    -------
    pd.DataFrame
        Columns:
          - PriceBin : float midpoint of the bin
          - Volume   : total volume accumulated into that bin

        Sorted by PriceBin ascending.
    """
    typical_price_series = typical_price(df)
    volume_series = df["Volume"].astype(float)

    tp_min, tp_max = float(typical_price_series.min()), float(typical_price_series.max())
    if not np.isfinite(tp_min) or not np.isfinite(tp_max) or tp_min == tp_max:
        # Degenerate case: single price or NaN; return one bin with all volume
        return pd.DataFrame({
            "PriceBin": [tp_min if np.isfinite(tp_min) else 0.0],
            "Volume": [float(volume_series.sum())]
        })

    bin_edges = np.linspace(tp_min, tp_max, bins + 1)
    bin_index = np.digitize(typical_price_series.values, bin_edges) - 1
    bin_index = np.clip(bin_index, 0, bins - 1)

    volume_by_bin = np.bincount(bin_index, weights=volume_series.values, minlength=bins)
    bin_midpoints = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    profile_df = pd.DataFrame({"PriceBin": bin_midpoints, "Volume": volume_by_bin})
    return profile_df.sort_values("PriceBin", ascending=True, ignore_index=True)


def classify_range_fraction(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each bar, compute where its TP sits inside the *day’s* [Low, High] range.

    Definitions (per day):
      RangeFrac in [0, 1]:
        0.0 = at the day’s Low
        1.0 = at the day’s High

    Returns
    -------
    pd.DataFrame
        Original columns plus:
          - TP
          - RangeFrac
    """
    out = df.copy()
    tp = typical_price(out)

    day_key = out.index.tz_convert("UTC").tz_localize(None).date
    grp = out.groupby(day_key, group_keys=False)

    day_low  = grp["Low"].transform("min")
    day_high = grp["High"].transform("max")
    rng = (day_high - day_low).replace(0, np.nan)

    frac = (tp - day_low) / rng
    out["TP"] = tp
    out["RangeFrac"] = frac.clip(0, 1)

    return out


def up_down_volume(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identity pass-through. We now prefer day-over-day volume change over up/down buckets.

    Returns
    -------
    pd.DataFrame
        Unmodified input DataFrame.
    """
    return df


def rvol_daily(
    symbol: str,
    tz: str,
    lookback: int = 20,
    use_adjusted: bool = True
) -> pd.DataFrame:
    """
    Compute daily Relative Volume (RVOL) on daily bars:
      RVOL = TodayVolume / RollingAverageVolume(lookback)

    We download roughly 3× the lookback (min 60 days) to ensure a stable average.

    Parameters
    ----------
    symbol : str
        Ticker symbol.
    tz : str
        Timezone for the output index.
    lookback : int
        Rolling window length for average volume.
    use_adjusted : bool
        If True, request auto_adjust=True for prices (does not affect volume).

    Returns
    -------
    pd.DataFrame
        Columns:
          - Close
          - Volume
          - AvgVol (rolling mean over `lookback`)
          - RVOL   (= Volume / AvgVol)
        Index is timezone-aware and cosmetically shifted to 16:00 local if
        the source stamps daily bars at midnight (common in yfinance).
    """
    dfd = yf.download(
        symbol,
        interval="1d",
        period=f"{max(lookback * 3, 60)}d",
        auto_adjust=use_adjusted,
        prepost=False,
        progress=False,
    )
    if dfd.empty:
        return pd.DataFrame()

    dfd.index = pd.to_datetime(dfd.index, utc=True).tz_convert(tz)

    # Handle MultiIndex columns if present
    if isinstance(dfd.columns, pd.MultiIndex):
        if symbol in dfd.columns.get_level_values(0):
            dfd = dfd.xs(symbol, axis=1, level=0)
        elif symbol in dfd.columns.get_level_values(1):
            dfd = dfd.xs(symbol, axis=1, level=1)
        else:
            dfd.columns = [' '.join([str(p) for p in tup if p]).strip() for tup in dfd.columns]

    dfd = dfd.rename(columns={c: str(c).title() for c in dfd.columns})

    if "Volume" not in dfd.columns:
        return pd.DataFrame()

    out = dfd.copy()
    out["AvgVol"] = (
        out["Volume"]
        .rolling(lookback, min_periods=lookback // 2)
        .mean()
        .fillna(0)       # Avoid division by NaN; interpret as 0 until enough history
        .astype(int)     # Friendly integer display; if you prefer floats, drop this
    )
    out["RVOL"] = out["Volume"] / out["AvgVol"].replace(0, np.nan)

    # Cosmetic index shift: many daily series show 00:00; move to 16:00 local for readability
    idx_local = out.index.tz_convert(tz)
    if all((idx_local.hour == 0) & (idx_local.minute == 0)):
        out.index = idx_local.normalize() + pd.Timedelta(hours=16)

    price_col = "Close" if "Close" in out.columns else ("Adj Close" if "Adj Close" in out.columns else None)
    cols = [c for c in [price_col, "Volume", "AvgVol", "RVOL"] if c in out.columns]
    return out[cols].rename(columns={price_col: "Close"}) if cols else out[["Volume","AvgVol","RVOL"]]

# ==============================================================================
# Feature aggregation (single, per-bar frame)
# ==============================================================================

def make_feature_frame(
    bars: pd.DataFrame,
    tz: str,
    daily_rvol: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Return a single per-bar feature frame with aligned timestamps containing:
      - OHLCV
      - TP (Typical Price)
      - VWAP (per-session if intraday; may be NaN for daily)
      - UpVol / DownVol
      - RangeFrac / RangeBucket
      - (optional) RVOL_Daily mapped from daily bars onto each bar's session date

    Notes
    -----
    * Volume profiles are price-bin histograms, not time-indexed → kept separate.
    * Bucketed day totals (e.g., bucket_vol) are day-indexed → kept separate.
    """
    # Start from bars to preserve index
    out = bars.copy()

    # Ensure the canonical features are present
    # 1) Typical Price
    out["TP"] = typical_price(out)

    # 2) (no per-bar signed volume)
    # We rely on daily volume change mapped below.

    # 3) Range fraction & bucket (per-session day)
    day_key = out.index.tz_convert("UTC").tz_localize(None).date
    grp = out.groupby(day_key, group_keys=False)
    day_low  = grp["Low"].transform("min")
    day_high = grp["High"].transform("max")
    rng = (day_high - day_low).replace(0, np.nan)

    frac = (out["TP"] - day_low) / rng
    out["RangeFrac"] = frac.clip(0, 1)

    # 4) VWAP per session if not already present
    if "VWAP" not in out.columns or out["VWAP"].isna().all():
        try:
            out["VWAP"] = vwap_by_day(out)
        except Exception:
            out["VWAP"] = np.nan

    # 5) Optional: map daily RVOL and related columns to each bar by session date
    if daily_rvol is not None and not daily_rvol.empty:
        # Build mappings from daily date → value
        daily_key = daily_rvol.index.tz_convert("UTC").tz_localize(None).date
        # Ensure alignment order by date
        daily_rvol_sorted = daily_rvol.copy()
        daily_rvol_sorted = daily_rvol_sorted.loc[~pd.Index(daily_key).duplicated(keep="last")] if len(daily_key) != len(set(daily_key)) else daily_rvol_sorted
        daily_key = daily_rvol_sorted.index.tz_convert("UTC").tz_localize(None).date

        if "RVOL" in daily_rvol_sorted.columns:
            rvol_map = pd.Series(daily_rvol_sorted["RVOL"].values, index=daily_key)
            out["RVOL_Daily"] = pd.Index(day_key).map(rvol_map).astype(float)
        if "AvgVol" in daily_rvol_sorted.columns:
            avgvol_map = pd.Series(daily_rvol_sorted["AvgVol"].values, index=daily_key)
            out["AvgVol_Daily"] = pd.Index(day_key).map(avgvol_map).astype(float)
        if "Volume" in daily_rvol_sorted.columns:
            dvol = pd.Series(daily_rvol_sorted["Volume"].values, index=daily_key)
            out["DailyVolume"] = pd.Index(day_key).map(dvol).astype(float)
            # Day-over-day change and percent change
            dvol_change = dvol.diff()
            dvol_chg_pct = dvol.pct_change()
            out["DailyVolChange"] = pd.Index(day_key).map(dvol_change).astype(float)
            out["DailyVolChangePct"] = pd.Index(day_key).map(dvol_chg_pct).astype(float)

    return out

# ==============================================================================
# MAIN (REAL DATA)
# ==============================================================================

if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # 1) Pull intraday (or daily) bars for the configured symbol
    df = fetch(SYMBOL, INTERVAL, PERIOD, TZ, INCLUDE_EXTENDED)

    # 2) Per-session intraday VWAP (only meaningful for intraday intervals)
    if INTERVAL.endswith(("m", "h")):
        df["VWAP"] = vwap_by_day(df)
    else:
        df["VWAP"] = np.nan  # Placeholder for daily bars

    # 3) Enrich bars with Up/Down volume and range-fraction features
    df2 = up_down_volume(df)
    df3 = classify_range_fraction(df2)

    # Identify the latest session (by UTC date key) for "today" summaries
    day_key = df3.index.tz_convert("UTC").tz_localize(None).date
    last_day = day_key[-1]
    today = df3[day_key == last_day]

    # Global and last-session volume profiles
    prof_all  = volume_profile(df3, bins=N_PRICE_BINS)
    prof_last = volume_profile(today, bins=max(10, N_PRICE_BINS // 2)) if not today.empty else pd.DataFrame()

    # Volume concentration by range fraction buckets for each day (without RangeBucket column)
    upper_mask = df3["RangeFrac"] > (2/3)
    lower_mask = df3["RangeFrac"] < (1/3)
    middle_mask = ~(upper_mask | lower_mask)

    bucket_vol = pd.DataFrame({
        "upper": df3["Volume"].where(upper_mask, 0).groupby(day_key).sum(),
        "middle": df3["Volume"].where(middle_mask, 0).groupby(day_key).sum(),
        "lower": df3["Volume"].where(lower_mask, 0).groupby(day_key).sum(),
    }).fillna(0)
    bucket_vol["Total"] = bucket_vol.sum(axis=1)
    bucket_vol["UpperPct"]  = bucket_vol["upper"]  / bucket_vol["Total"].replace(0, np.nan)
    bucket_vol["MiddlePct"] = bucket_vol["middle"] / bucket_vol["Total"].replace(0, np.nan)
    bucket_vol["LowerPct"]  = bucket_vol["lower"]  / bucket_vol["Total"].replace(0, np.nan)
    # Single-label per day: which bucket dominates by volume share
    bucket_vol["DominantBucket"] = bucket_vol[["UpperPct", "MiddlePct", "LowerPct"]].idxmax(axis=1)


    # 4) Daily RVOL (separate daily download)
    dfd_rvol = rvol_daily(SYMBOL, TZ, RVOL_LOOKBACK_DAYS, use_adjusted=True)

    # Build single per-bar feature frame
    feature_df = make_feature_frame(df, TZ, dfd_rvol)
    # Map per-day dominant bucket label to each bar
    bar_day_key = feature_df.index.tz_convert("UTC").tz_localize(None).date
    if "DominantBucket" in bucket_vol.columns:
        dom_map = pd.Series(bucket_vol["DominantBucket"].astype(str).values,
                            index=bucket_vol.index)
        feature_df["DominantBucket"] = pd.Index(bar_day_key).map(dom_map)

    # ------------------------ Console prints (compact) ------------------------
    pd.options.display.float_format = '{:.2f}'.format
    print(f"\n=== DATA SUMMARY: {SYMBOL} [{PERIOD}/{INTERVAL}] tz={TZ} prepost={INCLUDE_EXTENDED} ===")
    print(df.tail(3)[["Open", "High", "Low", "Close", "Volume", "VWAP"]])

    print("\n--- Combined per-bar features (tail) ---")
    cols_show = [
        "Open","High","Low","Close","Volume","VWAP","TP",
        "RangeFrac",
        "DailyVolume","DailyVolChange","DailyVolChangePct","AvgVol_Daily","RVOL_Daily"
    ]
    cols_show = [c for c in cols_show if c in feature_df.columns]
    print(feature_df.tail(100)[cols_show])

    if not today.empty:
        t_lo, t_hi = float(today["Low"].min()), float(today["High"].max())
        print("\n--- Today’s Range & Concentration ---")
        print(f"Day Low/High: {t_lo:.2f} / {t_hi:.2f}")
        # Show last few days with a single dominant label
        print(bucket_vol.tail(20)[["DominantBucket"]])
        print(f"Today label: {bucket_vol.iloc[-1]['DominantBucket']}")


    print("\n--- Volume Profile (All, top 10 bins) ---")
    print(prof_all.sort_values("Volume", ascending=False).head(10))

    if not prof_last.empty:
        print("\n--- Volume Profile (Last Session, top 5 bins) ---")
        print(prof_last.sort_values("Volume", ascending=False).head(5))

    if not dfd_rvol.empty:
        print("\n--- Daily RVOL (last 90 rows) ---")
        print(dfd_rvol.tail(90))

    # ------------------------ Save CSV outputs ------------------------
    # Filenames include a timestamp to avoid overwriting previous runs.
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    feature_df.to_csv(OUT_DIR / f"{SYMBOL}_{INTERVAL}_{PERIOD}_features_oneframe_{ts}.csv")
    prof_all.to_csv(OUT_DIR / f"{SYMBOL}_{INTERVAL}_{PERIOD}_volume_profile_all_{ts}.csv", index=False)