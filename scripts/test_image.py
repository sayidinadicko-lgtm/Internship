#!/usr/bin/env python3
"""
Test the image renderer locally — no Claude API call, no Instagram.

Usage:
    python scripts/test_image.py
    python scripts/test_image.py --slot evening

Outputs a JPEG to data/generated/ and prints the path.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ledeclicmental.content.generator import PostContent
from ledeclicmental.topics.trending import Topic
from ledeclicmental.image.renderer import render_post


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", default="morning", choices=["morning", "midday", "evening"])
    args = parser.parse_args()

    # Dummy content — no API call needed
    topic = Topic(keyword_fr="résilience", keyword_en="resilience", source="test")
    content = PostContent(
        topic=topic,
        slot=args.slot,
        quote_fr="La tempête ne dure pas, mais le rocher reste.",
        quote_en="The storm doesn't last, but the rock remains.",
        caption_fr=(
            "Chaque épreuve que tu traverses forge ton caractère. "
            "Ce n'est pas la chute qui définit ta trajectoire, "
            "c'est la façon dont tu te relèves. Aujourd'hui, choisis de te relever."
        ),
        caption_en=(
            "Every challenge you face shapes your character. "
            "It's not the fall that defines your path, "
            "it's how you rise. Today, choose to rise."
        ),
        cta_fr="Écris en commentaire un mot qui représente ta force du moment 👇",
        cta_en="Drop one word in the comments that represents your current strength 👇",
    )

    path = render_post(content)
    print(f"\n✅ Image generated: {path}")
    print("Open it with your image viewer to preview the design.")


if __name__ == "__main__":
    main()
