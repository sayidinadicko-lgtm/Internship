"""Unit tests for hashtag generation."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ledeclicmental.content.hashtags import get_hashtags, _BRAND_TAGS


def test_returns_30_tags():
    tags = get_hashtags("résilience", "morning")
    assert len(tags) == 30, f"Expected 30 tags, got {len(tags)}"


def test_brand_tags_always_included():
    for slot in ["morning", "midday", "evening"]:
        tags = get_hashtags("discipline", slot)
        for brand in _BRAND_TAGS:
            assert brand in tags, f"Brand tag {brand} missing for slot={slot}"


def test_all_tags_start_with_hash():
    tags = get_hashtags("courage", "evening")
    for tag in tags:
        assert tag.startswith("#"), f"Tag without #: {tag}"


def test_no_duplicates():
    tags = get_hashtags("confiance en soi", "midday")
    assert len(tags) == len(set(tags)), "Duplicate hashtags found"


def test_deterministic_within_same_call():
    tags1 = get_hashtags("succès", "morning")
    tags2 = get_hashtags("succès", "morning")
    assert tags1 == tags2, "Hashtag selection should be deterministic"


def test_unknown_topic_falls_back():
    # Should not raise
    tags = get_hashtags("thème_inconnu_xyz", "morning")
    assert len(tags) == 30


if __name__ == "__main__":
    tests = [
        test_returns_30_tags,
        test_brand_tags_always_included,
        test_all_tags_start_with_hash,
        test_no_duplicates,
        test_deterministic_within_same_call,
        test_unknown_topic_falls_back,
    ]
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
    print("Done.")
