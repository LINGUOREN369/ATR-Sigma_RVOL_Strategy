# ATR‑Sigma RVOL Strategy

A modular Python toolkit to compute and visualize daily ATR and (daily/intraday) RVOL, then auto‑stitch related charts into composite review images.

---

## Overview

- Bold, opinionated defaults in `config.py` to keep runs reproducible.
- Daily metrics: Close, Volume, RVOL, ATR (Wilder/SMA).
- Intraday metrics: Time‑of‑day averages (close/volume), intraday cumulative RVOL vs expected.
- Image compositor stitches period variants (e.g., 30‑60‑120 days) and intervals.

---

## Install

Option A — conda (recommended):

1) Create env from `environment.yml`
   - `conda env create -f environment.yml`
   - `conda activate capm`

Option B — pip:

- `python -m venv .venv && source .venv/bin/activate`
- `pip install pandas numpy "matplotlib<4" pillow alpha_vantage`

Set your Alpha Vantage API key (for downloads):

- macOS/Linux: `export ALPHA_VANTAGE_API_KEY=YOUR_KEY`
- Windows (Powershell): `$Env:ALPHA_VANTAGE_API_KEY = "YOUR_KEY"`

---

## Configure

Edit `config.py` to control all behavior:

- `STOCK_TICKER`: single symbol to analyze (e.g., `"VOO"`).
- `DOWNLOAD_STOCK_TICKER_LIST`: symbols to fetch to `data/`.
- `INTRADAY_INTERVAL`: intraday interval (`"1min"|"5min"|"15min"|"30min"|"60min"`).
- `OUTPUTSIZE`: Alpha Vantage size (`"compact"|"full"`).
- `FIGURE_PATH`: folder for per‑chart PNGs (default `./stock_image/<TICKER>/`).
- `REPORT_PATH`: folder for stitched composites (default `./stock_report/<TICKER>/`).
- `DAILY_DATE_RANGE`: list of daily windows to render (e.g., `[30, 60, 120]`).
- `DAILY_ROLLING_WINDOW`: RVOL lookback (days).
- `ATR_DAILY_ROLLING_WINDOW`: ATR lookback (days; Wilder or SMA in code).
- `INTRADAY_FILEPATH`: path to intraday CSV for the analysis ticker.
- `INTRADAY_ROLLING_WINDOW`: list of lookbacks for intraday features (days).
- `SHOW_N_DAYS`: number of recent days for the intraday RVOL heatmap.
- `SHOW_PLOTS`: show matplotlib windows (headless default is `False`).

---

## Data Fetching

The downloader saves CSVs to `data/` using Alpha Vantage:

- Intraday: `data/<TICKER>_<INTERVAL>.csv`
- Daily: `data/<TICKER>_daily.csv`

Run the bulk fetcher for your list in `config.py`:

```bash
python -m src.download_data
```

Notes:

- Ensure `ALPHA_VANTAGE_API_KEY` is set in your environment.
- Create the `data/` folder if it doesn’t exist yet.
- You may also load your own CSVs; see the expected columns in `src/intraday_handler.py` and `src/daily_handler.py`.

---

## Run The Pipeline

Generates daily and intraday charts, then stitches composites:

```bash
python -m src.test
```

Output locations:

- Individual charts → `FIGURE_PATH`
- Stitched composites → `REPORT_PATH`

---

## What Gets Produced

Daily charts (examples for `VOO`):

- `VOO_daily_close_30.png`, `VOO_daily_close_60.png`, `VOO_daily_close_120.png`
- `VOO_daily_volume_30.png`, `VOO_daily_volume_60.png`, `VOO_daily_volume_120.png`
- `VOO_daily_rvol_30.png`, `VOO_daily_rvol_60.png`, `VOO_daily_rvol_120.png`
- `VOO_daily_atr_30.png`, `VOO_daily_atr_60.png`, `VOO_daily_atr_120.png`

Intraday charts (interval aware):

- Averages (close/volume): `VOO_intraday_60min_average_close_10_days_look_back.png`
- RVOL heatmap: `VOO_intraday_60min_rvol_last_5_days_with_20_day_lookback.png`

Composites saved to `REPORT_PATH` by `src/image_stack_patch.py`:

- Daily family: `VOO_daily_close_30-60-120.png`
- Intraday averages family: `VOO_intraday_60min_average_close_5-10-20.png`
- Intraday RVOL family: `VOO_intraday_60min_rvol_last_5_days_with_lookback_5-10-20.png`

---

## Project Structure

- `config.py`: Central settings and paths.
- `src/download_data.py`: Pulls daily and intraday data to `data/` via Alpha Vantage.
- `src/daily_handler.py`: Cleans daily data; computes RVOL and ATR.
- `src/daily_viz.py`: Renders daily charts to `FIGURE_PATH`.
- `src/intraday_handler.py`: Prepares intraday features and expected cumulative volume.
- `src/intraday_viz.py`: Renders intraday averages and RVOL heatmaps.
- `src/image_stack_patch.py`: Auto‑discovers PNGs and stitches composites.
- `playground/*.ipynb`: Notebooks for exploration and one‑off checks.

---

## Tips & Troubleshooting

- Timezones: intraday timestamps are normalized to New York time in `intraday_read_csv_correct_time`.
- Missing folders: create `data/`, `stock_image/`, and `stock_report/` as needed; the code creates subfolders per ticker.
- API limits: Alpha Vantage is rate‑limited; consider waiting between runs or using your own cached CSVs.
- Large numpy/pandas versions: if you hit binary issues, use the provided `environment.yml`.

---

## License

MIT License. See `LICENSE` for details.
