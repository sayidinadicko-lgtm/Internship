"""Unit tests for audio recommendation."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ledeclicmental.content.audio import get_recommendation, _SLOT_MOODS


def test_returns_track_for_all_slots():
    for slot in ["morning", "midday", "evening"]:
        track = get_recommendation(slot)
        assert track.title, f"No title for slot={slot}"
        assert track.artist, f"No artist for slot={slot}"


def test_mood_matches_slot():
    for slot, moods in _SLOT_MOODS.items():
        track = get_recommendation(slot)
        assert track.mood in moods, f"Wrong mood {track.mood} for slot={slot}"


def test_caption_mentions_present():
    for slot in ["morning", "midday", "evening"]:
        track = get_recommendation(slot)
        assert track.caption_mention_fr.startswith("🎵")
        assert track.caption_mention_en.startswith("🎵")


def test_deterministic():
    t1 = get_recommendation("morning")
    t2 = get_recommendation("morning")
    assert t1.title == t2.title


if __name__ == "__main__":
    tests = [
        test_returns_track_for_all_slots,
        test_mood_matches_slot,
        test_caption_mentions_present,
        test_deterministic,
    ]
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
    print("Done.")
