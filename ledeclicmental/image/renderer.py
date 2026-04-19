"""
Instagram post image renderer — style @ledeclicmental.

Génère 2 slides 1080x1350 px :
  Slide 1 : histoire + morale en FRANÇAIS
  Slide 2 : histoire + morale en ANGLAIS

Layout :
  - Histoire centrée (police auto-sized)
  - Ligne séparatrice
  - "Morale : ..." en gris clair
  - @LEDECLICMENTAL
  - Logo en bas
"""
from __future__ import annotations

import textwrap
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ledeclicmental.config import settings
from ledeclicmental.content.generator import PostContent
from ledeclicmental.utils.logger import get_logger

logger = get_logger(__name__)

W, H = 1080, 1350
BG_COLOR     = (0, 0, 0)
TEXT_COLOR   = (255, 255, 255)
MORAL_COLOR  = (190, 190, 190)
HANDLE_COLOR = (160, 160, 160)
SEP_COLOR    = (80, 80, 80)
MARGIN       = 75
MAX_W        = W - MARGIN * 2


def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_dir: Path = settings.assets_dir / "fonts"
    for candidate in [font_dir / name, font_dir / name.replace("-", "_")]:
        if candidate.exists():
            try:
                return ImageFont.truetype(str(candidate), size)
            except OSError:
                pass
    system_fonts = [
        "C:\\Windows\\Fonts\\COPRGTB.TTF",
        "C:\\Windows\\Fonts\\COPRGTL.TTF",
        "/Library/Fonts/Copperplate.ttc",
        "/System/Library/Fonts/Copperplate.ttc",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for sf in system_fonts:
        if Path(sf).exists():
            try:
                return ImageFont.truetype(sf, size)
            except OSError:
                pass
    return ImageFont.load_default()


def _wrap(text: str, max_chars: int) -> list[str]:
    return textwrap.wrap(text, width=max_chars)


def _block_height(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    spacing: int,
) -> int:
    total = 0
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        total += bbox[3] - bbox[1]
        if i < len(lines) - 1:
            total += spacing
    return total


def _draw_centered(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    spacing: int,
    y: int,
    color: tuple,
) -> int:
    for line in lines:
        bbox   = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        draw.text(((W - line_w) // 2, y), line, font=font, fill=color)
        y += line_h + spacing
    return y


def _draw_slide(story: str, moral: str) -> Image.Image:
    img  = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_handle = _load_font("COPRGTB.TTF", 26)
    font_moral  = _load_font("COPRGTB.TTF", 27)
    moral_lines   = _wrap(f"Morale : {moral}", max_chars=46)
    moral_spacing = 10

    # ── Auto-size story font ──────────────────────────────────────────────────
    story_lines: list[str] = []
    font_story = _load_font("COPRGTB.TTF", 36)
    for font_size in range(36, 21, -2):
        font_story = _load_font("COPRGTB.TTF", font_size)
        for max_chars in [32, 36, 40, 46]:
            candidate = _wrap(story, max_chars=max_chars)
            max_w = max(
                draw.textbbox((0, 0), l, font=font_story)[2] -
                draw.textbbox((0, 0), l, font=font_story)[0]
                for l in candidate
            )
            if max_w <= MAX_W:
                story_lines = candidate
                break
        if story_lines:
            break
    if not story_lines:
        story_lines = _wrap(story, max_chars=46)

    story_spacing = int(font_size * 0.38)

    # ── Heights ───────────────────────────────────────────────────────────────
    story_h = _block_height(draw, story_lines, font_story, story_spacing)
    moral_h = _block_height(draw, moral_lines, font_moral, moral_spacing)
    handle_h = 30
    sep_gap  = 35
    total_h  = story_h + sep_gap + 1 + sep_gap + moral_h + 30 + handle_h

    logo_zone_top = H - 150 - 50
    usable_top    = int(H * 0.08)
    usable_h      = logo_zone_top - usable_top - 40
    start_y       = usable_top + max(0, (usable_h - total_h) // 2)

    # ── Story ─────────────────────────────────────────────────────────────────
    y = _draw_centered(draw, story_lines, font_story, story_spacing, start_y, TEXT_COLOR)

    # ── Separator ─────────────────────────────────────────────────────────────
    y += sep_gap
    draw.line([(MARGIN + 60, y), (W - MARGIN - 60, y)], fill=SEP_COLOR, width=1)
    y += 1 + sep_gap

    # ── Moral ─────────────────────────────────────────────────────────────────
    y = _draw_centered(draw, moral_lines, font_moral, moral_spacing, y, MORAL_COLOR)

    # ── Handle ────────────────────────────────────────────────────────────────
    handle  = "@LEDECLICMENTAL"
    h_bbox  = draw.textbbox((0, 0), handle, font=font_handle)
    handle_w = h_bbox[2] - h_bbox[0]
    draw.text(((W - handle_w) // 2, y + 30), handle, font=font_handle, fill=HANDLE_COLOR)

    # ── Logo ──────────────────────────────────────────────────────────────────
    logo_path: Path = settings.assets_dir / "logo" / "ledeclicmental_logo.png"
    if logo_path.exists():
        try:
            logo      = Image.open(logo_path).convert("RGBA")
            logo_size = 150
            logo      = logo.resize((logo_size, logo_size), Image.LANCZOS)
            img.paste(logo, ((W - logo_size) // 2, H - logo_size - 50), logo)
        except Exception as exc:
            logger.warning("Impossible de coller le logo : %s", exc)

    return img


def render_post(content: PostContent) -> list[Path]:
    out_dir: Path = settings.data_dir / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    _cleanup_old_images(out_dir, days=7)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    paths: list[Path] = []

    slides = [
        (content.quote_fr, content.moral_fr, "fr"),
        (content.quote_en, content.moral_en, "en"),
    ]

    for story, moral, lang in slides:
        img      = _draw_slide(story, moral)
        out_path = out_dir / f"{timestamp}_{content.slot}_{lang}.jpg"
        img.convert("RGB").save(str(out_path), "JPEG", quality=95)
        logger.info("Slide générée : %s", out_path)
        paths.append(out_path)

    return paths


def _cleanup_old_images(directory: Path, days: int = 7) -> None:
    import time
    cutoff = time.time() - days * 86400
    for f in directory.glob("*.jpg"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
        except OSError:
            pass
