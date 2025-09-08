import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.ticker as mtick

from pathlib import Path
import config


def intraday_feature_trend_viz(avg_feature_sorted, show = config.SHOW_PLOTS):
    """
    Visualize the trend of a specific feature by time of day over a look-back period.
    Param: avg_feature_sorted - a pandas Series with the average feature values sorted by time of day
    The df is generated through function in intraday_handler.py 
    """
    plt.figure(figsize=config.FIG_SIZE)
    times = [str(t) for t in avg_feature_sorted.index]
    plt.plot(times, avg_feature_sorted.values, marker='o')
    
    ax = plt.gca()
    if "volume" in avg_feature_sorted.name.lower():
        # # Option A: show commas
        # ax.ticklabel_format(style="plain", axis="y")
        # ax.yaxis.set_major_formatter(
        #     mtick.FuncFormatter(lambda x, _: f"{int(x):,}")
        # )
        # Option B: show in millions (uncomment if preferred)
        ax.yaxis.set_major_formatter(
            mtick.FuncFormatter(lambda x, _: f"{x/1e6:.1f}M")
        )
    
    plt.title(f"{config.STOCK_TICKER} Intraday {avg_feature_sorted.name} Trend")
    plt.xticks(rotation=45)
    plt.xlabel("Time of Day")
    plt.ylabel("Average Feature Value")
    plt.grid(True)
    plt.tight_layout()
    save_path = Path(config.FIGURE_PATH)
    save_path.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path / f"{config.STOCK_TICKER}_intraday_{avg_feature_sorted.name.replace(' ', '_').lower()}.png")

    if show:
        plt.show()
    else:
        plt.close()


def intraday_rvol_viz(rvol_df, look_back_period, show_n_days=10, show=config.SHOW_PLOTS):
    df = rvol_df.copy()
    df["Date"] = df.index.date
    df["Hour"] = df.index.hour

    # Get only the last n unique dates
    unique_dates = sorted(df["Date"].unique())[-show_n_days:]

    # Restrict dataframe
    df = df[df["Date"].isin(unique_dates)]

    # Rebuild colormap based only on these dates
    norm = mcolors.Normalize(vmin=0, vmax=len(unique_dates)-1)
    cmap = cm.get_cmap("viridis_r")

    plt.figure(figsize=config.FIG_SIZE)
    for i, (date, group) in enumerate(sorted(df.groupby("Date"))):
        color = cmap(norm(i))  # darker for later dates
        plt.plot(group["Hour"], group[f"Intraday_RVOL_{look_back_period}"], marker='o', mfc=color,
                 label=str(date), color=color)

    plt.xlabel("Hour of Day")
    plt.ylabel("Intraday RVOL Cumulative")
    plt.title(f"{config.STOCK_TICKER} - Intraday Relative Volume — last {show_n_days} days with {look_back_period}-day look-back")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    save_path = Path(config.FIGURE_PATH)
    save_path.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path / f"{config.STOCK_TICKER}_intraday_rvol_last_{show_n_days}_days_with_{look_back_period}_day_lookback.png")

    if show:
        plt.show()
    else:
        plt.close()