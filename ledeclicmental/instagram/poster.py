"""
Instagram posting via instagrapi.

Features:
- Session persistence (avoids repeated logins / security challenges)
- 3-attempt retry with 60-second back-off on transient errors
- Randomised pre-upload delay (30–90s) to mimic human behaviour
- DRY_RUN mode (skip actual upload)
- Full caption assembly: FR + EN + hashtags + audio mention
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
_RETRY_BACKOFF = 60  # seconds between retries


def _build_caption(content: PostContent, audio: AudioTrack) -> str:
    """
    Assemble the full Instagram caption.

    Structure:
      [French caption + CTA]

      [English caption + CTA]

      .
      .
      .
      [30 hashtags]

      [Audio mention FR / EN]
    """
    fr_block = f"{content.caption_fr}\n\n{content.cta_fr}"
    en_block = f"{content.caption_en}\n\n{content.cta_en}"

    tags = get_hashtags(content.topic.keyword_fr, content.slot)
    hashtag_line = format_hashtags(tags)

    audio_line = f"{audio.caption_mention_fr}\n{audio.caption_mention_en}"

    caption = (
        f"{fr_block}\n\n"
        f"──────────────\n\n"
        f"{en_block}\n\n"
        f".\n.\n.\n\n"
        f"{hashtag_line}\n\n"
        f"{audio_line}"
    )
    return caption


def _get_client():
    """Lazy-load instagrapi client with session persistence."""
    try:
        from instagrapi import Client  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "instagrapi is not installed. Run: pip install instagrapi"
        ) from exc

    cl = Client()
    session_file: Path = settings.instagram_session_file
    session_file.parent.mkdir(parents=True, exist_ok=True)

    if session_file.exists():
        try:
            cl.load_settings(session_file)
            cl.login(settings.instagram_username, settings.instagram_password)
            cl.get_timeline_feed()  # validate session
            logger.info("Instagram session loaded from %s", session_file)
            return cl
        except Exception as exc:
            logger.warning("Saved session invalid (%s) — re-logging in.", exc)

    # Fresh login
    logger.info("Logging in to Instagram as @%s", settings.instagram_username)
    cl.login(settings.instagram_username, settings.instagram_password)
    cl.dump_settings(session_file)
    logger.info("Session saved to %s", session_file)
    return cl


def upload_post(image_path: Path, content: PostContent, audio: AudioTrack) -> str:
    """
    Upload a photo post to Instagram.

    Returns the media ID (empty string in DRY_RUN mode).
    """
    caption = _build_caption(content, audio)

    if settings.dry_run:
        logger.info("[DRY RUN] Would post image: %s", image_path)
        logger.info("[DRY RUN] Caption preview (first 300 chars):\n%s", caption[:300])
        return "DRY_RUN_MEDIA_ID"

    # Human-like delay before posting
    delay = random.uniform(30, 90)
    logger.info("Waiting %.0f seconds before upload (anti-bot delay)…", delay)
    time.sleep(delay)

    cl = _get_client()

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            media = cl.photo_upload(
                path=str(image_path),
                caption=caption,
            )
            media_id = str(media.id)
            logger.info("Posted successfully — media_id=%s", media_id)
            return media_id
        except Exception as exc:
            logger.error("Upload attempt %d/%d failed: %s", attempt, _MAX_RETRIES, exc)
            if attempt < _MAX_RETRIES:
                logger.info("Retrying in %d seconds…", _RETRY_BACKOFF)
                time.sleep(_RETRY_BACKOFF)
            else:
                raise RuntimeError(f"Instagram upload failed after {_MAX_RETRIES} attempts") from exc

    return ""  # unreachable but satisfies type checkers
