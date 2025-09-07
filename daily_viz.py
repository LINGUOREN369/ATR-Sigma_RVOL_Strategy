import pandas as pd
import matplotlib.pyplot as plt
import config
import matplotlib.ticker as mtick


def daily_data_feature_viz(df_feature: pd.DataFrame, feature: str):
    """
    Visualizes a specified feature from daily data with a given lookback period.

    Parameters:
    - df_feature (pd.DataFrame): DataFrame containing the feature to visualize.
    - feature (str): The feature/column name to visualize.
    """
    daily_date_range = df_feature.shape[0]
    plt.figure(figsize=(20, 10))
    plt.plot(df_feature.index, df_feature[feature], marker="o")
    plt.title(
        (
            f"{config.stock_ticker} Daily {feature.capitalize()} "
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

    # Grid, ticks, and layout
    plt.grid(True)
    plt.xticks(df_feature.index, rotation=45)
    plt.tight_layout()

    # Save and show
    plt.savefig(config.FIGURE_PATH + f"{config.stock_ticker}_daily_{feature}.png")
    plt.show()
    

def daily_data_rvol_viz(volume_df: pd.DataFrame, lookback: int):
    """
    Visualizes the Relative Volume (RVOL) from a given volume DataFrame.

    Parameters:
    - volume_df (pd.DataFrame): DataFrame containing the volume and RVOL values indexed by date.
    - lookback (int): Number of days to look back for computing the feature.
    """
    plt.figure(figsize=(20, 10))
    plt.plot(volume_df.index, volume_df["rvol"], label="RVOL")
    for x, y in zip(volume_df.index, volume_df["rvol"]):
        plt.text(
            x, y, 
            f"{y:.2f}",  # format to 2 decimals
            ha="center", va="bottom", fontsize=8
        )
    plt.title(f"{config.stock_ticker} RVOL {config.daily_date_range} day range - {lookback}-day lookback \n from {volume_df.index.min().date()} to {volume_df.index.max().date()}")
    plt.xticks(volume_df.index, rotation=45)
    plt.xlabel("Date")
    plt.ylabel("RVOL")
    plt.legend()
    plt.grid(True)
    plt.savefig(config.FIGURE_PATH + f"{config.stock_ticker}_daily_rvol.png")
    plt.tight_layout()
    plt.show()
    


def daily_data_atr_viz(atr_df: pd.DataFrame, lookback: int):
    """
    Visualizes the Average True Range (ATR) from a given ATR series.

    Parameters:
    - atr_series (pd.Series): Series containing the ATR values indexed by date.
    - title (str, optional): Custom title for the plot.

    """
    plt.figure(figsize=(20, 10))
    plt.plot(atr_df.index, atr_df, label=f"ATR (n={lookback})")
    plt.title(f"{config.stock_ticker} ATR {config.daily_date_range} day range with {lookback}-day lookback \n from {atr_df.index.min().date()} to {atr_df.index.max().date()}")
    plt.xlabel("Date")
    plt.ylabel("ATR (price units)")
    plt.grid(True)
    plt.legend()
    plt.xticks(atr_df.index, rotation=45)
    plt.tight_layout()
    plt.savefig(config.FIGURE_PATH + f"{config.stock_ticker}_daily_atr.png")
    plt.show()