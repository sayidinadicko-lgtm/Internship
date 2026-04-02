"""
Main scheduler — orchestrates the 3-posts/day pipeline.

Each job:
  1. Gets today's trending topic
  2. Generates bilingual content via Claude
  3. Gets audio recommendation
  4. Renders the image
  5. Uploads to Instagram
  6. Records in post history
"""
from __future__ import annotations

from ledeclicmental.config import settings
from ledeclicmental.utils.logger import get_logger

logger = get_logger(__name__)

# Slot labels correspond to POST_TIMES order: morning, midday, evening
_SLOT_NAMES = ["morning", "midday", "evening"]


def run_post_job(slot: str) -> None:
    """Full pipeline for one post. Wrapped in broad try/except so scheduler stays alive."""
    logger.info("═══ Starting post job — slot=%s ═══", slot)
    try:
        from ledeclicmental.topics.trending import get_daily_topic
        from ledeclicmental.content.generator import generate_post
        from ledeclicmental.content.audio import get_recommendation
        from ledeclicmental.image.renderer import render_post
        from ledeclicmental.instagram.poster import upload_post
        from ledeclicmental.utils.history import record_post

        # Step 1: Topic
        topic = get_daily_topic()
        logger.info("Topic: %s / %s [%s]", topic.keyword_fr, topic.keyword_en, topic.source)

        # Step 2: Bilingual content
        content = generate_post(topic, slot)

        # Step 3: Audio recommendation
        audio = get_recommendation(slot)
        logger.info("Audio: %s – %s (%s BPM)", audio.title, audio.artist, audio.bpm)

        # Step 4: Render image
        image_path = render_post(content)

        # Step 5: Upload
        media_id = upload_post(image_path, content, audio)

        # Step 6: Record
        record_post(
            slot=slot,
            topic_fr=topic.keyword_fr,
            topic_en=topic.keyword_en,
            quote_fr=content.quote_fr,
            media_id=media_id,
        )

        logger.info("═══ Job complete — slot=%s  media_id=%s ═══", slot, media_id)

    except Exception as exc:
        logger.exception("Job failed for slot=%s: %s", slot, exc)
        # Do NOT re-raise — keeps APScheduler running for the next job


def start_scheduler() -> None:
    """Register 3 daily cron jobs and start the blocking scheduler."""
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler  # type: ignore
        from apscheduler.triggers.cron import CronTrigger  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "APScheduler not installed. Run: pip install APScheduler"
        ) from exc

    scheduler = BlockingScheduler(timezone=settings.timezone)

    post_times = settings.post_times
    if len(post_times) != 3:
        logger.warning(
            "Expected 3 post times, got %d. Slot names may not align.", len(post_times)
        )

    for i, (hour, minute) in enumerate(post_times):
        slot = _SLOT_NAMES[i] if i < len(_SLOT_NAMES) else f"slot_{i}"
        scheduler.add_job(
            run_post_job,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=settings.timezone),
            args=[slot],
            id=f"post_{slot}",
            name=f"@ledeclicmental post [{slot}] at {hour:02d}:{minute:02d}",
            misfire_grace_time=300,  # 5-minute grace window
        )
        logger.info(
            "Scheduled job: slot=%s at %02d:%02d %s",
            slot, hour, minute, settings.timezone,
        )

    logger.info(
        "Scheduler starting — 3 posts/day for @ledeclicmental (%s)", settings.timezone
    )

    if settings.dry_run:
        logger.warning("DRY_RUN=true — posts will be simulated, NOT uploaded.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user.")
