"""
Bilingual post content generation via Groq API (free tier).

Generates short motivational stories (FR + EN) with a moral at the end.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from groq import Groq

from ledeclicmental.config import settings
from ledeclicmental.topics.trending import Topic
from ledeclicmental.utils.logger import get_logger

logger = get_logger(__name__)

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


@dataclass
class PostContent:
    topic: Topic
    slot: str  # "morning" | "midday" | "evening"

    # Bilingual content
    quote_fr: str   # histoire en français
    quote_en: str   # histoire en anglais
    moral_fr: str   # morale en français
    moral_en: str   # morale en anglais
    caption_fr: str
    caption_en: str
    cta_fr: str
    cta_en: str


_SYSTEM_PROMPT = """
Tu es le créateur de contenu du compte Instagram @ledeclicmental — un compte de motivation en français et en anglais.

La voix de la marque est :
- Directe, chaleureuse, sans faux positif
- Orientée action concrète, pas de vœux pieux
- Inclusive, accessible à tous les âges
- Inspirante mais réaliste

Tu génères des posts Instagram bilingues (français + anglais) sous forme de courtes histoires motivantes.

Format de réponse OBLIGATOIRE : JSON valide uniquement, sans markdown ni backticks.
""".strip()


def generate_post(topic: Topic, slot: str) -> PostContent:
    user_prompt = f"""
Génère un post Instagram bilingue pour le compte @ledeclicmental.

Thème du jour : "{topic.keyword_fr}" / "{topic.keyword_en}"

Le post doit comporter :
- Une courte histoire motivante en français (60 à 80 mots, 4-5 phrases) — une vraie mini-histoire avec un personnage, une situation et un retournement inspirant. Pas une liste, une vraie narration.
- La même histoire en anglais (traduction naturelle)
- La morale de l'histoire en français (1 phrase courte et percutante)
- La même morale en anglais
- Une légende Instagram engageante en français (3-4 phrases, ton direct)
- La même légende en anglais
- Un call-to-action en français (1 phrase qui invite à commenter ou partager)
- Le même call-to-action en anglais

Réponds UNIQUEMENT avec ce JSON (aucun texte avant ou après) :
{{
  "story_fr": "...",
  "story_en": "...",
  "moral_fr": "...",
  "moral_en": "...",
  "caption_fr": "...",
  "caption_en": "...",
  "cta_fr": "...",
  "cta_en": "..."
}}
""".strip()

    logger.info("Calling Groq for topic='%s' slot='%s'", topic.keyword_fr, slot)

    response = _get_client().chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1500,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Groq returned invalid JSON: %s\nRaw: %s", exc, raw)
        raise RuntimeError("Groq returned non-JSON content") from exc

    post = PostContent(
        topic=topic,
        slot=slot,
        quote_fr=data["story_fr"],
        quote_en=data["story_en"],
        moral_fr=data["moral_fr"],
        moral_en=data["moral_en"],
        caption_fr=data["caption_fr"],
        caption_en=data["caption_en"],
        cta_fr=data["cta_fr"],
        cta_en=data["cta_en"],
    )

    logger.info("Histoire générée — FR : '%s'", post.quote_fr[:60])
    return post
