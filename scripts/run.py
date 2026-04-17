#!/usr/bin/env python3
"""
Production entry point for @ledeclicmental Instagram automation.

Usage:
    python scripts/run.py

    # Dry-run (no actual Instagram upload):
    DRY_RUN=true python scripts/run.py

    # Run a single post immediately (for testing):
    python scripts/run.py --now morning
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> None:
    parser = argparse.ArgumentParser(description="@ledeclicmental Instagram bot")
    parser.add_argument(
        "--now",
        metavar="SLOT",
        choices=["morning", "midday", "evening"],
        help="Run one post immediately for the given slot (skip scheduler)",
    )
    args = parser.parse_args()

    if args.now:
        from ledeclicmental.scheduler import run_post_job
        run_post_job(args.now)
    else:
        from ledeclicmental.scheduler import start_scheduler
        start_scheduler()


if __name__ == "__main__":
    main()
