"""Command-line helpers for ATR-Sigma RVOL scripts."""

from __future__ import annotations

import argparse
from pathlib import Path
import config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ATR-Sigma RVOL pipeline.")
    parser.add_argument(
        "--ticker", "-t",
        dest="ticker",
        help="Override stock ticker (e.g., CRCL)",
    )
    parser.add_argument(
        "--data-path",
        dest="data_path",
        type=Path,
        help="Custom data directory containing downloaded CSV files.",
    )
    parser.add_argument(
        "--report-base",
        dest="report_base_path",
        type=Path,
        help="Base directory where stitched reports should be written.",
    )
    parser.add_argument(
        "--figure-base",
        dest="figure_base_path",
        type=Path,
        help="Base directory for saving individual chart images.",
    )
    return parser


def parse_args(argv=None) -> argparse.Namespace:
    parser = build_parser()
    return parser.parse_args(argv)


def apply_overrides_from_args(args: argparse.Namespace) -> None:
    overrides = {}
    if getattr(args, "ticker", None):
        overrides["stock_ticker"] = args.ticker
    if getattr(args, "data_path", None):
        overrides["data_path"] = args.data_path
    if getattr(args, "report_base_path", None):
        overrides["report_base_path"] = args.report_base_path
    if getattr(args, "figure_base_path", None):
        overrides["figure_base_path"] = args.figure_base_path

    if overrides:
        config.apply_runtime_overrides(**overrides)


def configure_from_cli(argv=None) -> argparse.Namespace:
    args = parse_args(argv)
    apply_overrides_from_args(args)
    return args

