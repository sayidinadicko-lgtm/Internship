"""
Point d'entrée du bot @ledeclicmental.

Modes :
  python -m ledeclicmental               -> scheduler continu (3x/jour)
  python -m ledeclicmental --post-now    -> 1 post immédiat (slot auto selon heure)
  python -m ledeclicmental --slot morning|midday|evening -> 1 post immédiat (slot forcé)
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
    args = parser.parse_args()

    if args.post_now or args.slot:
        from ledeclicmental.scheduler import run_post_job
        slot = args.slot or _slot_from_utc_hour(datetime.now(timezone.utc).hour)
        run_post_job(slot)
    else:
        from ledeclicmental.scheduler import start_scheduler
        start_scheduler()


if __name__ == "__main__":
    main()
