"""
Audio recommendation for each post.

Instagram does not expose a public API for programmatic track selection.
This module embeds audio as metadata in the caption — a music mention
that guides the viewer and builds brand identity around specific tracks.

Tracks are mapped by mood: morning→energizing, midday→focused, evening→calm/uplifting.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date


@dataclass
class AudioTrack:
    title: str
    artist: str
    mood: str       # "energizing" | "focused" | "calm" | "uplifting"
    bpm: int
    caption_mention_fr: str  # French text for caption footer
    caption_mention_en: str  # English text for caption footer


_LIBRARY: list[AudioTrack] = [
    # ── Energizing (morning) ───────────────────────────────────────────────
    AudioTrack(
        "Unstoppable", "Sia",
        "energizing", 118,
        "🎵 Commence ta journée avec : Unstoppable – Sia",
        "🎵 Start your day with: Unstoppable – Sia",
    ),
    AudioTrack(
        "Eye of the Tiger", "Survivor",
        "energizing", 109,
        "🎵 L'énergie du matin : Eye of the Tiger – Survivor",
        "🎵 Morning energy: Eye of the Tiger – Survivor",
    ),
    AudioTrack(
        "Lose Yourself", "Eminem",
        "energizing", 171,
        "🎵 Pour te booster le matin : Lose Yourself – Eminem",
        "🎵 Boost your morning: Lose Yourself – Eminem",
    ),
    AudioTrack(
        "Hall of Fame", "The Script ft. will.i.am",
        "energizing", 120,
        "🎵 Rappelle-toi pourquoi tu te lèves : Hall of Fame – The Script",
        "🎵 Remember why you rise: Hall of Fame – The Script",
    ),
    AudioTrack(
        "Stronger", "Kanye West",
        "energizing", 104,
        "🎵 Ce qui ne te tue pas te rend plus fort : Stronger – Kanye West",
        "🎵 What doesn't kill you: Stronger – Kanye West",
    ),
    AudioTrack(
        "Fighter", "Christina Aguilera",
        "energizing", 130,
        "🎵 Tu es plus fort(e) que tu ne le crois : Fighter – Christina Aguilera",
        "🎵 You are stronger than you think: Fighter – Christina Aguilera",
    ),
    AudioTrack(
        "Roar", "Katy Perry",
        "energizing", 179,
        "🎵 Fais entendre ta voix ce matin : Roar – Katy Perry",
        "🎵 Let your voice be heard today: Roar – Katy Perry",
    ),

    # ── Focused (midday) ───────────────────────────────────────────────────
    AudioTrack(
        "Burn", "Ellie Goulding",
        "focused", 126,
        "🎵 Retrouve ton élan : Burn – Ellie Goulding",
        "🎵 Reclaim your momentum: Burn – Ellie Goulding",
    ),
    AudioTrack(
        "Work", "Rihanna",
        "focused", 93,
        "🎵 Le focus, c'est maintenant : Work – Rihanna",
        "🎵 Focus mode: ON – Work – Rihanna",
    ),
    AudioTrack(
        "Run the World", "Beyoncé",
        "focused", 128,
        "🎵 Tu mènes la danse : Run the World – Beyoncé",
        "🎵 You're in charge: Run the World – Beyoncé",
    ),
    AudioTrack(
        "Rise", "Katy Perry",
        "focused", 103,
        "🎵 Redresse-toi et avance : Rise – Katy Perry",
        "🎵 Stand up and move forward: Rise – Katy Perry",
    ),
    AudioTrack(
        "Not Afraid", "Eminem",
        "focused", 100,
        "🎵 Reprends le cap de l'après-midi : Not Afraid – Eminem",
        "🎵 Get back on track: Not Afraid – Eminem",
    ),

    # ── Calm / Uplifting (evening) ─────────────────────────────────────────
    AudioTrack(
        "Weightless", "Marconi Union",
        "calm", 60,
        "🎵 Décompresse ce soir : Weightless – Marconi Union",
        "🎵 Unwind tonight: Weightless – Marconi Union",
    ),
    AudioTrack(
        "Fix You", "Coldplay",
        "calm", 138,
        "🎵 Prends soin de toi ce soir : Fix You – Coldplay",
        "🎵 Take care of yourself tonight: Fix You – Coldplay",
    ),
    AudioTrack(
        "A Sky Full of Stars", "Coldplay",
        "uplifting", 125,
        "🎵 Termine en beauté : A Sky Full of Stars – Coldplay",
        "🎵 End on a high note: A Sky Full of Stars – Coldplay",
    ),
    AudioTrack(
        "Beautiful Day", "U2",
        "uplifting", 136,
        "🎵 C'était une belle journée : Beautiful Day – U2",
        "🎵 It was a beautiful day: Beautiful Day – U2",
    ),
    AudioTrack(
        "Don't Stop Me Now", "Queen",
        "uplifting", 157,
        "🎵 La journée n'est pas finie ! Don't Stop Me Now – Queen",
        "🎵 The day isn't over yet! Don't Stop Me Now – Queen",
    ),
    AudioTrack(
        "Count on Me", "Bruno Mars",
        "calm", 114,
        "🎵 Pour se rappeler ce qui compte : Count on Me – Bruno Mars",
        "🎵 Remember what matters: Count on Me – Bruno Mars",
    ),
]

_SLOT_MOODS: dict[str, list[str]] = {
    "morning": ["energizing"],
    "midday": ["focused"],
    "evening": ["calm", "uplifting"],
}


def get_recommendation(slot: str) -> AudioTrack:
    """
    Return a track recommendation seeded by today's date + slot
    (deterministic within a day, varies across days).
    """
    moods = _SLOT_MOODS.get(slot, ["energizing"])
    candidates = [t for t in _LIBRARY if t.mood in moods]
    if not candidates:
        candidates = _LIBRARY

    seed = f"{date.today().isoformat()}-{slot}-audio"
    rng = random.Random(seed)
    return rng.choice(candidates)
