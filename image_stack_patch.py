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

"""Filename pattern notes for intraday averages we accept (all kept backward compatible):
Legacy (no explicit interval token):
    VOO_intraday_average_close_5_days_look_back.png
Interval after 'intraday_': (preferred new style to match RVOL)
    VOO_intraday_30min_average_close_5_days_look_back.png
Interval after ticker (earlier experimental style some users may have):
    VOO_30min_intraday_average_close_5_days_look_back.png
"""

INTRA_AVG_PATTERN_AFTER_INTRADAY = re.compile(
    rf"^{re.escape(TICKER)}_intraday_(?P<interval>[a-z0-9]+)_average_(?P<atype>close|volume)_(?P<period>\d+)_days_look_back\.png$",
    re.IGNORECASE,
)

INTRA_AVG_PATTERN_AFTER_TICKER = re.compile(
    rf"^{re.escape(TICKER)}_(?P<interval>[a-z0-9]+)_intraday_average_(?P<atype>close|volume)_(?P<period>\d+)_days_look_back\.png$",
    re.IGNORECASE,
)

INTRA_AVG_PATTERN_LEGACY = re.compile(
    rf"^{re.escape(TICKER)}_intraday_average_(?P<atype>close|volume)_(?P<period>\d+)_days_look_back\.png$",
    re.IGNORECASE,
)


# Intraday (RVOL):
# New (interval-aware) pattern, e.g. VOO_intraday_5min_rvol_last_10_days_with_20_day_lookback.png
INTRA_RVOL_PATTERN_WITH_INTERVAL = re.compile(
    rf"^{re.escape(TICKER)}_intraday_(?P<interval>[a-z0-9]+)_rvol_last_(?P<show>\d+)_days_with_(?P<period>\d+)_day_lookback\.png$",
    re.IGNORECASE,
)

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

        # ---- Intraday Averages (interval-aware preferred) ----
        m_avg_new = INTRA_AVG_PATTERN_AFTER_INTRADAY.match(name)
        if m_avg_new:
            interval = m_avg_new.group("interval").lower()
            atype = m_avg_new.group("atype").lower()            # close | volume
            period = int(m_avg_new.group("period"))              # look-back days
            base = f"intraday_{interval}_average_{atype}"
            groups.setdefault(base, {})[period] = p
            continue

        # ---- Intraday Averages (alternate style: interval after ticker) ----
        m_avg_alt = INTRA_AVG_PATTERN_AFTER_TICKER.match(name)
        if m_avg_alt:
            interval = m_avg_alt.group("interval").lower()
            atype = m_avg_alt.group("atype").lower()
            period = int(m_avg_alt.group("period"))
            base = f"intraday_{interval}_average_{atype}"
            groups.setdefault(base, {})[period] = p
            continue

        # ---- Intraday Averages (legacy, no interval in filename) ----
        m_avg_legacy = INTRA_AVG_PATTERN_LEGACY.match(name)
        if m_avg_legacy:
            atype = m_avg_legacy.group("atype").lower()
            period = int(m_avg_legacy.group("period"))
            interval_cfg = getattr(config, "INTRADAY_INTERVAL", None)
            if interval_cfg:
                base = f"intraday_{str(interval_cfg).lower()}_average_{atype}"
            else:
                base = f"intraday_average_{atype}"
            groups.setdefault(base, {})[period] = p
            continue

        m2a = INTRA_RVOL_PATTERN_WITH_INTERVAL.match(name)
        if m2a:
            # Filename includes interval, e.g., intraday_5min_rvol_last_10_days_with_20_day_lookback.png
            interval = m2a.group("interval").lower()
            show_n = int(m2a.group("show"))
            period = int(m2a.group("period"))
            base = f"intraday_{interval}_rvol_last_{show_n}_days_with_lookback"
            groups.setdefault(base, {})[period] = p
            continue

        m2 = INTRA_RVOL_PATTERN.match(name)
        if m2:
            # Legacy filenames without interval; fall back to config interval for grouping/output
            interval = str(getattr(config, "INTRADAY_INTERVAL", "1min")).lower()
            show_n = int(m2.group("show"))          # e.g., 10
            period = int(m2.group("period"))        # 5 / 10 / 20
            base = f"intraday_{interval}_rvol_last_{show_n}_days_with_lookback"
            groups.setdefault(base, {})[period] = p
            continue

    return groups

