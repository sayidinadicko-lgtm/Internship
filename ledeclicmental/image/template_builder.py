"""
Template builder — generates the three background template PNGs
(morning, midday, evening) into assets/templates/.

Run once:  python -m ledeclicmental.image.template_builder

These templates can be replaced with custom designs from a designer.
The renderer will use them as background layers if present.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

W, H = 1080, 1080

_PALETTES = {
    "morning": {
        "top": (255, 140, 0),
        "bottom": (255, 70, 70),
        "accent": (255, 220, 120),
    },
    "midday": {
        "top": (15, 32, 90),
        "bottom": (40, 100, 200),
        "accent": (100, 200, 255),
    },
    "evening": {
        "top": (60, 20, 100),
        "bottom": (150, 50, 180),
        "accent": (220, 140, 255),
    },
}


def build_templates(output_dir: Path | None = None) -> None:
    if output_dir is None:
        root = Path(__file__).resolve().parent.parent.parent
        output_dir = root / "assets" / "templates"
    output_dir.mkdir(parents=True, exist_ok=True)

    for slot, palette in _PALETTES.items():
        img = Image.new("RGB", (W, H))
        top, bot = palette["top"], palette["bottom"]
        accent = palette["accent"]

        for y in range(H):
            r = int(top[0] + (bot[0] - top[0]) * y / H)
            g = int(top[1] + (bot[1] - top[1]) * y / H)
            b = int(top[2] + (bot[2] - top[2]) * y / H)
            for x in range(W):
                img.putpixel((x, y), (r, g, b))

        draw = ImageDraw.Draw(img)
        # Border accents
        draw.rectangle([(60, 60), (W - 60, 64)], fill=accent)
        draw.rectangle([(60, H - 64), (W - 60, H - 60)], fill=accent)
        # Corner dots
        for cx, cy in [(80, 80), (W - 80, 80), (80, H - 80), (W - 80, H - 80)]:
            draw.ellipse([(cx - 6, cy - 6), (cx + 6, cy + 6)], fill=accent)

        path = output_dir / f"template_{slot}.png"
        img.save(str(path), "PNG")
        print(f"Created: {path}")


if __name__ == "__main__":
    build_templates()
