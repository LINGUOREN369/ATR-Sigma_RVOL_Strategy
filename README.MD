# ATR‑Sigma RVOL Strategy

A modular Python toolkit to compute and visualize daily ATR and (daily/intraday) RVOL, then auto‑stitch related charts into composite review images.

---

## Overview

- Bold, opinionated defaults in `config.py` to keep runs reproducible.
- Daily metrics: Close (with Bollinger Bands, SMA/EMA), Volume, RVOL, ATR (Wilder/SMA).
- Intraday metrics: Time‑of‑day averages (close/volume), intraday cumulative RVOL vs expected.
- Image compositor stitches: daily by time range (Close → Volume → RVOL → ATR), and intraday period/interval variants.

---

## Install

Option A — conda (recommended):

1) Create env from `environment.yml`
   - `conda env create -f environment.yml`
   - `conda activate atr_sigma`

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
- `DOWNLOAD_STOCK_TICKER_LIST`: symbols to fetch to `DATA_PATH`.
- `INTRADAY_INTERVAL`: intraday interval (`"1min"|"5min"|"15min"|"30min"|"60min"`).
- `OUTPUTSIZE`: Alpha Vantage size (`"compact"|"full"`).
- `DATA_PATH`: base directory for downloaded CSVs (default `/Users/linguoren/Documents/Market_Research/stock_data`).
- `FIGURE_PATH`: folder for per‑chart PNGs (default `./stock_image/<TICKER>/`).
- `REPORT_PATH`: folder for stitched composites (default `/Users/linguoren/Documents/Market_Research/stock_report/<TICKER>/`).
- `DAILY_DATE_RANGE`: list of daily windows to render (e.g., `[30, 60, 120]`).
- `DAILY_ROLLING_WINDOW`: RVOL lookback (days).
- `ATR_DAILY_ROLLING_WINDOW`: ATR lookback (days; Wilder or SMA in code).
- `ATR_METHOD`: `"wilder"` or `"sma"`. Method is included in ATR chart titles and filenames.
- `BOLLINGER_WINDOW`, `BOLLINGER_NUM_STD`: Bollinger Bands settings for daily Close. Bands are computed on full history and then aligned to each window (30/60/120) so they are present from the first day of the window.
- `BOLLINGER_MA_METHOD`: `"sma"` or `"ema"` for the Bollinger moving average. The method is also reflected in the Close chart filename and title.
- `DAILY_RVOL_METHOD`: `"ema"` or `"sma"` for the daily RVOL average (denominator). The method is reflected in the RVOL chart filename and title.
- `INTRADAY_FILEPATH`: path to intraday CSV for the analysis ticker.
- `INTRADAY_ROLLING_WINDOW`: list of lookbacks for intraday features (days).
- `SHOW_N_DAYS`: number of recent days for the intraday RVOL heatmap.
- `SHOW_PLOTS`: show matplotlib windows (headless default is `False`).
- `INTRADAY_AVG_METHOD`: `"ema"` or `"sma"` for intraday time-of-day averages (close/volume). Reflected in the title and filename.
- `INTRADAY_RVOL_METHOD`: `"ema"` or `"sma"` for the expected cumulative volume used in intraday RVOL. Reflected in the title and filename.

---

## Data Fetching

The downloader saves CSVs to `DATA_PATH` using Alpha Vantage (default `/Users/linguoren/Documents/Market_Research/stock_data`):

- Intraday: `<DATA_PATH>/<TICKER>_<INTERVAL>.csv`
- Daily: `<DATA_PATH>/<TICKER>_daily.csv`

Run the bulk fetcher for your list in `config.py`:

```bash
python -m src.download_data
```

Notes:

- Ensure `ALPHA_VANTAGE_API_KEY` is set in your environment.
- The folder is created automatically if missing.
- You may also load your own CSVs; see the expected columns in `src/intraday_handler.py` and `src/daily_handler.py`.

---

## Run The Pipeline

Generates daily and intraday charts, then stitches composites:

```bash
python -m src.run
```

Output locations:

- Individual charts → `FIGURE_PATH` (default `./stock_image/<TICKER>/`)
- Stitched composites → `REPORT_PATH` (default `/Users/linguoren/Documents/Market_Research/stock_report/<TICKER>/`)

