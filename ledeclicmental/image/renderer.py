"""
Instagram post image renderer — style @ledeclicmental.

Génère 2 slides 1080x1080 px (carousel Instagram) :
  Slide 1 : citation en FRANÇAIS
  Slide 2 : citation en ANGLAIS

Style exact du compte :
  - Fond noir pur
  - Texte blanc gras majuscules centré
  - Grand " d'ouverture en haut à gauche du bloc texte
  - @LEDECLICMENTAL en petit sous la citation
  - Logo cerveau centré en bas
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

W, H = 1080, 1350  # format 4:5 Instagram portrait
BG_COLOR = (0, 0, 0)          # noir pur
TEXT_COLOR = (255, 255, 255)   # blanc
HANDLE_COLOR = (200, 200, 200) # gris clair pour le handle


def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_dir: Path = settings.assets_dir / "fonts"
    for candidate in [font_dir / name, font_dir / name.replace("-", "_")]:
        if candidate.exists():
            try:
                return ImageFont.truetype(str(candidate), size)
            except OSError:
                pass
    # Fallback système — Copperplate en priorité
    system_fonts = [
        "C:\\Windows\\Fonts\\COPRGTB.TTF",           # Copperplate Gothic Bold (Windows)
        "C:\\Windows\\Fonts\\COPRGTL.TTF",           # Copperplate Gothic Light (Windows)
        "/Library/Fonts/Copperplate.ttc",            # macOS
        "/System/Library/Fonts/Copperplate.ttc",     # macOS système
        "C:\\Windows\\Fonts\\arialbd.ttf",           # fallback Arial Bold
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for sf in system_fonts:
        if Path(sf).exists():
            try:
                return ImageFont.truetype(sf, size)
            except OSError:
                pass
    logger.warning("Aucune police TrueType trouvée — police bitmap par défaut.")
    return ImageFont.load_default()


def _wrap_text(text: str, max_chars: int) -> list[str]:
    """Découpe le texte en lignes sans couper les mots."""
    return textwrap.wrap(text.upper(), width=max_chars)


def _total_text_height(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    line_spacing: int,
) -> int:
    total = 0
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        total += bbox[3] - bbox[1]
        if i < len(lines) - 1:
            total += line_spacing
    return total


def _draw_slide(quote: str, lang: str, content: PostContent) -> Image.Image:
    """
    Crée une image 1080x1080 dans le style @ledeclicmental.

    lang : "fr" | "en"
    """
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # ── Polices (Copperplate Gothic Bold) ────────────────────────────────────
    font_quote  = _load_font("COPRGTB.TTF", 85)
    font_open   = _load_font("COPRGTB.TTF", 130)
    font_handle = _load_font("COPRGTB.TTF", 34)

    # ── Préparer les lignes de la citation ────────────────────────────────────
    lines = _wrap_text(quote, max_chars=18)

    # Zone de texte : adaptée au format 4:5 (1080x1350)
    text_zone_top    = 220
    text_zone_bottom = 1020
    text_zone_h      = text_zone_bottom - text_zone_top
    line_spacing     = 18

    text_h = _total_text_height(draw, lines, font_quote, line_spacing)
    text_start_y = text_zone_top + (text_zone_h - text_h) // 2

    # ── Grand guillemet " ouvrant (haut gauche du bloc texte) ─────────────────
    open_quote = "\u201c"   # "
    oq_bbox = draw.textbbox((0, 0), open_quote, font=font_open)
    oq_h = oq_bbox[3] - oq_bbox[1]
    # Positionné à gauche, légèrement au-dessus du début du texte
    draw.text(
        (60, text_start_y - oq_h // 2 - 10),
        open_quote,
        font=font_open,
        fill=TEXT_COLOR,
    )

    # ── Citation (centré) ─────────────────────────────────────────────────────
    y = text_start_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_quote)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        x = (W - line_w) // 2
        draw.text((x, y), line, font=font_quote, fill=TEXT_COLOR)
        y += line_h + line_spacing

    # ── @LEDECLICMENTAL ───────────────────────────────────────────────────────
    handle = "@LEDECLICMENTAL"
    h_bbox = draw.textbbox((0, 0), handle, font=font_handle)
    handle_w = h_bbox[2] - h_bbox[0]
    handle_x = (W - handle_w) // 2
    handle_y = y + 40
    draw.text((handle_x, handle_y), handle, font=font_handle, fill=HANDLE_COLOR)

    # ── Logo cerveau (centré en bas) ──────────────────────────────────────────
    logo_path: Path = settings.assets_dir / "logo" / "ledeclicmental_logo.png"
    if logo_path.exists():
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo_size = 160
            logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
            logo_x = (W - logo_size) // 2
            logo_y = H - logo_size - 80
            img.paste(logo, (logo_x, logo_y), logo)
        except Exception as exc:
            logger.warning("Impossible de coller le logo : %s", exc)
    else:
        logger.info("Logo absent — rendu sans logo.")

    return img


def render_post(content: PostContent) -> list[Path]:
    """
    Génère 2 slides (FR + EN) pour un carousel Instagram.
    Retourne la liste des chemins vers les JPEG générés.
    """
    out_dir: Path = settings.data_dir / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    _cleanup_old_images(out_dir, days=7)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    paths: list[Path] = []

    slides = [
        (content.quote_fr, "fr"),
        (content.quote_en, "en"),
    ]

    for quote, lang in slides:
        img = _draw_slide(quote, lang, content)
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
