"""
Bilingual post content generation via Groq API.

Retranscribes real, well-known fables and tales (FR + EN) with their moral.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from groq import Groq

from ledeclicmental.config import settings
from ledeclicmental.content.stories import Story
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
    story_title: str
    story_source: str
    slot: str

    quote_fr: str
    quote_en: str
    moral_fr: str
    moral_en: str
    caption_fr: str
    caption_en: str
    cta_fr: str
    cta_en: str


_SYSTEM_PROMPT = """
Tu es un conteur pour le compte Instagram @ledeclicmental.

Tu retranscris fidèlement de vraies fables et contes célèbres (Ésope, La Fontaine, Bible, Mille et une Nuits, mythologie, contes zen...).
Tu respectes l'esprit et les personnages de l'histoire originale, mais tu l'écris dans un style fluide, poétique et engageant pour Instagram.

Format de réponse OBLIGATOIRE : JSON valide uniquement, sans markdown ni backticks.
""".strip()


def generate_post(story: Story, slot: str) -> PostContent:
    user_prompt = f"""
Retranscris cette histoire célèbre pour le compte Instagram @ledeclicmental.

Histoire : "{story.title_fr}" ({story.source})

Écris le récit en français (70 à 100 mots) :
- Fidèle à l'histoire originale (personnages, situation, retournement)
- Style fluide, poétique, agréable à lire
- Le récit s'arrête à la fin de l'histoire — sans morale dans le texte

La morale est dans le champ "moral_fr" : 1 phrase percutante tirée de l'histoire originale, sans préfixe "Morale :".

Puis :
- Même récit en anglais (traduction naturelle et littéraire)
- Morale en anglais (sans préfixe "Morale :")
- Légende Instagram en français (3-4 phrases engageantes, mentionne le titre et la source)
- Même légende en anglais
- Call-to-action en français (invite à commenter ou partager)
- Même call-to-action en anglais

Réponds UNIQUEMENT avec ce JSON :
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

    logger.info("Calling Groq for story='%s' (%s)", story.title_fr, story.source)

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

    def _clean(text: str) -> str:
        return re.sub(r"^morale\s*:\s*", "", text, flags=re.IGNORECASE).strip()

    post = PostContent(
        story_title=story.title_fr,
        story_source=story.source,
        slot=slot,
        quote_fr=data["story_fr"],
        quote_en=data["story_en"],
        moral_fr=_clean(data["moral_fr"]),
        moral_en=_clean(data["moral_en"]),
        caption_fr=data["caption_fr"],
        caption_en=data["caption_en"],
        cta_fr=data["cta_fr"],
        cta_en=data["cta_en"],
    )

    logger.info("Histoire retranscrite : '%s'", post.story_title)
    return post
