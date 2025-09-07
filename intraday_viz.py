import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors

from pathlib import Path
import config


def intraday_feature_trend_viz(avg_feature_sorted):
    """
    Visualize the trend of a specific feature by time of day over a look-back period.
    Param: avg_feature_sorted - a pandas Series with the average feature values sorted by time of day
    The df is generated through function in intraday_handler.py 
    """
    plt.figure(figsize=(12, 6))

    # Use actual dates as legend labels
    day_labels = [str(d) for d in tail_block.index]

    for i, (d, row) in enumerate(tail_block.iterrows()):
        y = row.iloc[order].values
        # label every day (could be noisy; feel free to thin this)
        plt.plot(tick_labels, y, alpha=0.18, linewidth=1, label=day_labels[i])

    # Plot the average line on top
    plt.plot(tick_labels, avg_sorted.values, linewidth=2,
                label=f"Average {feature} by time (last {look_back_days} days)")

    # Nice title/date range from the same slice you plotted
    start_date = tail_block.index.min()
    end_date = tail_block.index.max()
    plt.title(
        f"{feature.capitalize()} by Time of Day (last {look_back_days} days)\n"
        f"{start_date} → {end_date}"
    )
    plt.xlabel("Time of Day")
    plt.ylabel(feature)
    plt.xticks(tick_labels, rotation=90)
    plt.grid(True)
    plt.legend(ncol=2)  # adjust as you like
    plt.tight_layout()

    # Ensure folder exists and save
    Path("stock_image").mkdir(parents=True, exist_ok=True)
    out_path = (
        f"stock_image/Average_{feature}_by_Time_of_Day_over_{look_back_days}_days_"
        f"from_{start_date}_to_{end_date}.png"
    )
    plt.savefig(out_path, bbox_inches="tight", dpi=300)
    # plt.show()  # enable if you want to display interactively



def intraday_rvol_viz(rvol_df):
    df = rvol_df.copy()
    df["Date"] = df.index.date
    df["Hour"] = df.index.hour
    
    # Sort unique dates so earliest → lightest, latest → darkest
    unique_dates = sorted(df["Date"].unique())
    norm = mcolors.Normalize(vmin=0, vmax=len(unique_dates)-1)
    cmap = cm.get_cmap("viridis_r")  # you can try "plasma", "cividis", etc.
    
    plt.figure(figsize=(20, 10))
    for i, (date, group) in enumerate(df.groupby("Date")):
        color = cmap(norm(i))  # darker for later dates
        plt.plot(group["Hour"], group["Intraday_RVOL_cum"], 
                 label=str(date), color=color)
    
    plt.xlabel("Hour of Day")
    plt.ylabel("Intraday RVOL Cumulative")
    plt.title("Intraday Relative Volume (Cumulative) by Hour")
    plt.legend()
    plt.grid(True)
    plt.show()