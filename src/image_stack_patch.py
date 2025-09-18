"""Composite image stacker for daily and intraday charts.

Discovers PNGs under `FIG_DIR` that match known filename patterns and
stitches related images vertically into composite panels saved under
`REPORT_DIR`.

Daily behavior:
- Previously stacked by variable across time ranges (e.g., close 30-60-120).
- Now stacks by time range, combining variables in this top-to-bottom order:
  Close, Volume, RVOL, ATR.
  Output filename is formatted as:
    `<TICKER>_daily_<period>_close-volume-rvol-atr.png`.

Intraday behavior remains unchanged.
"""

from pathlib import Path
from typing import Dict, Iterable, Hashable
import re
from PIL import Image
import config


# ---------- CONFIG SNAPSHOT ----------
TICKER = getattr(config, "STOCK_TICKER", "VOO")
FIG_DIR = Path(getattr(config, "FIGURE_PATH", "./stock_image/"))
REPORT_DIR = Path(getattr(config, "REPORT_PATH", f"./report/{TICKER}/"))


# ---------- PATTERNS ----------
# Daily: VOO_daily_close_30.png
DAILY_PATTERN = re.compile(
    rf"^{re.escape(TICKER)}_(?P<base>daily_[a-z0-9_]+)_(?P<period>\d+)\.png$",
    re.IGNORECASE,
)

# Intraday averages filename variants we accept (backward compatible):
# - Legacy (no interval):
#     VOO_intraday_average_close_5_days_look_back.png
# - Preferred (interval after 'intraday_'):
#     VOO_intraday_30min_average_close_5_days_look_back.png
# - Alternate (interval after ticker):
#     VOO_30min_intraday_average_close_5_days_look_back.png
INTRA_AVG_PATTERN_AFTER_INTRADAY = re.compile(
    rf"^{re.escape(TICKER)}_intraday_(?P<interval>[a-z0-9]+)_average_(?P<atype>close|volume)_(?P<period>\d+)_days_look_back(?:_(?P<method>ema|sma))?\.png$",
    re.IGNORECASE,
)
INTRA_AVG_PATTERN_AFTER_TICKER = re.compile(
    rf"^{re.escape(TICKER)}_(?P<interval>[a-z0-9]+)_intraday_average_(?P<atype>close|volume)_(?P<period>\d+)_days_look_back(?:_(?P<method>ema|sma))?\.png$",
    re.IGNORECASE,
)
INTRA_AVG_PATTERN_LEGACY = re.compile(
    rf"^{re.escape(TICKER)}_intraday_average_(?P<atype>close|volume)_(?P<period>\d+)_days_look_back(?:_(?P<method>ema|sma))?\.png$",
    re.IGNORECASE,
)

# Intraday RVOL:
# - Interval-aware, e.g.: VOO_intraday_5min_rvol_last_10_days_with_20_day_lookback.png
INTRA_RVOL_PATTERN_WITH_INTERVAL = re.compile(
    rf"^{re.escape(TICKER)}_intraday_(?P<interval>[a-z0-9]+)_rvol_last_(?P<show>\d+)_days_with_(?P<period>\d+)_day_lookback(?:_(?P<method>ema|sma))?\.png$",
    re.IGNORECASE,
)
# - Legacy without interval, e.g.: VOO_intraday_rvol_last_10_days_with_20_day_lookback.png
INTRA_RVOL_PATTERN = re.compile(
    rf"^{re.escape(TICKER)}_intraday_rvol_last_(?P<show>\d+)_days_with_(?P<period>\d+)_day_lookback(?:_(?P<method>ema|sma))?\.png$",
    re.IGNORECASE,
)


# ---------- HELPERS ----------
def _interval_sort_key(token: str) -> tuple[int, object]:
    """Sort intervals like '1min','5min','30min','60min' numerically first."""
    m = re.match(r"(\d+)", token)
    return (0, int(m.group(1))) if m else (1, token)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _add(groups: Dict[str, Dict[Hashable, Path]], base: str, key: Hashable, p: Path) -> None:
    groups.setdefault(base, {})[key] = p


