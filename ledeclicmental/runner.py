"""
Génère 3 posts motivationnels, les dépose sur le Bureau et les envoie par email.

Structure créée :
  Bureau/
    Le déclic mental/
      Post 1/  slide_fr.jpg  slide_en.jpg  legende.txt
      Post 2/  ...
      Post 3/  ...

Les anciens posts sont supprimés à chaque lancement.
Les histoires utilisées ne reviennent pas avant 120 jours.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from ledeclicmental.config import settings
from ledeclicmental.content.generator import generate_post
from ledeclicmental.content.hashtags import format_hashtags, get_hashtags
from ledeclicmental.content.stories import get_multiple_stories
from ledeclicmental.image.renderer import render_post
from ledeclicmental.utils.history import record_topic_used
from ledeclicmental.utils.logger import get_logger
from ledeclicmental.utils.mailer import send_post_email

logger = get_logger(__name__)

_FOLDER_NAME = "Le déclic mental"


def _find_desktop() -> Path:
    home = Path.home()
    candidates = [
        home / "OneDrive" / "Bureau",
        home / "OneDrive" / "Desktop",
        home / "Bureau",
        home / "Desktop",
    ]
    for path in candidates:
        if path.exists():
            return path
    fallback = home / "Desktop"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def _build_caption(content) -> str:
    fr_block = f"{content.caption_fr}\n\n{content.cta_fr}"
    en_block = f"{content.caption_en}\n\n{content.cta_en}"
    tags = get_hashtags(content.story_title, "morning")
    return (
        f"{fr_block}\n\n"
        f"- - -\n\n"
        f"{en_block}\n\n"
        f".\n.\n.\n\n"
        f"{format_hashtags(tags)}"
    )


def generate_daily_posts() -> None:
    desktop = _find_desktop()
    output_dir = desktop / _FOLDER_NAME

    if output_dir.exists():
        shutil.rmtree(output_dir)
        logger.info("Anciens posts supprimes.")
    output_dir.mkdir(parents=True)

    stories = get_multiple_stories(n=3)
    logger.info("Histoires du jour : %s", " | ".join(s.title_fr for s in stories))

    for i, story in enumerate(stories, start=1):
        post_dir = output_dir / f"Post {i}"
        post_dir.mkdir()

        content = generate_post(story, slot="morning")
        logger.info("Post %d — histoire : '%s' (%s)", i, content.story_title, content.story_source)

        image_paths = render_post(content)

        slide_fr = slide_en = None
        for img_path in image_paths:
            lang = "fr" if "_fr." in img_path.name else "en"
            dest = post_dir / f"slide_{lang}.jpg"
            shutil.copy2(img_path, dest)
            if lang == "fr":
                slide_fr = dest
            else:
                slide_en = dest

        caption = _build_caption(content)
        (post_dir / "legende.txt").write_text(caption, encoding="utf-8")

        if slide_fr and slide_en:
            try:
                send_post_email(i, slide_fr, slide_en, caption)
                print(f"  Email POST_{i} envoye.")
            except Exception as exc:
                logger.warning("Echec envoi email POST_%d : %s", i, exc)
                print(f"  Echec email POST_{i} : {exc}")

        logger.info("Post %d enregistre dans %s", i, post_dir)

    for story in stories:
        record_topic_used(story.title_fr)

    try:
        os.startfile(str(output_dir))
    except Exception:
        pass

    print(f"\n{'='*55}")
    print(f"  3 posts generes et envoyes par email !")
    print(f"  Dossier : {output_dir}")
    print(f"{'='*55}\n")
    for i, story in enumerate(stories, 1):
        print(f"  Post {i} : {story.title_fr} ({story.source})")
    print()
