"""Catalogue de vraies fables et contes célèbres à utiliser comme source."""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date

from ledeclicmental.utils.history import was_topic_used_recently
from ledeclicmental.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Story:
    title_fr: str
    title_en: str
    source: str


_STORIES: list[Story] = [
    Story("La Cigale et la Fourmi", "The Grasshopper and the Ant", "La Fontaine"),
    Story("Le Lièvre et la Tortue", "The Tortoise and the Hare", "Ésope"),
    Story("Le Corbeau et le Renard", "The Fox and the Crow", "La Fontaine"),
    Story("Le Lion et la Souris", "The Lion and the Mouse", "Ésope"),
    Story("Le Berger qui criait au loup", "The Boy Who Cried Wolf", "Ésope"),
    Story("Le Chêne et le Roseau", "The Oak and the Reed", "La Fontaine"),
    Story("La Laitière et le Pot au lait", "The Milkmaid and Her Pail", "La Fontaine"),
    Story("L'Enfant prodigue", "The Prodigal Son", "Bible — Luc 15"),
    Story("Le Bon Samaritain", "The Good Samaritan", "Bible — Luc 10"),
    Story("Les Aveugles et l'Éléphant", "The Blind Men and the Elephant", "Parabole indienne"),
    Story("Les Deux Loups", "The Two Wolves", "Légende Cherokee"),
    Story("Le Vase fissuré", "The Cracked Pot", "Parabole indienne"),
    Story("Le Tailleur de pierres", "The Stonecutter", "Conte japonais"),
    Story("Le Bambou chinois", "The Chinese Bamboo", "Sagesse chinoise"),
    Story("Nasreddin et l'âne", "Nasreddin and the Donkey", "Conte soufi"),
    Story("Le Pêcheur et le Génie", "The Fisherman and the Genie", "Mille et une nuits"),
    Story("Le Petit Prince et le Renard", "The Little Prince and the Fox", "Antoine de Saint-Exupéry"),
    Story("Le Petit Prince et la Rose", "The Little Prince and the Rose", "Antoine de Saint-Exupéry"),
    Story("Sisyphe et son rocher", "Sisyphus and His Boulder", "Mythologie grecque"),
    Story("Icare et le soleil", "Icarus and the Sun", "Mythologie grecque"),
    Story("Le Roi Midas", "King Midas", "Mythologie grecque"),
    Story("Le Renard et la Cigogne", "The Fox and the Stork", "Ésope"),
    Story("Le Loup et l'Agneau", "The Wolf and the Lamb", "La Fontaine"),
    Story("Le Rat des villes et le Rat des champs", "The Town Mouse and the Country Mouse", "La Fontaine"),
    Story("Le Laboureur et ses enfants", "The Farmer and His Sons", "La Fontaine"),
    Story("Alexandre et Diogène", "Alexander and Diogenes", "Philosophie grecque"),
    Story("La Tasse de thé", "The Cup of Tea", "Conte zen"),
    Story("Androcles et le Lion", "Androcles and the Lion", "Conte romain"),
    Story("Le Chien et son reflet", "The Dog and His Reflection", "Ésope"),
    Story("La Grenouille et le Bœuf", "The Frog and the Ox", "La Fontaine"),
    Story("Le Meunier, son fils et l'âne", "The Miller, His Son and the Donkey", "La Fontaine"),
    Story("Le Pot de terre et le Pot de fer", "The Earthen Pot and the Iron Pot", "La Fontaine"),
    Story("L'Éléphant enchaîné", "The Chained Elephant", "Parabole bouddhiste"),
    Story("Le Maître zen et la tasse pleine", "The Zen Master and the Full Cup", "Conte zen"),
    Story("La Flèche et le Roseau", "The Arrow and the Reed", "Rumi"),
    Story("Le Marchand et le Perroquet", "The Merchant and the Parrot", "Rumi"),
    Story("Le Roi et le Faucon", "The King and the Falcon", "Contes persans"),
    Story("Salomon et les deux mères", "Solomon and the Two Mothers", "Bible — 1 Rois 3"),
    Story("David et Goliath", "David and Goliath", "Bible — 1 Samuel 17"),
    Story("La Tour de Babel", "The Tower of Babel", "Bible — Genèse 11"),
]


def get_multiple_stories(n: int = 3) -> list[Story]:
    """Retourne n histoires différentes, pas répétées avant 120 jours."""
    today = date.today()
    used: set[str] = set()
    result: list[Story] = []

    rng = random.Random(today.toordinal())
    pool = list(_STORIES)
    rng.shuffle(pool)

    for story in pool:
        if len(result) >= n:
            break
        if story.title_fr.lower() in used:
            continue
        if was_topic_used_recently(story.title_fr, days=120):
            continue
        result.append(story)
        used.add(story.title_fr.lower())

    if len(result) < n:
        rng2 = random.Random(today.toordinal() + 999)
        pool2 = [s for s in _STORIES if s.title_fr.lower() not in used]
        rng2.shuffle(pool2)
        for story in pool2:
            if len(result) >= n:
                break
            result.append(story)
            used.add(story.title_fr.lower())

    logger.info("Histoires du jour : %s", [s.title_fr for s in result[:n]])
    return result[:n]