def _match_intraday_avg(name: str):
    """Return (interval:str|None, atype:str, period:int) if intraday average; else None."""
    m = INTRA_AVG_PATTERN_AFTER_INTRADAY.match(name)
    if m:
        return m.group("interval").lower(), m.group("atype").lower(), int(m.group("period"))

    m = INTRA_AVG_PATTERN_AFTER_TICKER.match(name)
    if m:
        return m.group("interval").lower(), m.group("atype").lower(), int(m.group("period"))

    m = INTRA_AVG_PATTERN_LEGACY.match(name)
    if m:
        atype = m.group("atype").lower()
        period = int(m.group("period"))
        interval_cfg = getattr(config, "INTRADAY_INTERVAL", None)
        interval = str(interval_cfg).lower() if interval_cfg else None
        return interval, atype, period

    return None


def _match_intraday_rvol(name: str):
    """Return (interval:str|None, show:int, period:int) if intraday RVOL; else None."""
    m = INTRA_RVOL_PATTERN_WITH_INTERVAL.match(name)
    if m:
        return m.group("interval").lower(), int(m.group("show")), int(m.group("period"))

    m = INTRA_RVOL_PATTERN.match(name)
    if m:
        interval_cfg = str(getattr(config, "INTRADAY_INTERVAL", "1min")).lower()
        return interval_cfg, int(m.group("show")), int(m.group("period"))

    return None


# ---------- DISCOVERY ----------
def discover_daily_images() -> Dict[str, Dict[int, Path]]:
    """Return { base -> { period:int -> Path } } for daily images."""
    groups: Dict[str, Dict[int, Path]] = {}
    for p in FIG_DIR.glob("*.png"):
        m = DAILY_PATTERN.match(p.name)
        if not m:
            continue
        base = m.group("base").lower()
        period = int(m.group("period"))
        _add(groups, base, period, p)
    return groups


def discover_daily_images_by_period() -> Dict[int, Dict[str, Path]]:
    """Return { period:int -> { feature:str -> Path } } for daily images.

    Features expected: close, volume, rvol, atr
    """
    by_period: Dict[int, Dict[str, Path]] = {}
    daily = discover_daily_images()
    for base, per_map in daily.items():
        # base like: 'daily_close', 'daily_close_ema', 'daily_volume', 'daily_rvol', 'daily_rvol_ema', 'daily_atr', 'daily_atr_wilder'
        feat_full = base.replace("daily_", "").lower()
        # Normalize to canonical feature key for stacking
        if feat_full.startswith("close"):
            feat_key = "close"
        elif feat_full.startswith("volume"):
            feat_key = "volume"
        elif feat_full.startswith("rvol"):
            feat_key = "rvol"
        elif feat_full.startswith("atr"):
            feat_key = "atr"
        else:
            feat_key = feat_full  # fallback

        for period, p in per_map.items():
            # If multiple variants exist (e.g., close and close_ema), the latter seen wins.
            _add(by_period, period, feat_key, p)
    return by_period


def discover_intraday_images() -> Dict[str, Dict[Hashable, Path]]:
    """
    Group intraday images by logical base and period.

    Returns { base -> { period:int -> Path } }

    Families:
      - Averages: intraday_<interval>_average_(close|volume)_{period}_days_look_back
          base = f"intraday_{interval}_average_{atype}"
          key  = period
      - RVOL: intraday_<interval>_rvol_last_{show}_days_with_{period}_day_lookback
          base = f"intraday_{interval}_rvol_last_{show}_days_with_lookback"
          key  = period
    """
    groups: Dict[str, Dict[Hashable, Path]] = {}
    for p in FIG_DIR.glob("*.png"):
        name = p.name

        avg = _match_intraday_avg(name)
        if avg:
            interval, atype, period = avg
            if interval:
                base = f"intraday_{interval}_average_{atype}"
            else:
                base = f"intraday_average_{atype}"
            _add(groups, base, period, p)
            continue

        rvol = _match_intraday_rvol(name)
        if rvol:
            interval, show_n, period = rvol
            base = f"intraday_{interval}_rvol_last_{show_n}_days_with_lookback"
            _add(groups, base, period, p)
            continue

    return groups


