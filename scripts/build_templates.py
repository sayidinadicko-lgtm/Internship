#!/usr/bin/env python3
"""
Generate the three background template PNGs (morning, midday, evening).

Run this once to populate assets/templates/ before starting the bot.
Replace the generated PNGs with custom designs from a designer if desired.

Usage:
    python scripts/build_templates.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ledeclicmental.image.template_builder import build_templates

if __name__ == "__main__":
    print("Building template backgrounds…")
    build_templates()
    print("Done. Templates saved to assets/templates/")
