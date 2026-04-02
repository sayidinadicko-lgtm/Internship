"""
Instagram posting via instagrapi — carousel (album) FR + EN.

Chaque post = carousel 2 slides :
  Slide 1 : citation en français
  Slide 2 : citation en anglais

Features :
- Persistance de session (évite les re-logins)
- 3 tentatives avec back-off 60s
- Délai aléatoire 30–90s avant upload (comportement humain)
- Mode DRY_RUN (simulation sans publication)
"""
from __future__ import annotations

import random
import time
from pathlib import Path

from ledeclicmental.config import settings
from ledeclicmental.content.audio import AudioTrack
from ledeclicmental.content.generator import PostContent
from ledeclicmental.content.hashtags import format_hashtags, get_hashtags
from ledeclicmental.utils.logger import get_logger

logger = get_logger(__name__)

_MAX_RETRIES = 3
_RETRY_BACKOFF = 60


def _build_caption(content: PostContent, audio: AudioTrack) -> str:
    """
    Assemble la légende complète du post Instagram.

    Structure :
      [Légende FR + CTA FR]

      ──────────────

      [Légende EN + CTA EN]

      .
      .
      .
      [30 hashtags]

      [Mention audio FR / EN]
    """
    fr_block = f"{content.caption_fr}\n\n{content.cta_fr}"
    en_block = f"{content.caption_en}\n\n{content.cta_en}"

    tags = get_hashtags(content.topic.keyword_fr, content.slot)
    hashtag_line = format_hashtags(tags)

    audio_line = f"{audio.caption_mention_fr}\n{audio.caption_mention_en}"

    return (
        f"{fr_block}\n\n"
        f"──────────────\n\n"
        f"{en_block}\n\n"
        f".\n.\n.\n\n"
        f"{hashtag_line}\n\n"
        f"{audio_line}"
    )


def _get_client():
    """Client instagrapi avec persistance de session."""
    try:
        from instagrapi import Client  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Installe instagrapi : pip install instagrapi") from exc

    cl = Client()
    session_file: Path = settings.instagram_session_file
    session_file.parent.mkdir(parents=True, exist_ok=True)

    if session_file.exists():
        try:
            cl.load_settings(session_file)
            cl.login(settings.instagram_username, settings.instagram_password)
            cl.get_timeline_feed()
            logger.info("Session Instagram chargée depuis %s", session_file)
            return cl
        except Exception as exc:
            logger.warning("Session invalide (%s) — reconnexion.", exc)

    logger.info("Connexion à Instagram en tant que @%s", settings.instagram_username)
    cl.login(settings.instagram_username, settings.instagram_password)
    cl.dump_settings(session_file)
    logger.info("Session sauvegardée dans %s", session_file)
    return cl


def upload_post(image_paths: list[Path], content: PostContent, audio: AudioTrack) -> str:
    """
    Publie un carousel (album) sur Instagram.

    image_paths : [slide_fr.jpg, slide_en.jpg]
    Retourne le media_id (chaîne vide en mode DRY_RUN).
    """
    caption = _build_caption(content, audio)

    if settings.dry_run:
        logger.info("[DRY RUN] Carousel simulé : %s", [str(p) for p in image_paths])
        logger.info("[DRY RUN] Légende (300 premiers caractères) :\n%s", caption[:300])
        return "DRY_RUN_MEDIA_ID"

    # Délai anti-bot
    delay = random.uniform(30, 90)
    logger.info("Attente de %.0f secondes avant publication…", delay)
    time.sleep(delay)

    cl = _get_client()

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            if len(image_paths) == 1:
                # Post simple (fallback)
                media = cl.photo_upload(
                    path=str(image_paths[0]),
                    caption=caption,
                )
            else:
                # Carousel (album)
                media = cl.album_upload(
                    paths=[str(p) for p in image_paths],
                    caption=caption,
                )
            media_id = str(media.id)
            logger.info("Publié avec succès — media_id=%s", media_id)
            return media_id

        except Exception as exc:
            logger.error("Tentative %d/%d échouée : %s", attempt, _MAX_RETRIES, exc)
            if attempt < _MAX_RETRIES:
                logger.info("Nouvelle tentative dans %d secondes…", _RETRY_BACKOFF)
                time.sleep(_RETRY_BACKOFF)
            else:
                raise RuntimeError(
                    f"Échec de la publication après {_MAX_RETRIES} tentatives"
                ) from exc

    return ""
