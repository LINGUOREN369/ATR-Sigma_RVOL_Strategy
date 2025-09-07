import pandas as pd
import matplotlib.pyplot as plt
import config


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
    plt.title(f"Daily {feature.capitalize()} with {daily_date_range}-Day Lookback \n from {df_feature.index.min().date()} to {df_feature.index.max().date()}")
    plt.xlabel("Date")
    plt.ylabel(feature.capitalize())
    plt.grid(True)
    plt.xticks(df_feature.index, rotation=45)  # rotate labels, let matplotlib auto-select ticks
    plt.tight_layout()
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
    plt.title("Relative Volume (RVOL) Over Time with Lookback of " + str(lookback) + " Days \n from " + str(volume_df.index.min().date()) + " to " + str(volume_df.index.max().date()))
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
    ttl = f"Average True Range — {lookback}-period"
    start = pd.to_datetime(atr_df.index.min()).date() if len(atr_df) else ""
    end   = pd.to_datetime(atr_df.index.max()).date() if len(atr_df) else ""
    plt.title(f"{ttl}\n{start} to {end}")
    plt.xlabel("Date")
    plt.ylabel("ATR (price units)")
    plt.grid(True)
    plt.legend()
    plt.xticks(atr_df.index, rotation=45)
    plt.tight_layout()
    plt.savefig(config.FIGURE_PATH + f"{config.stock_ticker}_daily_atr.png")
    plt.show()