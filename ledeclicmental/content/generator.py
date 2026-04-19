"""
Bilingual post content generation via Groq API.

Generates short fables / contes (FR + EN) with a moral, in the style of La Fontaine / Aesop.
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
Tu es un conteur talentueux pour le compte Instagram @ledeclicmental — un compte de motivation en français et en anglais.

Tu écris de courtes fables, contes ou histoires imaginaires dans le style de La Fontaine, Esope ou les contes orientaux.
Chaque histoire doit :
- Avoir des personnages vivants (animaux, héros, sages, enfants, voyageurs...)
- Créer une vraie tension narrative avec un retournement ou une révélation
- Être poétique, imageée, agréable à lire
- Porter une leçon de vie profonde sans être moralisatrice
- Donner envie de relire et de partager

La voix est chaleureuse, littéraire mais accessible, jamais froide ni générique.

Format de réponse OBLIGATOIRE : JSON valide uniquement, sans markdown ni backticks.
""".strip()


def generate_post(topic: Topic, slot: str) -> PostContent:
    user_prompt = f"""
Écris un post Instagram bilingue pour le compte @ledeclicmental.

Thème du jour : "{topic.keyword_fr}" / "{topic.keyword_en}"

Écris une fable, un conte ou une histoire imaginaire courte en français (70 à 100 mots) avec :
- Un ou plusieurs personnages attachants (animal, enfant, sage, voyageur, artisan...)
- Une situation de départ claire
- Un retournement ou une révélation qui surprend et inspire
- Un style poétique et imageé, agréable à lire à voix haute
- Une morale finale courte et frappante (1 phrase, commence par "Morale :")

Puis :
- Traduis l'histoire en anglais (traduction littéraire naturelle)
- Traduis la morale en anglais
- Écris une légende Instagram en français (3-4 phrases engageantes)
- La même légende en anglais
- Un call-to-action en français (invite à commenter ou partager)
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
