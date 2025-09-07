import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.ticker as mtick

from pathlib import Path
import config


def intraday_feature_trend_viz(avg_feature_sorted):
    """
    Visualize the trend of a specific feature by time of day over a look-back period.
    Param: avg_feature_sorted - a pandas Series with the average feature values sorted by time of day
    The df is generated through function in intraday_handler.py 
    """
    plt.figure(figsize=(12, 6))
    times = [str(t) for t in avg_feature_sorted.index]
    plt.plot(times, avg_feature_sorted.values, marker='o')
    
    ax = plt.gca()
    if avg_feature_sorted.name.lower() == "average volume":
        # # Option A: show commas
        # ax.ticklabel_format(style="plain", axis="y")
        # ax.yaxis.set_major_formatter(
        #     mtick.FuncFormatter(lambda x, _: f"{int(x):,}")
        # )
        # Option B: show in millions (uncomment if preferred)
        ax.yaxis.set_major_formatter(
            mtick.FuncFormatter(lambda x, _: f"{x/1e6:.1f}M")
        )
        
    plt.title(f'Intraday {avg_feature_sorted.name} Trend with {config.intraday_rolling_window} Days Rolling Window')
    plt.xticks(rotation=45)
    plt.xlabel("Time of Day")
    plt.ylabel("Average Feature Value")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(Path(config.FIGURE_PATH) / f"{config.stock_ticker}_intraday_{avg_feature_sorted.name.replace(' ', '_').lower()}_trend.png")
    plt.show()



def intraday_rvol_viz(rvol_df, last_n_days=10):
    df = rvol_df.copy()
    df["Date"] = df.index.date
    df["Hour"] = df.index.hour

    # Get only the last n unique dates
    unique_dates = sorted(df["Date"].unique())[-last_n_days:]

    # Restrict dataframe
    df = df[df["Date"].isin(unique_dates)]

    # Rebuild colormap based only on these dates
    norm = mcolors.Normalize(vmin=0, vmax=len(unique_dates)-1)
    cmap = cm.get_cmap("viridis_r")

    plt.figure(figsize=(20, 10))
    for i, (date, group) in enumerate(sorted(df.groupby("Date"))):
        color = cmap(norm(i))  # darker for later dates
        plt.plot(group["Hour"], group["Intraday_RVOL_cum"],
                 label=str(date), color=color)

    plt.xlabel("Hour of Day")
    plt.ylabel("Intraday RVOL Cumulative")
    plt.title(f"Intraday Relative Volume (Cumulative) — last {last_n_days} days")
    plt.legend()
    plt.grid(True)
    plt.savefig(Path(config.FIGURE_PATH) / f"{config.stock_ticker}_intraday_rvol_cumulative_last_{last_n_days}_days.png")
    plt.show()