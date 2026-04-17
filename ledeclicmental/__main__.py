"""
Point d'entrée — Le Déclic Mental.

Usage :
  python -m ledeclicmental          → génère 3 posts sur le Bureau
"""
from __future__ import annotations


def main() -> None:
    from ledeclicmental.runner import generate_daily_posts
    generate_daily_posts()


if __name__ == "__main__":
    main()
