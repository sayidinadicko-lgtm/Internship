"""Post history — deduplication and audit trail."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ledeclicmental.config import settings
from ledeclicmental.utils.logger import get_logger

logger = get_logger(__name__)


def _load() -> list[dict[str, Any]]:
    path: Path = settings.post_history_file
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.warning("Could not parse post_history.json — starting fresh.")
        return []


def _save(records: list[dict[str, Any]]) -> None:
    path: Path = settings.post_history_file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def was_slot_posted_today(slot: str) -> bool:
    """Retourne True si ce slot a déjà été publié aujourd'hui (UTC)."""
    today = datetime.utcnow().date().isoformat()
    for record in _load():
        posted_date = record.get("posted_at", "")[:10]
        if posted_date == today and record.get("slot") == slot:
            return True
    return False


def was_topic_used_recently(keyword_fr: str, days: int = 14) -> bool:
    cutoff = datetime.utcnow() - timedelta(days=days)
    for record in _load():
        posted_at = datetime.fromisoformat(record.get("posted_at", "2000-01-01"))
        if posted_at > cutoff and record.get("topic_fr", "").lower() == keyword_fr.lower():
            return True
    return False


def record_post(
    slot: str,
    topic_fr: str,
    topic_en: str,
    quote_fr: str,
    media_id: str = "",
) -> str:
    records = _load()
    entry = {
        "id": str(uuid.uuid4()),
        "posted_at": datetime.utcnow().isoformat(timespec="seconds"),
        "slot": slot,
        "topic_fr": topic_fr,
        "topic_en": topic_en,
        "quote_fr": quote_fr,
        "instagram_media_id": media_id,
    }
    records.append(entry)
    _save(records)
    logger.debug("Recorded post %s for topic '%s'", entry["id"], topic_fr)
    return entry["id"]


def record_topic_used(keyword_fr: str) -> None:
    """Enregistre qu'un sujet a été utilisé aujourd'hui (anti-répétition 120j)."""
    records = _load()
    records.append({
        "id": str(uuid.uuid4()),
        "posted_at": datetime.utcnow().isoformat(timespec="seconds"),
        "topic_fr": keyword_fr,
    })
    _save(records)
    logger.debug("Sujet enregistre : '%s'", keyword_fr)
