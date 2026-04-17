"""
Trending motivation topic discovery.

Strategy:
  1. Query Google Trends (pytrends) for FR region with motivation seed keywords.
  2. Fallback to curated evergreen list if Trends is rate-limited or empty.
  3. Cache today's result in post_history check to avoid redundant API calls.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date

from ledeclicmental.utils.logger import get_logger
from ledeclicmental.utils.history import was_topic_used_recently

logger = get_logger(__name__)

# ── Bilingual topic pairs (fr, en) ───────────────────────────────────────────
_CURATED: list[tuple[str, str]] = [
    ("résilience", "resilience"),
    ("discipline", "discipline"),
    ("confiance en soi", "self-confidence"),
    ("courage", "courage"),
    ("persévérance", "perseverance"),
    ("dépassement de soi", "self-improvement"),
    ("état d'esprit de croissance", "growth mindset"),
    ("objectifs", "goals"),
    ("succès", "success"),
    ("focus", "focus"),
    ("habitudes", "habits"),
    ("action", "action"),
    ("ingratitude", "gratitude"),
    ("énergie positive", "positive energy"),
    ("leadership", "leadership"),
    ("prise de décision", "decision-making"),
    ("gestion du temps", "time management"),
    ("bien-être mental", "mental well-being"),
    ("sortir de sa zone de confort", "leaving comfort zone"),
    ("vision", "vision"),
    ("ambition", "ambition"),
    ("travail acharné", "hard work"),
    ("réussite", "achievement"),
    ("mindfulness", "mindfulness"),
    ("équilibre vie pro-perso", "work-life balance"),
    ("apprentissage continu", "continuous learning"),
    ("confiance", "trust"),
    ("forces intérieures", "inner strength"),
    ("optimisme", "optimism"),
    ("changement", "change"),
    ("transformation", "transformation"),
    ("calme intérieur", "inner calm"),
    ("écoute de soi", "self-awareness"),
    ("responsabilité", "accountability"),
    ("passion", "passion"),
    ("créativité", "creativity"),
    ("gratitude", "gratitude"),
    ("détermination", "determination"),
    ("peur et dépassement", "overcoming fear"),
    ("lâcher prise", "letting go"),
]

# Seed keywords for pytrends (FR region)
_TREND_SEEDS = [
    "motivation",
    "développement personnel",
    "mindset",
    "bien-être",
    "succès",
]

# Daily cache: {date_str -> (fr, en)}
_daily_cache: dict[str, tuple[str, str]] = {}


@dataclass
class Topic:
    keyword_fr: str
    keyword_en: str
    source: str  # "trends" | "curated"


def _fetch_from_trends() -> tuple[str, str] | None:
    """Try Google Trends for a rising motivation keyword."""
    try:
        from pytrends.request import TrendReq  # type: ignore

        pt = TrendReq(hl="fr-FR", tz=60, timeout=(10, 25))
        seed = random.choice(_TREND_SEEDS)
        pt.build_payload([seed], cat=0, timeframe="now 1-d", geo="FR")
        related = pt.related_queries()
        rising = related.get(seed, {}).get("rising")
        if rising is not None and not rising.empty:
            keyword_fr = rising.iloc[0]["query"]
            # Simple heuristic: use the same word for EN (Claude will refine)
            keyword_en = keyword_fr
            logger.info("Trends returned keyword: '%s'", keyword_fr)
            return keyword_fr, keyword_en
    except Exception as exc:
        logger.warning("pytrends failed (%s), using curated fallback.", exc)
    return None


def _pick_curated(today: date) -> tuple[str, str]:
    """Pick a curated topic that hasn't been used recently."""
    # Shuffle deterministically by date so morning/midday/evening share the same topic
    rng = random.Random(today.toordinal())
    pool = list(_CURATED)
    rng.shuffle(pool)
    for fr, en in pool:
        if not was_topic_used_recently(fr, days=14):
            return fr, en
    # All used recently — just pick the first deterministic one
    return pool[0]


def get_multiple_topics(n: int = 3) -> list[Topic]:
    """
    Retourne n sujets différents, aucun utilisé dans les 120 derniers jours.
    """
    today = date.today()
    topics: list[Topic] = []
    used_keywords: set[str] = set()

    # Essaie Google Trends pour le premier sujet
    result = _fetch_from_trends()
    if result:
        fr, en = result
        if not was_topic_used_recently(fr, days=120):
            topics.append(Topic(keyword_fr=fr, keyword_en=en, source="trends"))
            used_keywords.add(fr.lower())

    # Complète avec la liste curatée (ordre aléatoire basé sur la date)
    rng = random.Random(today.toordinal())
    pool = list(_CURATED)
    rng.shuffle(pool)

    for fr, en in pool:
        if len(topics) >= n:
            break
        if fr.lower() in used_keywords:
            continue
        if was_topic_used_recently(fr, days=120):
            continue
        topics.append(Topic(keyword_fr=fr, keyword_en=en, source="curated"))
        used_keywords.add(fr.lower())

    # Fallback si tout a été utilisé récemment
    if len(topics) < n:
        rng2 = random.Random(today.toordinal() + 999)
        pool2 = [p for p in _CURATED if p[0].lower() not in used_keywords]
        rng2.shuffle(pool2)
        for fr, en in pool2:
            if len(topics) >= n:
                break
            topics.append(Topic(keyword_fr=fr, keyword_en=en, source="curated"))
            used_keywords.add(fr.lower())

    logger.info("Topics selectionnes : %s", [t.keyword_fr for t in topics[:n]])
    return topics[:n]


def get_daily_topic() -> Topic:
    """
    Return today's motivation topic.
    Same result for repeated calls on the same date (cached in memory).
    """
    today = date.today()
    key = today.isoformat()

    if key in _daily_cache:
        fr, en = _daily_cache[key]
        return Topic(keyword_fr=fr, keyword_en=en, source="cache")

    # Try Trends first
    result = _fetch_from_trends()
    source = "trends"

    if result is None:
        result = _pick_curated(today)
        source = "curated"

    fr, en = result
    _daily_cache[key] = (fr, en)
    logger.info("Today's topic [%s]: FR='%s' / EN='%s'", source, fr, en)
    return Topic(keyword_fr=fr, keyword_en=en, source=source)
