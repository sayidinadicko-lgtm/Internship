"""
Bilingual post content generation via Groq API (free tier).

One API call generates French + English content simultaneously,
ensuring thematic and tonal coherence between both languages.
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
    quote_fr: str
    quote_en: str
    caption_fr: str
    caption_en: str
    cta_fr: str  # call-to-action
    cta_en: str


_SLOT_CONTEXT = {
    "morning": {
        "fr": "matin (énergie, lancement de la journée, ambition du réveil)",
        "en": "morning (energy, day-launch, wake-up ambition)",
    },
    "midday": {
        "fr": "midi (relance de l'élan, focus, reprendre le cap)",
        "en": "midday (momentum reboot, focus, getting back on track)",
    },
    "evening": {
        "fr": "soir (réflexion, bilan, recharge pour demain)",
        "en": "evening (reflection, self-assessment, recharging for tomorrow)",
    },
}

_SYSTEM_PROMPT = """
Tu es le créateur de contenu du compte Instagram @ledeclicmental — un compte de motivation en français et en anglais.

La voix de la marque est :
- Directe, chaleureuse, sans faux positif
- Orientée action concrète, pas de vœux pieux
- Inclusive, accessible à tous les âges
- Inspirante mais réaliste

Tu génères des posts Instagram bilingues (français + anglais) sur des thèmes de motivation et développement personnel.

Format de réponse OBLIGATOIRE : JSON valide uniquement, sans markdown ni backticks.
""".strip()


def generate_post(topic: Topic, slot: str) -> PostContent:
    """
    Call Groq (Llama 3.3 70B) to generate a bilingual Instagram post.

    Returns a PostContent dataclass with all text fields populated.
    """
    slot_ctx = _SLOT_CONTEXT.get(slot, _SLOT_CONTEXT["morning"])

    user_prompt = f"""
Génère un post Instagram bilingue pour le compte @ledeclicmental.

Thème du jour : "{topic.keyword_fr}" / "{topic.keyword_en}"
Moment de publication : {slot_ctx["fr"]} / {slot_ctx["en"]}

Le post doit comporter :
- Une citation courte et percutante (max 15 mots) en français
- La même citation en anglais
- Une légende engageante en français (3-4 phrases, ton direct et motivant)
- La même légende en anglais (traduction naturelle, pas littérale)
- Un call-to-action en français (1 phrase qui invite à commenter ou partager)
- Le même call-to-action en anglais

Réponds UNIQUEMENT avec ce JSON (aucun texte avant ou après) :
{{
  "quote_fr": "...",
  "quote_en": "...",
  "caption_fr": "...",
  "caption_en": "...",
  "cta_fr": "...",
  "cta_en": "..."
}}
""".strip()

    logger.info("Calling Groq for topic='%s' slot='%s'", topic.keyword_fr, slot)

    response = _get_client().chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if the model adds them despite instructions
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
        quote_fr=data["quote_fr"],
        quote_en=data["quote_en"],
        caption_fr=data["caption_fr"],
        caption_en=data["caption_en"],
        cta_fr=data["cta_fr"],
        cta_en=data["cta_en"],
    )

    logger.info("Content generated — quote_fr: '%s'", post.quote_fr)
    return post
