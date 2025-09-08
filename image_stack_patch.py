# stitch_daily_periods_vertical.py
from pathlib import Path
import re
from PIL import Image
import config

TICKER = getattr(config, "STOCK_TICKER", "VOO")
FIG_DIR = Path(getattr(config, "FIGURE_PATH", "./stock_image/"))

# ---------- PATTERNS ----------
# Daily: VOO_daily_close_30.png
DAILY_PATTERN = re.compile(
    rf"^{re.escape(TICKER)}_(?P<base>daily_[a-z0-9_]+)_(?P<period>\d+)\.png$",
    re.IGNORECASE,
)

# Intraday (averages):
#   VOO_intraday_average_close_5_days_look_back.png
#   VOO_intraday_average_volume_20_days_look_back.png
INTRA_AVG_PATTERN = re.compile(
    rf"^{re.escape(TICKER)}_(?P<base>intraday_average_(?:close|volume))_(?P<period>\d+)_days_look_back\.png$",
    re.IGNORECASE,
)

# Intraday (RVOL):
#   VOO_intraday_rvol_last_10_days_with_5_day_lookback.png
#   VOO_intraday_rvol_last_10_days_with_10_day_lookback.png
#   VOO_intraday_rvol_last_10_days_with_20_day_lookback.png
INTRA_RVOL_PATTERN = re.compile(
    rf"^{re.escape(TICKER)}_intraday_rvol_last_(?P<show>\d+)_days_with_(?P<period>\d+)_day_lookback\.png$",
    re.IGNORECASE,
)

def discover_daily_images():
    """Return { base -> { period:int -> Path } } for daily images."""
    groups = {}
    for p in FIG_DIR.glob("*.png"):
        m = DAILY_PATTERN.match(p.name)
        if not m:
            continue
        base = m.group("base").lower()              # e.g., daily_close
        period = int(m.group("period"))             # e.g., 30
        groups.setdefault(base, {})[period] = p
    return groups

def discover_intraday_images():
    """
    Return { base -> { period:int -> Path } } for intraday images.

    Groups two families:
      1) intraday_average_(close|volume)_{period}_days_look_back.png
         base key = 'intraday_average_close' or 'intraday_average_volume'
         period   = 5 / 10 / 20 (days look-back)

      2) intraday_rvol_last_{show}_days_with_{period}_day_lookback.png
         base key = f"intraday_rvol_last_{show}_days_with_lookback"
         period   = 5 / 10 / 20 (look-back)
    """
    groups = {}
    for p in FIG_DIR.glob("*.png"):
        name = p.name

        m1 = INTRA_AVG_PATTERN.match(name)
        if m1:
            base = m1.group("base").lower()         # intraday_average_close / volume
            period = int(m1.group("period"))        # 5 / 10 / 20
            groups.setdefault(base, {})[period] = p
            continue

        m2 = INTRA_RVOL_PATTERN.match(name)
        if m2:
            show_n = int(m2.group("show"))          # e.g., 10
            period = int(m2.group("period"))        # 5 / 10 / 20
            base = f"intraday_rvol_last_{show_n}_days_with_lookback"
            groups.setdefault(base, {})[period] = p
            continue

    return groups

def stitch_vertical(paths):
    """Stack images vertically; resize to same width for alignment."""
    imgs = [Image.open(p) for p in paths]
    min_w = min(im.width for im in imgs)
    resized = []
    for im in imgs:
        if im.width != min_w:
            new_h = int(im.height * (min_w / im.width))
            im = im.resize((min_w, new_h), Image.BICUBIC)
        resized.append(im)
    total_h = sum(im.height for im in resized)
    out = Image.new("RGB", (min_w, total_h), "white")
    y = 0
    for im in resized:
        out.paste(im, (0, y))
        y += im.height
    return out



def patch_images():
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # Collect both daily and intraday groups
    groups = discover_daily_images()
    intra_groups = discover_intraday_images()
    for k, v in intra_groups.items():
        groups[k] = v

    if not groups:
        print("No matching daily or intraday images found.")
        return

    # Stitch each base (e.g., daily_close, intraday_average_close, intraday_rvol_last_10_days_with_lookback)
    for base, period_map in groups.items():
        periods = sorted(period_map.keys())
        if len(periods) < 2:
            continue  # need at least two periods to stack
        paths = [period_map[p] for p in periods]
        combined = stitch_vertical(paths)
        suffix = "-".join(str(p) for p in periods)
        out_name = f"{TICKER}_{base}_{suffix}.png"
        save_path = Path(getattr(config, "REPORT_PATH", f"./report/{TICKER}/"))
        save_path.mkdir(parents=True, exist_ok=True)
        out_path = save_path / out_name
        combined.save(out_path)
        print(f"✔ Saved {out_path}")