### Default report location and how to change it

- Default: On this machine, stitched reports are saved under `/Users/linguoren/Documents/Market_Research/stock_report/<TICKER>/` (inside the `Documents` folder of user `linguoren`).
- Change it for a single run (recommended for quick tests):

  ```bash
  python -m src.run --report-base ~/Documents/my_stock_reports
  ```

- Change it permanently (edit config): open `config.py` and set a new base folder. `REPORT_PATH` will automatically append the ticker subfolder for you.

  ```python
  # config.py
  REPORT_BASE_PATH = Path("/path/you/prefer/stock_report")
  # REPORT_PATH is derived as: REPORT_BASE_PATH / STOCK_TICKER
  ```

- Tip: You can also redirect where individual charts are saved with `--figure-base` (or `FIGURE_BASE_PATH` in `config.py`).

Override settings per run without editing `config.py`:

```bash
python -m src.run --ticker CRCL
# Additional examples
python -m src.run --ticker VOO --data-path ~/custom_data --report-base ~/reports
```

---

## What Gets Produced

Daily charts (examples for `VOO`):

- `VOO_daily_close_sma_30.png`, `VOO_daily_close_sma_60.png`, `VOO_daily_close_sma_120.png` (suffix reflects Bollinger MA method)
- `VOO_daily_volume_30.png`, `VOO_daily_volume_60.png`, `VOO_daily_volume_120.png`
- `VOO_daily_rvol_ema_30.png`, `VOO_daily_rvol_ema_60.png`, `VOO_daily_rvol_ema_120.png` (suffix reflects RVOL average method)
- `VOO_daily_atr_wilder_30.png`, `VOO_daily_atr_wilder_60.png`, `VOO_daily_atr_wilder_120.png` (suffix reflects ATR method; title shows WILD or SMA)

Intraday charts (interval aware):

- Averages (close/volume): `VOO_intraday_60min_average_close_10_days_look_back_ema.png` (suffix reflects average method)
- RVOL heatmap: `VOO_intraday_60min_rvol_last_5_days_with_20_day_lookback_ema.png` (suffix reflects expected-curve method)

Composites saved to `REPORT_PATH` by `src/image_stack_patch.py`:

- Daily (by period, ordered Close → Volume → RVOL → ATR):
  `VOO_daily_30_close-volume-rvol-atr.png`, `VOO_daily_60_close-volume-rvol-atr.png`, `VOO_daily_120_close-volume-rvol-atr.png`
- Intraday averages family: `VOO_intraday_60min_average_close_5-10-20.png`
- Intraday RVOL family: `VOO_intraday_60min_rvol_last_5_days_with_lookback_5-10-20.png`

Manual patching only (optional):

```bash
python -c "from src.image_stack_patch import patch_images; patch_images()"
```

---

## Project Structure

- `config.py`: Central settings and paths.
- `src/download_data.py`: Pulls daily and intraday data to `DATA_PATH` via Alpha Vantage.
- `src/daily_handler.py`: Cleans daily data; computes RVOL and ATR.
- `src/daily_viz.py`: Renders daily charts to `FIGURE_PATH`.
- `src/intraday_handler.py`: Prepares intraday features and expected cumulative volume.
- `src/intraday_viz.py`: Renders intraday averages and RVOL heatmaps.
- `src/image_stack_patch.py`: Auto‑discovers PNGs and stitches composites.
- `src/cli.py`: Shared CLI parser + config override helpers.
- `playground/*.ipynb`: Notebooks for exploration and one‑off checks.

---

## Tips & Troubleshooting

- Timezones: intraday timestamps are normalized to New York time in `intraday_read_csv_correct_time`.
- Missing folders: ensure the directories referenced by `DATA_PATH`, `FIGURE_PATH`, and `REPORT_PATH` exist; the code will create subfolders per ticker on demand.
- API limits: Alpha Vantage is rate‑limited; consider waiting between runs or using your own cached CSVs.
- Large numpy/pandas versions: if you hit binary issues, use the provided `environment.yml`.

---

## License

MIT License. See `LICENSE` for details.
