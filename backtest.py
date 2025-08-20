import pandas as pd
import numpy as np
import datetime as dt

# your modules
from data_fetch import fetch          # not used in this script, but keep if you want
from technical_indicator import atr, rvol, price_deviation

pd.options.display.float_format = "{:.2f}".format

# --------------------
# Config
# --------------------
ATR_LOOKBACK_DAYS      = 14
RVOL_LOOKBACK_DAYS     = 20
PRICEDEV_LOOKBACK_DAYS = 20
RVOL_ALPHA             = 0.5   # hybrid rvol weight (SMA share)
ROLLING_WINDOW_DAYS    = 10    # for expected cumulative volume curve

# --------------------
# Build daily indicators
# --------------------
def build_indicators(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute ATR (Wilder EMA), historical RVOL (hybrid), and price sigma (z-score).
    Returns df with columns: Close, Volume, ATR, Hist_RVOL, Price_Sigma
    """
    atr_series   = atr(raw_df, ATR_LOOKBACK_DAYS)
    rvol_series  = rvol(raw_df, RVOL_LOOKBACK_DAYS, method="hybrid", alpha=RVOL_ALPHA)
    sigma_series = price_deviation(raw_df, PRICEDEV_LOOKBACK_DAYS)

    out = pd.concat(
        [raw_df["Close"], raw_df["Volume"], atr_series, rvol_series, sigma_series],
        axis=1
    )
    out.columns = ["Close", "Volume", "ATR", "Hist_RVOL", "Price_Sigma"]
    return out

# --------------------
# Rolling expected cumulative volume (no leakage)
# --------------------
def build_expected_cumvol(min_df: pd.DataFrame, window_days: int = 10) -> pd.DataFrame:
    """
    From minute-level df (index=datetime, columns include Volume), compute:
      - CumVolume per day
      - Pivot to Date x Time matrix
      - Rolling mean over last N days, shifted(1) to avoid using same day
      - Return long-form DF with Datetime index and column 'Exp_CumVolume_10d'
    """
    tmp = min_df.copy()
    tmp = tmp.sort_index()
    tmp.index = pd.to_datetime(tmp.index)

    # Day & time keys
    tmp["Date"] = tmp.index.date
    tmp["Time"] = tmp.index.time

    # Per-day cumulative volume & share
    tmp["CumVolume"] = tmp.groupby("Date")["Volume"].cumsum()
    day_tot = tmp.groupby("Date")["Volume"].transform("sum").replace(0, np.nan)
    tmp["CumVolumeShare"] = tmp["CumVolume"] / day_tot

    # Pivot (Date x Time) cumulative volume
    pivot_cum = tmp.pivot_table(index="Date", columns="Time", values="CumVolume")

    # Rolling mean over last N days; shift(1) to ensure today uses *prior* days only
    rolling_avg_vol = pivot_cum.rolling(window=window_days, min_periods=1).mean().shift(1)

    # Back to long form → (Date, Time, value)
    avg_cumvol = rolling_avg_vol.stack().reset_index()
    avg_cumvol.columns = ["Date", "Time", "Exp_CumVolume_10d"]

    # Build a proper Datetime index from Date + Time
    avg_cumvol["Datetime"] = pd.to_datetime(
        avg_cumvol["Date"].astype(str) + " " + avg_cumvol["Time"].astype(str)
    )
    avg_cumvol = avg_cumvol.set_index("Datetime").drop(columns=["Date", "Time"])
    return avg_cumvol

# --------------------Alyssa is right here like he's kinda just kind of interesting and she's eating a chocolate right now. You know kind of why it's gone crazy I just keep going. I was like what is going on actually because I was just humming the song so it was not like a nonsense like coding stuff, but I also have my gay pilot going on. Gay is my cope of a coding so basically you think about your driving have a copilot when writing a coat they also have a copilot.
# Main
# --------------------
if __name__ == "__main__":
    # === Load & prep historical daily ===
    hist_df = pd.read_csv("data/CRCL_daily.csv")
    hist_df["date"] = pd.to_datetime(hist_df["date"])
    hist_df = hist_df.set_index("date").sort_index()
    hist_df.columns = ["Open", "High", "Low", "Close", "Volume"]

    hist_TI_df = build_indicators(hist_df)

    # === Load & prep minute-level ===
    min_df = pd.read_csv("data/CRCL_min.csv")
    min_df["date"] = pd.to_datetime(min_df["date"])
    min_df = min_df.set_index("date").sort_index()
    min_df.columns = ["Open", "High", "Low", "Close", "Volume"]
    # Keep only what we need
    min_df = min_df[["Close", "Volume"]]

    # Per-day cumulative volume (today’s actuals)
    work = min_df.copy()
    work["Date"] = work.index.date
    work["Time"] = work.index.time
    work["CumVolume"] = work.groupby("Date")["Volume"].cumsum()

    # Build expected cumulative volume curve over rolling 10 days (no leakage)
    exp_cumvol = build_expected_cumvol(min_df, window_days=ROLLING_WINDOW_DAYS)
    exp_cumvol = exp_cumvol.rename(columns={"Exp_CumVolume_10d": "Exp_CumVolume_10d"})

    # Join expected cumvol back to minutes (align on Datetime index)
    # First, give `work` a DatetimeIndex identical to min_df’s index (it already is)
    joined = work.join(exp_cumvol, how="left")

    # Intraday RVOL (cumulative): reality vs expectation
    joined["Intraday_RVOL_cum"] = joined["CumVolume"] / joined["Exp_CumVolume_10d"]

    # Optional: clean helper columns if you only want core outputs saved
    # keep_cols = ["Close", "Volume", "CumVolume", "Exp_CumVolume_10d", "Intraday_RVOL_cum"]
    # joined = joined[keep_cols]

    # Inspect tails
    print("\n=== Daily indicators (tail) ===")
    print(hist_TI_df.tail())
    print("\n=== Minute + expected cumvol (tail) ===")
    print(joined.tail())

    # Save
    hist_TI_df.to_csv("out/CRCL_daily_indicators.csv")
    joined.to_csv("out/CRCL_min_with_intraday_rvol.csv")
    print("\nSaved:\n  out/CRCL_daily_indicators.csv\n  out/CRCL_min_with_intraday_rvol.csv")
    
    
    
    