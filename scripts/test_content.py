#!/usr/bin/env python3
"""
Dry-run test: Claude content generation + hashtags + audio.
No image rendering, no Instagram upload.

Usage:
    python scripts/test_content.py
    python scripts/test_content.py --slot evening --topic "discipline"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", default="morning", choices=["morning", "midday", "evening"])
    parser.add_argument("--topic", default=None, help="Override topic keyword (French)")
    args = parser.parse_args()

    from ledeclicmental.topics.trending import get_daily_topic, Topic
    from ledeclicmental.content.generator import generate_post
    from ledeclicmental.content.hashtags import get_hashtags, format_hashtags
    from ledeclicmental.content.audio import get_recommendation

    if args.topic:
        topic = Topic(keyword_fr=args.topic, keyword_en=args.topic, source="manual")
    else:
        topic = get_daily_topic()

    print(f"\n📌 Topic: {topic.keyword_fr} / {topic.keyword_en} [{topic.source}]")
    print(f"⏰ Slot:  {args.slot}")
    print("─" * 60)

    print("🤖 Calling Claude API…")
    content = generate_post(topic, args.slot)

    print(f"\n🇫🇷 Quote FR : {content.quote_fr}")
    print(f"🇬🇧 Quote EN : {content.quote_en}")
    print(f"\n🇫🇷 Caption FR:\n{content.caption_fr}")
    print(f"\n🇬🇧 Caption EN:\n{content.caption_en}")
    print(f"\n🇫🇷 CTA FR: {content.cta_fr}")
    print(f"🇬🇧 CTA EN: {content.cta_en}")

    tags = get_hashtags(topic.keyword_fr, args.slot)
    print(f"\n🏷️  Hashtags ({len(tags)}):\n{format_hashtags(tags)}")

    audio = get_recommendation(args.slot)
    print(f"\n🎵 Audio recommendation:")
    print(f"   {audio.title} – {audio.artist} ({audio.mood}, {audio.bpm} BPM)")
    print(f"   FR: {audio.caption_mention_fr}")
    print(f"   EN: {audio.caption_mention_en}")

    print("\n✅ Content generation test complete.")


if __name__ == "__main__":
    main()
