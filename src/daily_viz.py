import pandas as pd
import matplotlib.pyplot as plt
import config
import matplotlib.ticker as mtick
from pathlib import Path


def daily_data_feature_viz(
    df_feature: pd.DataFrame,
    feature: str,
    show = config.SHOW_PLOTS,
    context_df: pd.DataFrame | None = None,
):
    """
    Visualizes a specified feature from daily data with a given lookback period.

    Parameters:
    - df_feature (pd.DataFrame): DataFrame containing the feature to visualize.
    - feature (str): The feature/column name to visualize.
    """
    daily_date_range = df_feature.shape[0]
    plt.figure(figsize=config.FIG_SIZE)
    plt.plot(df_feature.index, df_feature[feature], marker="o", label=feature.capitalize())
    title = (
        f"{config.STOCK_TICKER} Daily {feature.capitalize()} "
        f"with {daily_date_range}-Day Range \n from {df_feature.index.min().date()} "
        f"to {df_feature.index.max().date()}"
    )
    plt.xlabel("Date")
    plt.ylabel(feature.capitalize())
    
    ax = plt.gca()
    if feature.lower() == "volume":
        # # Option A: show commas
        # ax.ticklabel_format(style="plain", axis="y")
        # ax.yaxis.set_major_formatter(
        #     mtick.FuncFormatter(lambda x, _: f"{int(x):,}")
        # )
        # Option B: show in millions (uncomment if preferred)
        ax.yaxis.set_major_formatter(
            mtick.FuncFormatter(lambda x, _: f"{x/1e6:.1f}M")
        )

    # If this is the close series, overlay Bollinger Bands
    if feature.lower() == "close":
        window = int(getattr(config, "BOLLINGER_WINDOW", 20))
        num_std = float(getattr(config, "BOLLINGER_NUM_STD", 2.0))
        ma_method = str(getattr(config, "BOLLINGER_MA_METHOD", "sma")).lower()
        # Compute bands on full context if provided, then align to the visible window.
        close_series = (
            context_df[feature]
            if context_df is not None and feature in context_df.columns
            else df_feature[feature]
        )
        if ma_method == "ema":
            ma_full = close_series.ewm(span=window, adjust=False).mean()
        else:
            ma_full = close_series.rolling(window=window, min_periods=window).mean()
        std_full = close_series.rolling(window=window, min_periods=window).std(ddof=0)
        upper_full = ma_full + num_std * std_full
        lower_full = ma_full - num_std * std_full

        # Align to the plotting index
        ma = ma_full.reindex(df_feature.index)
        upper = upper_full.reindex(df_feature.index)
        lower = lower_full.reindex(df_feature.index)

        valid = ~(upper.isna() | lower.isna())
        # Shaded band
        plt.fill_between(
            df_feature.index[valid],
            lower[valid],
            upper[valid],
            color="tab:blue",
            alpha=0.15,
            label=f"BB ({ma_method.upper()}, n={window}, ±{num_std}σ)"
        )
        # Middle band (MA)
        plt.plot(df_feature.index, ma, color="tab:purple", linewidth=1.5, label=f"MA {ma_method.upper()} {window}")

        # Append method to title
        title += f"\nBollinger MA: {ma_method.upper()} (n={window}, k={num_std})"

    ## include line for median, quartiles
    median_val = df_feature[feature].median()
    q1_val = df_feature[feature].quantile(0.25)
    q3_val = df_feature[feature].quantile(0.75)
    plt.axhline(median_val, color="red", linestyle="--", label="Median")
    plt.axhline(q1_val, color="orange", linestyle="--", label="Q1 (25th %ile)")
    plt.axhline(q3_val, color="green", linestyle="--", label="Q3 (75th %ile)")
    plt.legend()
    # Grid, ticks, and layout
    plt.grid(True)
    plt.xticks(df_feature.index, rotation=90)
    plt.tight_layout()

    # Ensure figure directory exists
    save_dir = Path(config.FIGURE_PATH)
    save_dir.mkdir(parents=True, exist_ok=True)

    # Build full file path, include MA method for close
    feature_tag = feature
    if feature.lower() == "close":
        feature_tag = f"{feature}_{ma_method}"
    save_path = save_dir / f"{config.STOCK_TICKER}_daily_{feature_tag}_{daily_date_range}.png"
    # Apply final title and save
    plt.title(title)
    plt.savefig(save_path, bbox_inches="tight", pad_inches=0.2)
    
    if show:
        plt.show()
    else:
        plt.close()
    

