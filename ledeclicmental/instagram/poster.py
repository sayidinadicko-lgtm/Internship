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

import base64
import os
import random
import tempfile
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

      - - -

      [Légende EN + CTA EN]

      .
      .
      .
      [30 hashtags]
    """
    fr_block = f"{content.caption_fr}\n\n{content.cta_fr}"
    en_block = f"{content.caption_en}\n\n{content.cta_en}"

    tags = get_hashtags(content.topic.keyword_fr, content.slot)
    hashtag_line = format_hashtags(tags)

    return (
        f"{fr_block}\n\n"
        f"- - -\n\n"
        f"{en_block}\n\n"
        f".\n.\n.\n\n"
        f"{hashtag_line}"
    )


def _get_client():
    """
    Client instagrapi avec persistance de session.

    Priorité :
      1. Variable d'env INSTAGRAM_SESSION_B64 (GitHub Actions / CI)
         → charge la session sans re-login pour éviter le blocage IP
      2. Fichier session local (exécution sur PC)
      3. Login fresh (première exécution locale)
    """
    try:
        from instagrapi import Client  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Installe instagrapi : pip install instagrapi") from exc

    cl = Client()
    session_file: Path = settings.instagram_session_file
    session_file.parent.mkdir(parents=True, exist_ok=True)

    # ── Cas 1 : session encodée en base64 (CI/GitHub Actions) ────────────────
    session_b64 = os.getenv("INSTAGRAM_SESSION_B64", "")
    if session_b64:
        try:
            session_json = base64.b64decode(session_b64).decode("utf-8")
            tmp = Path(tempfile.mktemp(suffix=".json"))
            tmp.write_text(session_json, encoding="utf-8")
            cl.load_settings(tmp)
            tmp.unlink(missing_ok=True)
            cl.get_timeline_feed()   # vérifie la session SANS re-login
            logger.info("Session CI chargée depuis INSTAGRAM_SESSION_B64.")
            return cl
        except Exception as exc:
            logger.warning("Session CI invalide (%s) — tentative login.", exc)

    # ── Cas 2 : fichier session local ────────────────────────────────────────
    if session_file.exists():
        try:
            cl.load_settings(session_file)
            cl.login(settings.instagram_username, settings.instagram_password)
            cl.get_timeline_feed()
            logger.info("Session locale chargée depuis %s", session_file)
            return cl
        except Exception as exc:
            logger.warning("Session locale invalide (%s) — reconnexion.", exc)

    # ── Cas 3 : login fresh ──────────────────────────────────────────────────
    logger.info("Connexion à Instagram en tant que @%s", settings.instagram_username)
    cl.login(settings.instagram_username, settings.instagram_password)
    cl.dump_settings(session_file)
    logger.info("Session sauvegardée dans %s", session_file)
    return cl


def _post_story(cl, image_path: Path, content: PostContent) -> None:
    """
    Publie la slide FR en Story juste après le carousel.
    Non bloquant : un échec ici ne stoppe pas le pipeline.
    """
    try:
        delay = random.uniform(10, 25)
        logger.info("Story : attente %.0fs avant publication…", delay)
        time.sleep(delay)
        cl.photo_upload_to_story(path=str(image_path))
        logger.info("Story publiée avec succès.")
    except Exception as exc:
        logger.warning("Story non publiée (non bloquant) : %s", exc)


def _post_first_comment(cl, media_id: str, content: PostContent) -> None:
    """
    Poste un premier commentaire pour stimuler l'engagement.
    Posté 15-30s après la publication pour paraître organique.
    """
    try:
        delay = random.uniform(15, 30)
        logger.info("Commentaire : attente %.0fs…", delay)
        time.sleep(delay)
        comment = (
            f"Swipe pour lire la version EN >> "
            f"Slide to read the FR version \u2764\ufe0f\u200d\U0001f525 "
            f"| Sauvegarde ce post si \u00e7a t\u2019a parl\u00e9 ! "
            f"Save this if it resonated with you!"
        )
        cl.media_comment(media_id, comment)
        logger.info("Premier commentaire post\u00e9.")
    except Exception as exc:
        logger.warning("Commentaire non post\u00e9 (non bloquant) : %s", exc)


def upload_post(image_paths: list[Path], content: PostContent, audio: AudioTrack) -> str:
    """
    Publie un carousel (album) sur Instagram, puis une Story + premier commentaire.

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

            # Story automatique (slide FR)
            _post_story(cl, image_paths[0], content)

            # Premier commentaire
            _post_first_comment(cl, media_id, content)

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
