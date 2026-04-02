"""Unit tests for the image renderer."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ledeclicmental.content.generator import PostContent
from ledeclicmental.topics.trending import Topic
from ledeclicmental.image.renderer import render_post


def _make_content(slot: str = "morning") -> PostContent:
    return PostContent(
        topic=Topic("résilience", "resilience", "test"),
        slot=slot,
        quote_fr="Ce qui ne te tue pas te rend plus fort.",
        quote_en="What doesn't kill you makes you stronger.",
        caption_fr="Test caption FR.",
        caption_en="Test caption EN.",
        cta_fr="Commentez !",
        cta_en="Comment below!",
    )


def test_renders_jpeg_file():
    content = _make_content("morning")
    path = render_post(content)
    assert path.exists(), f"File not found: {path}"
    assert path.suffix == ".jpg"


def test_file_is_nonzero():
    content = _make_content("midday")
    path = render_post(content)
    assert path.stat().st_size > 10_000, "Image file is suspiciously small"


def test_all_slots_render():
    for slot in ["morning", "midday", "evening"]:
        path = render_post(_make_content(slot))
        assert path.exists(), f"Render failed for slot={slot}"


if __name__ == "__main__":
    tests = [test_renders_jpeg_file, test_file_is_nonzero, test_all_slots_render]
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
    print("Done.")
