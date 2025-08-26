# portfolio_eval.py
# ===================
# - Loads daily and minute data for a stock.
# - Calculates daily indicators (ATR, RVOL) and intraday cumulative RVOL.
# - Runs a backtest on a simple trading strategy using these indicators.
# - Evaluates and prints the portfolio performance.

import re
from pathlib import Path
import numpy as np
import pandas as pd

# Assume technical_indicator.py with atr() and rvol() exists in the same directory
from technical_indicator import atr, rvol

pd.options.display.float_format = "{:.2f}".format

# ==========================
# Config
# ==========================
class Config:
    # Use your data files here
    STOCK = "AAPL"
    DAILY_FILE = f"data/{STOCK}_daily.csv"
    MINUTE_FILE = f"data/{STOCK}_min.csv"

    # Strategy Parameters (shorter lookbacks for more responsive signals)
    ATR_LOOKBACK_DAYS = 5
    RVOL_LOOKBACK_DAYS = 10
    ROLLING_WINDOW_DAYS = 5
    RVOL_ALPHA = 0.5

    # Backtest Parameters
    INITIAL_CAPITAL = 10000.00
    TRADE_SHARES = 100
    RVOL_ENTRY_THRESHOLD = 1.5
    ATR_BAND_MULTIPLIER = 1.5 # Controls the width of the ATR bands

# ==========================
# Data Loading (from your script)
# ==========================
def load_ohlcv_csv(filepath: str) -> pd.DataFrame:
    """
    Load OHLCV CSV and normalize to ['Open','High','Low','Close','Volume'].
    """
    df = pd.read_csv(filepath)
    date_col = None
    for c in df.columns:
        if str(c).strip().lower() in {"date", "datetime", "timestamp"}:
            date_col = c
            break
    if date_col is None:
        raise ValueError(f"No date/datetime column found in {filepath}.")
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.set_index(date_col).sort_index()

    norm = {c: re.sub(r"[^a-z]", "", str(c).lower()) for c in df.columns}
    wants = {
        "Open": {"open"}, "High": {"high"}, "Low": {"low"},
        "Close": {"close", "adjclose"}, "Volume": {"volume"},
    }
    chosen, used = {}, set()
    for target, keys in wants.items():
        for orig, n in norm.items():
            if n in keys and orig not in used:
                chosen[target] = orig
                used.add(orig)
                break
    if len(chosen) < 5:
        raise ValueError(f"Could not coerce to OHLCV. Found: {chosen}")
    out = df[list(chosen.values())].copy()
    out.columns = list(chosen.keys())
    return out

# ==========================
# Indicator Calculations (from your script)
# ==========================
def daily_indicators(daily_df: pd.DataFrame, k: float) -> pd.DataFrame:
    """
    Returns daily frame with Close, Volume, ATR, Hist_RVOL,
    and yesterday's data for lookahead-free backtesting.
    """
    out = daily_df[["Close", "Volume"]].copy()
    out["ATR"] = atr(daily_df, Config.ATR_LOOKBACK_DAYS)
    out["Hist_RVOL"] = rvol(daily_df, Config.RVOL_LOOKBACK_DAYS, method="hybrid", alpha=Config.RVOL_ALPHA)
    out["Y_Close"] = out["Close"].shift(1)
    out["Y_ATR"] = out["ATR"].shift(1)
    out["Y_ATR_Upper"] = out["Y_Close"] + k * out["Y_ATR"]
    out["Y_ATR_Lower"] = out["Y_Close"] - k * out["Y_ATR"]
    return out