def discover_intraday_images_by_interval():
    """
    Return { base -> { interval:str -> Path } } to allow stacking ACROSS intervals
    for the *same* logical metric parameters.

    Two families supported:
      A) Averages: intraday_<interval>_average_(close|volume)_{period}_days_look_back.png
         base key = f"intraday_average_{atype}_{period}_days_look_back"
         interval keys = e.g., '1min', '5min', '30min', '60min'

      B) RVOL: intraday_<interval>_rvol_last_{show}_days_with_{period}_day_lookback.png
         base key = f"intraday_rvol_last_{show}_days_with_{period}_day_lookback"
         interval keys = as above

    Legacy names (no interval) are ignored for cross-interval stacks because they
    do not encode an interval in the filename.
    """
    by_interval = {}

    for p in FIG_DIR.glob("*.png"):
        name = p.name

        # ---- A) Averages (interval-aware) ----
        m_avg_new = INTRA_AVG_PATTERN_AFTER_INTRADAY.match(name)
        if m_avg_new:
            interval = m_avg_new.group("interval").lower()
            atype = m_avg_new.group("atype").lower()
            period = int(m_avg_new.group("period"))
            base = f"intraday_average_{atype}_{period}_days_look_back"
            by_interval.setdefault(base, {})[interval] = p
            continue

        m_avg_alt = INTRA_AVG_PATTERN_AFTER_TICKER.match(name)
        if m_avg_alt:
            interval = m_avg_alt.group("interval").lower()
            atype = m_avg_alt.group("atype").lower()
            period = int(m_avg_alt.group("period"))
            base = f"intraday_average_{atype}_{period}_days_look_back"
            by_interval.setdefault(base, {})[interval] = p
            continue

        # ---- B) RVOL (interval-aware) ----
        m2a = INTRA_RVOL_PATTERN_WITH_INTERVAL.match(name)
        if m2a:
            interval = m2a.group("interval").lower()
            show_n = int(m2a.group("show"))
            period = int(m2a.group("period"))
            base = f"intraday_rvol_last_{show_n}_days_with_{period}_day_lookback"
            by_interval.setdefault(base, {})[interval] = p
            continue

    return by_interval

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

    # Also collect cross-interval groupings (same parameters, different intervals)
    intra_by_interval = discover_intraday_images_by_interval()
    for k, v in intra_by_interval.items():
        # re-key intervals as sortable tokens, but keep original order lexicographically
        groups[k] = v

    if not groups:
        print("No matching daily or intraday images found.")
        return

    # Stitch each base (e.g., daily_close, intraday_average_close, intraday_rvol_last_10_days_with_lookback)
    for base, period_map in groups.items():
        # period_map can be keyed by int (standard) or str intervals (cross-interval)
        if all(isinstance(k, int) for k in period_map.keys()):
            ordered_keys = sorted(period_map.keys())
        else:
            # Sort intervals in a human-friendly way: numeric minutes first if possible
            def interval_key(tok: str):
                # extract leading integer if like '30min'; fallback to tok
                import re as _re
                m = _re.match(r"(\d+)", tok)
                return (0, int(m.group(1))) if m else (1, tok)
            ordered_keys = sorted(period_map.keys(), key=interval_key)

        if len(ordered_keys) < 2:
            continue
        paths = [period_map[k] for k in ordered_keys]
        combined = stitch_vertical(paths)
        suffix = "-".join(str(k) for k in ordered_keys)
        out_name = f"{TICKER}_{base}_{suffix}.png"
        save_path = Path(getattr(config, "REPORT_PATH", f"./report/{TICKER}/"))
        save_path.mkdir(parents=True, exist_ok=True)
        out_path = save_path / out_name
        combined.save(out_path)
        print(f"✔ Saved {out_path}")
