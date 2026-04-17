#!/usr/bin/env python3
"""
Test du renderer — aucun appel API, aucun Instagram.

Usage:
    python scripts/test_image.py
    python scripts/test_image.py --slot evening

Génère 2 JPEG (FR + EN) dans data/generated/ et affiche les chemins.
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

    topic = Topic(keyword_fr="résilience", keyword_en="resilience", source="test")
    content = PostContent(
        topic=topic,
        slot=args.slot,
        quote_fr="La tempête ne dure pas, mais le rocher reste.",
        quote_en="The storm doesn't last, but the rock remains.",
        caption_fr=(
            "Chaque épreuve forge ton caractère. "
            "Ce n'est pas la chute qui te définit, c'est la façon dont tu te relèves."
        ),
        caption_en=(
            "Every challenge shapes your character. "
            "It's not the fall that defines you — it's how you rise."
        ),
        cta_fr="Écris en commentaire un mot qui représente ta force 👇",
        cta_en="Drop one word in the comments that represents your strength 👇",
    )

    paths = render_post(content)
    print(f"\n✅ Slides générées :")
    for p in paths:
        print(f"   {p}")
    print("\nOuvre ces fichiers pour vérifier le rendu visuel.")


if __name__ == "__main__":
    main()