def discover_intraday_images_by_interval() -> Dict[str, Dict[str, Path]]:
    """
    Return { base -> { interval:str -> Path } } to allow stacking ACROSS intervals
    for the same logical parameters.

    Families considered (interval-aware only):
      - Averages: base = f"intraday_average_{atype}_{period}_days_look_back"
      - RVOL:     base = f"intraday_rvol_last_{show}_days_with_{period}_day_lookback"

    Legacy names (no interval) are ignored for cross-interval stacks.
    """
    by_interval: Dict[str, Dict[str, Path]] = {}
    for p in FIG_DIR.glob("*.png"):
        name = p.name

        avg = _match_intraday_avg(name)
        if avg:
            interval, atype, period = avg
            if interval:
                base = f"intraday_average_{atype}_{period}_days_look_back"
                _add(by_interval, base, interval, p)
            continue

        rvol = _match_intraday_rvol(name)
        if rvol:
            interval, show_n, period = rvol
            if interval:
                base = f"intraday_rvol_last_{show_n}_days_with_{period}_day_lookback"
                _add(by_interval, base, interval, p)
            continue

    return by_interval


# ---------- STITCHING ----------
def stitch_vertical(paths: Iterable[Path]) -> Image.Image:
    """Stack images vertically, resizing each to the smallest width for alignment."""
    # First pass: find the minimum width without holding files open
    widths: list[int] = []
    for p in paths:
        with Image.open(p) as im:
            widths.append(im.width)
    min_w = min(widths)

    # Second pass: load resized copies
    resized: list[Image.Image] = []
    for p in paths:
        with Image.open(p) as im:
            if im.width != min_w:
                new_h = int(im.height * (min_w / im.width))
                im = im.resize((min_w, new_h), Image.BICUBIC)
            else:
                im = im.copy()
            resized.append(im.convert("RGB"))

    total_h = sum(im.height for im in resized)
    out = Image.new("RGB", (min_w, total_h), "white")
    y = 0
    for im in resized:
        out.paste(im, (0, y))
        y += im.height

    # Explicitly close intermediates
    for im in resized:
        im.close()
    return out


# ---------- ORCHESTRATION ----------
def patch_images() -> None:
    """Discover related images and write stitched composites to `REPORT_DIR`."""
    _ensure_dir(FIG_DIR)
    _ensure_dir(REPORT_DIR)

    saved_any = False

    # -------- DAILY: stack by time (period), order: Close, Volume, RVOL, ATR --------
    daily_by_period = discover_daily_images_by_period()
    DAILY_FEATURE_ORDER = ["close", "volume", "rvol", "atr"]

    for period in sorted(daily_by_period.keys()):
        fmap = daily_by_period[period]
        ordered_paths = [fmap[f] for f in DAILY_FEATURE_ORDER if f in fmap]
        if len(ordered_paths) < 2:
            continue  # need at least 2 to stack meaningfully
        stitched = stitch_vertical(ordered_paths)
        order_suffix = "-".join(DAILY_FEATURE_ORDER)
        out_name = f"{TICKER}_daily_{period}_{order_suffix}.png"
        out_path = REPORT_DIR / out_name
        stitched.save(out_path)
        saved_any = True
        print(f"✔ Saved {out_path}")

    # -------- INTRADAY: existing behavior (stack by period or across intervals) --------
    # Period-based stacks for intraday families
    intra_groups: Dict[str, Dict[Hashable, Path]] = {}
    for base, mapping in discover_intraday_images().items():
        intra_groups[base] = mapping

    # Across-interval stacks for matching logical bases
    for base, mapping in discover_intraday_images_by_interval().items():
        intra_groups[base] = mapping

    for base, variant_map in intra_groups.items():
        keys = list(variant_map.keys())
        if all(isinstance(k, int) for k in keys):
            ordered = sorted(keys)  # periods
        else:
            ordered = sorted(keys, key=_interval_sort_key)  # intervals

        if len(ordered) < 2:
            continue

        paths = [variant_map[k] for k in ordered]
        stitched = stitch_vertical(paths)
        suffix = "-".join(str(k) for k in ordered)
        out_name = f"{TICKER}_{base}_{suffix}.png"
        out_path = REPORT_DIR / out_name
        stitched.save(out_path)
        saved_any = True
        print(f"✔ Saved {out_path}")

    if not saved_any:
        print("No matching daily or intraday images found.")
