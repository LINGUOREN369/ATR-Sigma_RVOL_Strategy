import pandas as pd
import matplotlib.pyplot as plt
import config
import matplotlib.ticker as mtick
from pathlib import Path


def daily_data_feature_viz(df_feature: pd.DataFrame, feature: str, show = config.SHOW_PLOTS):
    """
    Visualizes a specified feature from daily data with a given lookback period.

    Parameters:
    - df_feature (pd.DataFrame): DataFrame containing the feature to visualize.
    - feature (str): The feature/column name to visualize.
    """
    daily_date_range = df_feature.shape[0]
    plt.figure(figsize=config.FIG_SIZE)
    plt.plot(df_feature.index, df_feature[feature], marker="o")
    plt.title(
        (
            f"{config.STOCK_TICKER} Daily {feature.capitalize()} "
            f"with {daily_date_range}-Day Range \n from {df_feature.index.min().date()} "
            f"to {df_feature.index.max().date()}"
        )
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

    # Build full file path
    save_path = save_dir / f"{config.STOCK_TICKER}_daily_{feature}_{daily_date_range}.png"

    plt.savefig(save_path)
    
    if show:
        plt.show()
    else:
        plt.close()
    

def daily_data_rvol_viz(volume_df: pd.DataFrame, lookback: int, show = config.SHOW_PLOTS):
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
    plt.title(
        f"{config.STOCK_TICKER} RVOL {daily_date_range} day range - {lookback}-day lookback \n"
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
    plt.savefig(save_path / f"{config.STOCK_TICKER}_daily_rvol_{daily_date_range}.png")
   
    if show:
        plt.show()
    else:
        plt.close()


def daily_data_atr_viz(atr_df: pd.DataFrame, lookback: int, show = config.SHOW_PLOTS):
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
    
    plt.title(f"{config.STOCK_TICKER} ATR {daily_date_range} day range with {lookback}-day lookback \n from {atr_df.index.min().date()} to {atr_df.index.max().date()}")
    plt.xlabel("Date")
    plt.ylabel("ATR (price units)")
    plt.grid(True)
    plt.legend()
    plt.xticks(atr_df.index, rotation=90)
    plt.tight_layout()
    
    save_path = Path(config.FIGURE_PATH)
    save_path.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path / f"{config.STOCK_TICKER}_daily_atr_{daily_date_range}.png")
    
    if show:
        plt.show()
    else:
        plt.close()
