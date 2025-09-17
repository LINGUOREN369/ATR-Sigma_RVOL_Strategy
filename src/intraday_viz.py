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
    plt.xticks(rotation=90)
    plt.xlabel("Time of Day")
    plt.ylabel("Average Feature Value")
    plt.grid(True)
    plt.tight_layout()
    save_path = Path(config.FIGURE_PATH)
    save_path.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path / f"{config.STOCK_TICKER}_intraday_{config.INTRADAY_INTERVAL}_{avg_feature_sorted.name.replace(' ', '_').lower()}.png")

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
    # Create pivot table for heatmap
    pivot_df = df.pivot(index="Hour", columns="Date", values=f"Intraday_RVOL_{look_back_period}")
    # Use a slightly shorter figure height so composites remain readable
    fig_size = getattr(config, "INTRADAY_RVOL_FIG_SIZE", config.FIG_SIZE)
    plt.figure(figsize=fig_size)
    im = plt.imshow(pivot_df.T, aspect='auto', cmap="viridis_r", origin='lower')

    plt.colorbar(im, label=f"Intraday RVOL ({look_back_period}-day look-back)")
    plt.xticks(ticks=np.arange(len(pivot_df.index)), labels=pivot_df.index)
    plt.yticks(ticks=np.arange(len(pivot_df.columns)), labels=[str(d) for d in pivot_df.columns])
    plt.xlabel("Hour of Day")
    plt.ylabel("Date")
    plt.title(f"{config.STOCK_TICKER} - Heatmap of Intraday RVOL — last {show_n_days} days with {look_back_period}-day look-back")
    plt.tight_layout()

    save_path = Path(config.FIGURE_PATH)
    save_path.mkdir(parents=True, exist_ok=True)
    # Save with tight bounding box to avoid clipping tick labels (years)
    plt.savefig(
        save_path / f"{config.STOCK_TICKER}_intraday_{config.INTRADAY_INTERVAL}_rvol_last_{show_n_days}_days_with_{look_back_period}_day_lookback.png",
        bbox_inches="tight",
        pad_inches=0.2,
    )

    if show:
        plt.show()
    else:
        plt.close()