def expected_cumvol(min_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build rolling expected cumulative volume by minute-of-day.
    """
    tmp = min_df.copy().sort_index()
    tmp["Date"] = tmp.index.normalize()
    tmp["Time"] = tmp.index.time
    tmp["CumVolume"] = tmp.groupby("Date")["Volume"].cumsum()
    pivot_cum = tmp.pivot_table(index="Date", columns="Time", values="CumVolume")
    exp_curve = pivot_cum.rolling(window=Config.ROLLING_WINDOW_DAYS, min_periods=1).mean().shift(1)
    exp_long = exp_curve.stack().reset_index()
    exp_long.columns = ["Date", "Time", "Exp_CumVolume"]
    exp_long["Datetime"] = pd.to_datetime(exp_long["Date"].astype(str) + " " + exp_long["Time"].astype(str))
    return exp_long.set_index("Datetime").drop(columns=["Date", "Time"])

def intraday_rvol(min_df: pd.DataFrame, exp_cum_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Intraday_RVOL_cum = CumVolume / Exp_CumVolume.
    """
    df = min_df[["Close", "Volume"]].copy().sort_index()
    df["Date"] = df.index.normalize()
    df["CumVolume"] = df.groupby("Date")["Volume"].cumsum()
    joined = df.join(exp_cum_df, how="left")
    joined["Intraday_RVOL_cum"] = joined["CumVolume"] / joined["Exp_CumVolume"]
    return joined

def attach_yesterday_daily_to_minutes(intraday_df: pd.DataFrame, daily_ind: pd.DataFrame) -> pd.DataFrame:
    """
    Maps yesterday's daily data to today's minutes for a lookahead-free signal.
    """
    out = intraday_df.copy()
    out["Date"] = pd.to_datetime(out.index).normalize()
    d = daily_ind.copy()
    d.index = pd.to_datetime(d.index).normalize()
    ycols = ["Y_Close", "Y_ATR", "Y_ATR_Upper", "Y_ATR_Lower", "Hist_RVOL"]
    out = out.join(d[ycols], on="Date")
    return out

# ==========================
# NEW: Backtesting Engine
# ==========================
def run_backtest(df: pd.DataFrame):
    """
    Runs the backtest on the enriched intraday dataframe.
    """
    cash = Config.INITIAL_CAPITAL
    position = 0  # 0: flat, 1: long, -1: short
    shares = 0
    
    trades = []
    portfolio_history = []

    # Group by day to handle daily exits
    for date, day_df in df.groupby(df.index.date):
        for index, row in day_df.iterrows():
            # --- ENTRY LOGIC ---
            # Check for entry signals only if we are flat
            if position == 0:
                # LONG entry condition
                if row['Intraday_RVOL_cum'] > Config.RVOL_ENTRY_THRESHOLD and row['Close'] > row['Y_ATR_Upper']:
                    position = 1
                    shares = Config.TRADE_SHARES
                    trade_cost = shares * row['Close']
                    cash -= trade_cost
                    trades.append({'Date': index, 'Action': 'BUY', 'Shares': shares, 'Price': row['Close'], 'Cost': trade_cost})
                
                # SHORT entry condition
                elif row['Intraday_RVOL_cum'] > Config.RVOL_ENTRY_THRESHOLD and row['Close'] < row['Y_ATR_Lower']:
                    position = -1
                    shares = Config.TRADE_SHARES
                    trade_credit = shares * row['Close']
                    cash += trade_credit
                    trades.append({'Date': index, 'Action': 'SELL_SHORT', 'Shares': shares, 'Price': row['Close'], 'Credit': trade_credit})

        # --- END-OF-DAY EXIT LOGIC ---
        # At the end of the day (last bar), close any open position
        if position != 0:
            last_price = day_df['Close'].iloc[-1]
            if position == 1: # Close long
                cash += shares * last_price
                trades.append({'Date': day_df.index[-1], 'Action': 'SELL_CLOSE', 'Shares': shares, 'Price': last_price})
            elif position == -1: # Close short
                cash -= shares * last_price
                trades.append({'Date': day_df.index[-1], 'Action': 'BUY_COVER', 'Shares': shares, 'Price': last_price})
            
            position = 0
            shares = 0

        # Record portfolio value at the end of the day
        portfolio_value = cash # Since we are flat at end of day
        portfolio_history.append({'Date': date, 'Portfolio_Value': portfolio_value})

    return pd.DataFrame(trades), pd.DataFrame(portfolio_history)

def evaluate_performance(trades_df: pd.DataFrame, portfolio_df: pd.DataFrame):
    """
    Calculates and prints key performance metrics.
    """
    if trades_df.empty or portfolio_df.empty:
        print("No trades were made. Cannot evaluate performance.")
        return

    print("\n" + "="*30)
    print("PORTFOLIO PERFORMANCE EVALUATION")
    print("="*30)

    final_value = portfolio_df['Portfolio_Value'].iloc[-1]
    total_return_pct = (final_value - Config.INITIAL_CAPITAL) / Config.INITIAL_CAPITAL * 100
    
    print(f"\nInitial Capital:      ${Config.INITIAL_CAPITAL:,.2f}")
    print(f"Final Portfolio Value:  ${final_value:,.2f}")
    print(f"Total Return:           {total_return_pct:.2f}%")
    
    print("\n--- Trade Statistics ---")
    num_trades = len(trades_df) // 2 # Each trade has an entry and exit
    print(f"Total Trades Executed:  {int(num_trades)}")
    
    profits = []
    losses = []
    
    for i in range(0, len(trades_df), 2):
        entry = trades_df.iloc[i]
        exit = trades_df.iloc[i+1]
        
        if entry['Action'] == 'BUY':
            pnl = (exit['Price'] - entry['Price']) * entry['Shares']
        else: # SELL_SHORT
            pnl = (entry['Price'] - exit['Price']) * entry['Shares']

        if pnl > 0:
            profits.append(pnl)
        else:
            losses.append(pnl)
            
    win_rate = (len(profits) / num_trades * 100) if num_trades > 0 else 0
    avg_win = sum(profits) / len(profits) if profits else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    
    print(f"Winning Trades:         {len(profits)}")
    print(f"Losing Trades:          {len(losses)}")
    print(f"Win Rate:               {win_rate:.2f}%")
    print(f"Average Win:            ${avg_win:,.2f}")
    print(f"Average Loss:           ${avg_loss:,.2f}")

    print("\n--- Portfolio History (Last 10 Days) ---")
    print(portfolio_df.tail(10).to_string(index=False))

    print("\n--- Trade Log (Last 10 Trades) ---")
    print(trades_df.tail(10).to_string(index=False))


# ==========================
# Main Execution
# ==========================
def main():
    """
    Main function to orchestrate data loading, indicator calculation,
    and backtesting.
    """
    OUT_DIR = Path("out")
    OUT_DIR.mkdir(exist_ok=True)

    # --- 1. Load Data ---
    daily_df = load_ohlcv_csv(Config.DAILY_FILE)
    minute_df = load_ohlcv_csv(Config.MINUTE_FILE)[["Close", "Volume"]]

    # --- 2. Calculate Indicators ---
    daily_ind = daily_indicators(daily_df, k=Config.ATR_BAND_MULTIPLIER)
    exp_cum = expected_cumvol(minute_df)
    intraday = intraday_rvol(minute_df, exp_cum)

    # --- 3. Create Final DataFrame for Backtesting ---
    # This dataframe has all the necessary signals for each minute
    intraday_enriched = attach_yesterday_daily_to_minutes(intraday, daily_ind)
    intraday_enriched.dropna(inplace=True) # Important: remove rows where indicators are not yet calculated

    # --- 4. Run Backtest ---
    print("Running backtest...")
    trades_log, portfolio_history = run_backtest(intraday_enriched)

    # --- 5. Evaluate and Display Results ---
    evaluate_performance(trades_log, portfolio_history)

if __name__ == "__main__":
    main()