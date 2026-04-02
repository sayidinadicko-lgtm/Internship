#!/usr/bin/env python3
"""
CV Optimizer – Point d'entrée principal.

Usage :
    python main.py [--source indeed|hellowork|all] [--max N] [--query "..."]

Variables d'environnement requises :
    ANTHROPIC_API_KEY : clé API Anthropic (dans .env)
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
import anthropic

from scrapers import scrape_indeed, scrape_hellowork
from cv_optimizer import optimize_cv, generate_cover_letter, build_cv_docx, build_cover_letter_docx, docx_to_pdf

load_dotenv()


def slugify(text: str) -> str:
    """Transforme un titre en nom de fichier valide."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text[:60]


def load_cv_data(path: str = "cv_data.json") -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def process_job(job: dict, cv_data: dict, client: anthropic.Anthropic, output_dir: Path):
    """Optimise le CV et génère la lettre de motivation pour une offre."""
    slug = slugify(f"{job['title']}_{job['company']}")
    print(f"\n{'='*60}")
    print(f"Traitement : {job['title']} – {job['company']}")
    print(f"Source : {job['source']} | Lieu : {job['location']}")
    print(f"{'='*60}")

    # 1. Optimiser le CV
    print("  → Optimisation du CV...")
    try:
        optimized = optimize_cv(cv_data, job, client)
    except Exception as e:
        print(f"  ✗ Erreur optimisation CV : {e}")
        return

    # 2. Générer la lettre de motivation
    print("  → Génération de la lettre de motivation...")
    try:
        letter = generate_cover_letter(cv_data, optimized, job, client)
    except Exception as e:
        print(f"  ✗ Erreur génération LM : {e}")
        letter = None

    # 3. Générer les fichiers .docx puis convertir en PDF
    cv_path = output_dir / f"CV_{slug}.docx"
    build_cv_docx(optimized, str(cv_path))
    print("  → Conversion CV en PDF...")
    try:
        cv_pdf = docx_to_pdf(str(cv_path), str(output_dir))
        print(f"  ✓ CV PDF : {cv_pdf}")
    except Exception as e:
        print(f"  ✗ Conversion CV PDF échouée : {e}")

    if letter:
        lm_path = output_dir / f"LM_{slug}.docx"
        build_cover_letter_docx(letter, str(lm_path))
        print("  → Conversion lettre de motivation en PDF...")
        try:
            lm_pdf = docx_to_pdf(str(lm_path), str(output_dir))
            print(f"  ✓ LM PDF : {lm_pdf}")
        except Exception as e:
            print(f"  ✗ Conversion LM PDF échouée : {e}")

    # 4. Sauvegarder les données JSON (pour relecture/debug)
    json_path = output_dir / f"data_{slug}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "job": job,
            "optimized_cv": optimized,
            "cover_letter": letter,
        }, f, ensure_ascii=False, indent=2)

    print(f"  ✓ Terminé : {slug}")


def main():
    parser = argparse.ArgumentParser(
        description="Optimise automatiquement ton CV pour des offres de stage en microélectronique / IA embarquée."
    )
    parser.add_argument(
        "--source",
        choices=["indeed", "hellowork", "all"],
        default="all",
        help="Source de scraping (défaut : all)",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=10,
        help="Nombre maximum d'offres à traiter par source (défaut : 10)",
    )
    parser.add_argument(
        "--query",
        type=str,
        default="stage microelectronique IA embarquée intelligence artificielle",
        help="Requête de recherche",
    )
    parser.add_argument(
        "--location",
        type=str,
        default="France",
        help="Localisation pour la recherche (défaut : France)",
    )
    parser.add_argument(
        "--cv",
        type=str,
        default="cv_data.json",
        help="Chemin vers le fichier cv_data.json",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Dossier de sortie (défaut : output/)",
    )
    args = parser.parse_args()

    # Vérifications
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERREUR : ANTHROPIC_API_KEY manquante. Créer un fichier .env avec la clé.")
        sys.exit(1)

    if not Path(args.cv).exists():
        print(f"ERREUR : Fichier CV '{args.cv}' introuvable.")
        sys.exit(1)

    # Préparation
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    client = anthropic.Anthropic(api_key=api_key)
    cv_data = load_cv_data(args.cv)

    # Scraping
    jobs = []
    if args.source in ("indeed", "all"):
        print(f"\n[Scraping Indeed] query='{args.query}' location='{args.location}' max={args.max}")
        jobs += scrape_indeed(query=args.query, location=args.location, max_results=args.max)

    if args.source in ("hellowork", "all"):
        print(f"\n[Scraping HelloWork] query='{args.query}' location='{args.location}' max={args.max}")
        jobs += scrape_hellowork(query=args.query, location=args.location, max_results=args.max)

    if not jobs:
        print("\nAucune offre trouvée. Vérifier la connexion ou les paramètres de recherche.")
        sys.exit(0)

    print(f"\n{len(jobs)} offre(s) trouvée(s). Début de l'optimisation...")

    # Traitement
    for i, job in enumerate(jobs, 1):
        print(f"\n[{i}/{len(jobs)}]")
        process_job(job, cv_data, client, output_dir)

    print(f"\n{'='*60}")
    print(f"Terminé ! {len(jobs)} CV + LM générés dans : {output_dir.resolve()}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
