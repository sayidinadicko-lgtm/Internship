"""
Bilingual hashtag strategy for @ledeclicmental.

Three tiers:
  Tier 1 — Brand tags (always included): 2 tags
  Tier 2 — Topic-specific tags: 8 tags
  Tier 3 — Rotated pool (seeded by date+slot): 20 tags

Total: 30 tags (Instagram maximum).
"""
from __future__ import annotations

import random
from datetime import date

# ── Tier 1: brand tags ───────────────────────────────────────────────────────
_BRAND_TAGS = [
    "#ledeclicmental",
    "#declicmental",
]

# ── Tier 2: topic keyword → specific tags ────────────────────────────────────
_TOPIC_TAGS: dict[str, list[str]] = {
    "résilience": ["#résilience", "#resilience", "#buildresilience", "#résilientemind",
                   "#rebondir", "#forceintérieure", "#mentalstrength", "#resilient"],
    "discipline": ["#discipline", "#selfdiscipline", "#autodiscipline", "#disciplinedlife",
                   "#disciplineequalsfreedom", "#consistency", "#régularité", "#constance"],
    "confiance en soi": ["#confianceensoi", "#selfconfidence", "#selfesteem", "#estime",
                         "#confiance", "#believeinyourself", "#croireensoi", "#confidence"],
    "courage": ["#courage", "#brave", "#bravoure", "#oser", "#daretobemore",
                "#bekind", "#courageouslife", "#osetravancer"],
    "persévérance": ["#persévérance", "#perseverance", "#nevergiveup", "#nuncteabandones",
                     "#continuez", "#keepgoing", "#tenacity", "#ténacité"],
    "dépassement de soi": ["#dépassementdesoi", "#selfimprovement", "#bettereveryday",
                           "#progress", "#progressnotperfection", "#evolveyourself",
                           "#grandirchaquejour", "#levelup"],
    "état d'esprit de croissance": ["#growthmindset", "#mentalitédecroissance",
                                    "#growthmode", "#mindset", "#mindsetshift",
                                    "#croissance", "#evolve", "#mindsetmatters"],
    "objectifs": ["#objectifs", "#goals", "#goalsetting", "#fixeruneintention",
                  "#vision", "#visionclear", "#rêves", "#dreams"],
    "succès": ["#succès", "#success", "#reussite", "#winner", "#winning",
               "#successmindset", "#réussite", "#achieve"],
    "habitudes": ["#habitudes", "#habits", "#goodhabits", "#routinematin",
                  "#morningroutine", "#dailyhabits", "#habitudessaines", "#consistency"],
    "action": ["#action", "#passezàlaction", "#takeaction", "#agir",
               "#starttoday", "#doitnow", "#maintenant", "#now"],
    "gratitude": ["#gratitude", "#reconaissance", "#grateful", "#thankful",
                  "#blessings", "#comptervosbienfaits", "#gratefulness", "#beingthankful"],
    "focus": ["#focus", "#concentration", "#focusedmind", "#restercentré",
              "#deepwork", "#productivité", "#productivity", "#zenmode"],
    "vision": ["#vision", "#clarity", "#claretémentale", "#bigpicture",
               "#dreambig", "#visionclair", "#purposedriven", "#purpose"],
    "ambition": ["#ambition", "#ambitieux", "#ambitious", "#dream",
                 "#biggerthanme", "#aimhigh", "#viserhaut", "#nolimits"],
    "leadership": ["#leadership", "#leader", "#leadbyexample", "#mentorat",
                   "#mentor", "#inspirer", "#inspire", "#leadwithpurpose"],
    "mindfulness": ["#mindfulness", "#pleinconscience", "#méditation", "#meditation",
                    "#présence", "#presentmoment", "#breathe", "#paix"],
    "transformation": ["#transformation", "#changement", "#change", "#newme",
                       "#évolution", "#evolution", "#becomebetter", "#devenir"],
    "optimisme": ["#optimisme", "#optimism", "#positivity", "#positivité",
                  "#goodvibes", "#bonnesvibes", "#hopeful", "#espoir"],
}

# ── Tier 3: large bilingual rotation pool ───────────────────────────────────
_POOL: list[str] = [
    # French
    "#motivationdujour", "#developpementpersonnel", "#mentalité", "#épanouissement",
    "#bienetre", "#mieuxetre", "#croissancepersonnelle", "#inspirationdujour",
    "#positivité", "#philosophiedevie", "#travailsurtoi", "#restimoi",
    "#autrement", "#chaquejour", "#progresser", "#apprendre", "#grandirensemble",
    "#réflexion", "#introspection", "#selflove", "#amourpropre",
    # English
    "#dailymotivation", "#personaldevelopment", "#mentalhealthmatters", "#selfcare",
    "#mindsetcoach", "#lifecoach", "#motivationalquotes", "#inspirationalquotes",
    "#quoteoftheday", "#morningmotivation", "#successquotes", "#empowerment",
    "#strongertogether", "#positivethinking", "#mindfulnessmatters", "#wellbeing",
    "#selfgrowth", "#bethebestyou", "#liveyourbestlife", "#mindsetiseverything",
    "#growthanddevelopment", "#inspireyourself", "#elevate", "#getbetter",
    "#neversettle", "#gogetit", "#hustlesmarter", "#createyourlife",
]


def get_hashtags(topic_keyword_fr: str, slot: str) -> list[str]:
    """
    Return exactly 30 hashtags for the given topic and posting slot.
    Seeded by today's date + slot for determinism within a run.
    """
    tags: list[str] = list(_BRAND_TAGS)  # Tier 1

    # Tier 2 — topic-specific
    key = topic_keyword_fr.lower()
    tier2 = _TOPIC_TAGS.get(key)
    if tier2 is None:
        # Fuzzy fallback: match on partial keyword
        for k, v in _TOPIC_TAGS.items():
            if k in key or key in k:
                tier2 = v
                break
    if tier2 is None:
        tier2 = _TOPIC_TAGS["action"]  # safe default

    tags.extend(tier2[:8])

    # Tier 3 — rotate from pool
    seed = f"{date.today().isoformat()}-{slot}"
    rng = random.Random(seed)
    available = [t for t in _POOL if t not in tags]
    rng.shuffle(available)
    tags.extend(available[:30 - len(tags)])

    return tags[:30]


def format_hashtags(tags: list[str]) -> str:
    """Return hashtags as a single space-separated string."""
    return " ".join(tags)
