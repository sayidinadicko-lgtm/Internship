"""
Point d'entrée du bot @ledeclicmental.

Modes :
  python -m ledeclicmental               -> scheduler continu (3x/jour)
  python -m ledeclicmental --post-now    -> 1 post immédiat (slot auto selon heure)
  python -m ledeclicmental --slot morning|midday|evening -> 1 post immédiat (slot forcé)
  python -m ledeclicmental --catch-up    -> rattrape tous les slots manqués aujourd'hui
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone


def _slot_from_utc_hour(hour: int) -> str:
    """Détermine le slot selon l'heure UTC courante."""
    if 4 <= hour < 9:
        return "morning"
    elif 9 <= hour < 14:
        return "midday"
    else:
        return "evening"


def _catch_up() -> None:
    """
    Rattrape tous les slots non publiés aujourd'hui dont l'heure est passée.
    Utilise l'heure locale de la machine pour déterminer ce qui est manqué.
    """
    from ledeclicmental.scheduler import run_post_job
    from ledeclicmental.utils.history import was_slot_posted_today
    from ledeclicmental.utils.logger import get_logger

    logger = get_logger(__name__)

    # Heure locale de déclenchement de chaque slot (Paris)
    slot_trigger_hours = {
        "morning": 7,
        "midday": 12,
        "evening": 19,
    }

    now_hour = datetime.now().hour  # heure locale machine

    for slot, trigger_hour in slot_trigger_hours.items():
        if now_hour >= trigger_hour:
            if was_slot_posted_today(slot):
                logger.info("Slot '%s' déjà publié aujourd'hui — ignoré.", slot)
            else:
                logger.info("Rattrapage slot '%s' (heure dépassée, non publié).", slot)
                run_post_job(slot)
        else:
            logger.info("Slot '%s' pas encore dû (trigger à %dh).", slot, trigger_hour)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bot Instagram @ledeclicmental — 3 posts/jour bilingues FR/EN"
    )
    parser.add_argument(
        "--post-now",
        action="store_true",
        help="Publie un post immédiatement (slot déterminé par l'heure actuelle)",
    )
    parser.add_argument(
        "--slot",
        choices=["morning", "midday", "evening"],
        help="Slot à utiliser pour la publication (morning / midday / evening)",
    )
    parser.add_argument(
        "--catch-up",
        action="store_true",
        help="Rattrape tous les slots manqués aujourd'hui puis quitte",
    )
    args = parser.parse_args()

    if args.catch_up:
        _catch_up()
    elif args.post_now or args.slot:
        from ledeclicmental.scheduler import run_post_job
        slot = args.slot or _slot_from_utc_hour(datetime.now(timezone.utc).hour)
        run_post_job(slot)
    else:
        from ledeclicmental.scheduler import start_scheduler
        start_scheduler()


if __name__ == "__main__":
    main()
