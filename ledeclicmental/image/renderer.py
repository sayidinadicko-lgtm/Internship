"""
Instagram post image renderer.

Generates 1080x1080 px images with:
  - Gradient background (slot-specific color palette)
  - French quote (large, centered)
  - English quote (smaller, below)
  - Horizontal separator
  - Logo overlay (bottom-right)
  - @ledeclicmental handle (bottom-center)

Falls back to system fonts if custom fonts are not found in assets/fonts/.
"""
from __future__ import annotations

import textwrap
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from ledeclicmental.config import settings
from ledeclicmental.content.generator import PostContent
from ledeclicmental.utils.logger import get_logger

logger = get_logger(__name__)

# ── Canvas size ───────────────────────────────────────────────────────────────
W, H = 1080, 1080

# ── Slot color palettes (gradient start → end as RGB tuples) ─────────────────
_PALETTES: dict[str, dict[str, tuple[int, int, int]]] = {
    "morning": {
        "top": (255, 140, 0),       # deep orange
        "bottom": (255, 70, 70),    # warm red
        "accent": (255, 220, 120),  # golden yellow
    },
    "midday": {
        "top": (15, 32, 90),        # deep navy
        "bottom": (40, 100, 200),   # bright blue
        "accent": (100, 200, 255),  # sky blue
    },
    "evening": {
        "top": (60, 20, 100),       # deep violet
        "bottom": (150, 50, 180),   # purple
        "accent": (220, 140, 255),  # lavender
    },
}


def _make_gradient(colors: dict[str, tuple[int, int, int]]) -> Image.Image:
    """Create a vertical linear gradient background."""
    img = Image.new("RGB", (W, H))
    top = colors["top"]
    bot = colors["bottom"]
    for y in range(H):
        r = int(top[0] + (bot[0] - top[0]) * y / H)
        g = int(top[1] + (bot[1] - top[1]) * y / H)
        b = int(top[2] + (bot[2] - top[2]) * y / H)
        for x in range(W):
            img.putpixel((x, y), (r, g, b))
    return img


def _dark_overlay(img: Image.Image, alpha: int = 80) -> Image.Image:
    """Add a semi-transparent dark overlay for better text contrast."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, alpha))
    base = img.convert("RGBA")
    combined = Image.alpha_composite(base, overlay)
    return combined.convert("RGB")


def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_dir: Path = settings.assets_dir / "fonts"
    candidates = [
        font_dir / name,
        font_dir / name.replace("-", "_"),
    ]
    for path in candidates:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                pass
    # System font fallback
    system_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\arialbd.ttf",
    ]
    for sf in system_fonts:
        if Path(sf).exists():
            try:
                return ImageFont.truetype(sf, size)
            except OSError:
                pass
    logger.warning("No TrueType font found — using PIL default bitmap font.")
    return ImageFont.load_default()


def _wrap_text(text: str, max_chars: int) -> list[str]:
    return textwrap.wrap(text, width=max_chars)


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    color: tuple[int, int, int, int],
    center_y: int,
    line_spacing: int = 10,
) -> int:
    """Draw centered multiline text. Returns the y position after the last line."""
    # Measure total block height
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])

    total_h = sum(line_heights) + line_spacing * (len(lines) - 1)
    y = center_y - total_h // 2

    for i, (line, lh) in enumerate(zip(lines, line_heights)):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (W - text_w) // 2
        # Shadow
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 100))
        draw.text((x, y), line, font=font, fill=color)
        y += lh + line_spacing

    return y


def render_post(content: PostContent) -> Path:
    """
    Render a 1080x1080 Instagram post image.
    Returns the path to the saved JPEG.
    """
    slot = content.slot
    palette = _PALETTES.get(slot, _PALETTES["morning"])
    accent = palette["accent"]

    # ── Background ───────────────────────────────────────────────────────────
    img = _make_gradient(palette)
    img = _dark_overlay(img, alpha=60)

    draw = ImageDraw.Draw(img, "RGBA")

    # ── Decorative accent lines ───────────────────────────────────────────────
    draw.rectangle([(60, 60), (W - 60, 64)], fill=(*accent, 120))
    draw.rectangle([(60, H - 64), (W - 60, H - 60)], fill=(*accent, 120))

    # ── Fonts ────────────────────────────────────────────────────────────────
    font_quote_fr = _load_font("Montserrat-Bold.ttf", 58)
    font_quote_en = _load_font("Montserrat-Bold.ttf", 38)
    font_handle = _load_font("Montserrat-Bold.ttf", 28)

    # ── French quote (upper 55% of canvas) ───────────────────────────────────
    lines_fr = _wrap_text(f'« {content.quote_fr} »', max_chars=24)
    white = (255, 255, 255, 255)
    y_after_fr = _draw_centered_text(draw, lines_fr, font_quote_fr, white, center_y=390, line_spacing=14)

    # ── Separator ────────────────────────────────────────────────────────────
    sep_y = y_after_fr + 30
    draw.rectangle([(W // 4, sep_y), (3 * W // 4, sep_y + 2)], fill=(*accent, 180))

    # ── English quote (below separator) ──────────────────────────────────────
    lines_en = _wrap_text(f'"{content.quote_en}"', max_chars=32)
    en_color = (220, 220, 220, 200)
    _draw_centered_text(draw, lines_en, font_quote_en, en_color, center_y=sep_y + 100, line_spacing=10)

    # ── Account handle (bottom center) ───────────────────────────────────────
    handle = "@ledeclicmental"
    bbox = draw.textbbox((0, 0), handle, font=font_handle)
    handle_w = bbox[2] - bbox[0]
    handle_x = (W - handle_w) // 2
    draw.text((handle_x + 1, H - 89), handle, font=font_handle, fill=(0, 0, 0, 100))
    draw.text((handle_x, H - 90), handle, font=font_handle, fill=(*accent, 255))

    # ── Logo overlay (bottom-right) ───────────────────────────────────────────
    logo_path: Path = settings.assets_dir / "logo" / "ledeclicmental_logo.png"
    if logo_path.exists():
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo = logo.resize((160, 160), Image.LANCZOS)
            # Position: 20px from right and bottom edges
            logo_x = W - 160 - 20
            logo_y = H - 160 - 20
            img.paste(logo, (logo_x, logo_y), logo)
            logger.debug("Logo composited at (%d, %d)", logo_x, logo_y)
        except Exception as exc:
            logger.warning("Could not composite logo: %s", exc)
    else:
        logger.info("Logo not found at %s — skipping logo overlay.", logo_path)
        # Draw a text placeholder instead
        draw.text((W - 200, H - 50), "@ledeclicmental", font=font_handle, fill=(*accent, 200))

    # ── Save ─────────────────────────────────────────────────────────────────
    out_dir: Path = settings.data_dir / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Clean files older than 7 days
    _cleanup_old_images(out_dir, days=7)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{timestamp}_{slot}.jpg"
    img.convert("RGB").save(str(out_path), "JPEG", quality=92)
    logger.info("Image saved: %s", out_path)
    return out_path


def _cleanup_old_images(directory: Path, days: int = 7) -> None:
    import time
    cutoff = time.time() - days * 86400
    for f in directory.glob("*.jpg"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
                logger.debug("Deleted old image: %s", f)
        except OSError:
            pass