def daily_data_rvol_viz(volume_df: pd.DataFrame, lookback: int, *, method: str = None, show = config.SHOW_PLOTS):
    """
    Visualizes the Relative Volume (RVOL) from a given volume DataFrame.

    Parameters:
    - volume_df (pd.DataFrame): DataFrame containing the volume and RVOL values indexed by date.
    - lookback (int): Number of days to look back for computing the feature.
    """
    
    daily_date_range = volume_df.shape[0]

    # Match the same figure size and font settings as other daily plots
    plt.figure(figsize=config.FIG_SIZE)
    plt.plot(volume_df.index, volume_df["rvol"], label="RVOL", marker="o")
    method = (method or getattr(config, "DAILY_RVOL_METHOD", "ema")).lower()
    plt.title(
        f"{config.STOCK_TICKER} RVOL ({method.upper()}) {daily_date_range} day range - {lookback}-day lookback \n"
        f"from {volume_df.index.min().date()} to {volume_df.index.max().date()}"
    )
    ## median and quartiles
    median_rvol = volume_df["rvol"].median()
    q1_rvol = volume_df["rvol"].quantile(0.25)
    q3_rvol = volume_df["rvol"].quantile(0.75)
    plt.axhline(median_rvol, color="red", linestyle="--", label="Median")
    plt.axhline(q1_rvol, color="orange", linestyle="--", label="Q1 (25th %ile)")
    plt.axhline(q3_rvol, color="green", linestyle="--", label="Q3 (75th %ile)")
    plt.xticks(volume_df.index, rotation=90)
    plt.xlabel("Date")
    plt.ylabel("RVOL")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    save_path = Path(config.FIGURE_PATH)
    save_path.mkdir(parents=True, exist_ok=True)
    plt.savefig(
        save_path / f"{config.STOCK_TICKER}_daily_rvol_{method}_{daily_date_range}.png",
        bbox_inches="tight",
        pad_inches=0.2,
    )
   
    if show:
        plt.show()
    else:
        plt.close()


def daily_data_atr_viz(atr_df: pd.DataFrame, lookback: int, *, method: str = "wilder", show = config.SHOW_PLOTS):
    """
    Visualizes the Average True Range (ATR) from a given ATR series.

    Parameters:
    - atr_series (pd.Series): Series containing the ATR values indexed by date.
    - title (str, optional): Custom title for the plot.

    """
    daily_date_range = atr_df.shape[0]

    plt.figure(figsize=config.FIG_SIZE)
    plt.plot(atr_df.index, atr_df, label=f"ATR (n={lookback})", marker="o")
    ## median and quartiles
    median_atr = atr_df.median()
    q1_atr = atr_df.quantile(0.25)
    q3_atr = atr_df.quantile(0.75)
    plt.axhline(median_atr, color="red", linestyle="--", label="Median")
    plt.axhline(q1_atr, color="orange", linestyle="--", label="Q1 (25th %ile)")
    plt.axhline(q3_atr, color="green", linestyle="--", label="Q3 (75th %ile)")
    
    m = method.lower()
    m_disp = "WILD" if m in ("wilder", "wild", "w") else m.upper()
    plt.title(
        f"{config.STOCK_TICKER} ATR ({m_disp}) {daily_date_range} day range with {lookback}-day lookback \n"
        f"from {atr_df.index.min().date()} to {atr_df.index.max().date()}"
    )
    plt.xlabel("Date")
    plt.ylabel("ATR (price units)")
    plt.grid(True)
    plt.legend()
    plt.xticks(atr_df.index, rotation=90)
    plt.tight_layout()
    
    save_path = Path(config.FIGURE_PATH)
    save_path.mkdir(parents=True, exist_ok=True)
    plt.savefig(
        save_path / f"{config.STOCK_TICKER}_daily_atr_{m}_{daily_date_range}.png",
        bbox_inches="tight",
        pad_inches=0.2,
    )
    
    if show:
        plt.show()
    else:
        plt.close()
