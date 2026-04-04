#!/usr/bin/env python3
"""
CV Optimizer â€“ Point d'entrÃ©e principal.

Usage :
    python main.py [--source linkedin|indeed|hellowork|all] [--max N] [--query "..."]

Variables d'environnement requises (.env) :
    ANTHROPIC_API_KEY      : clÃ© API Anthropic
    LINKEDIN_EMAIL         : email du compte LinkedIn
    LINKEDIN_PASSWORD      : mot de passe LinkedIn
    GMAIL_ADDRESS          : adresse Gmail pour les notifications
    GMAIL_APP_PASSWORD     : mot de passe d'application Gmail
    NOTIFY_EMAIL           : adresse qui reÃ§oit les notifications (souvent = GMAIL_ADDRESS)
"""
import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
import anthropic

from scrapers import scrape_indeed, scrape_hellowork
from cv_optimizer import optimize_cv, generate_cover_letter, build_cv_docx, build_cover_letter_docx, docx_to_pdf
from notifier.email_sender import send_applied_confirmation, send_offer_notification, send_daily_summary

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text[:60]


def load_cv_data(path: str = "cv_data.json") -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def generate_docs(job: dict, cv_data: dict, client: anthropic.Anthropic, output_dir: Path) -> tuple[str, str, str]:
    """
    GÃ©nÃ¨re CV + LM pour une offre.
    Retourne (cv_docx_path, cv_pdf_path, lm_docx_path).
    """
    slug = slugify(f"{job['title']}_{job['company']}")

    optimized = optimize_cv(cv_data, job, client)
    letter = generate_cover_letter(cv_data, optimized, job, client)

    cv_docx = str(output_dir / f"CV_{slug}.docx")
    lm_docx = str(output_dir / f"LM_{slug}.docx")
    build_cv_docx(optimized, cv_docx)
    build_cover_letter_docx(letter, lm_docx)

    # Conversion PDF (pour l'upload LinkedIn)
    cv_pdf = cv_docx
    try:
        cv_pdf = docx_to_pdf(cv_docx, str(output_dir))
    except Exception as e:
        logger.warning(f"Conversion PDF Ã©chouÃ©e, utilisation du .docx : {e}")

    # Sauvegarder les donnÃ©es JSON
    json_path = output_dir / f"data_{slug}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"job": job, "optimized_cv": optimized, "cover_letter": letter},
                  f, ensure_ascii=False, indent=2)

    return cv_docx, cv_pdf, lm_docx


def process_job_linkedin(
    job: dict,
    cv_data: dict,
    client: anthropic.Anthropic,
    output_dir: Path,
    driver,
) -> bool:
    """
    Postule Ã  une offre LinkedIn Easy Apply.
    Retourne True si la candidature a Ã©tÃ© soumise avec succÃ¨s.
    """
    from applicator.easy_apply import apply_easy_apply

    print(f"\n{'='*60}")
    print(f"  {job['title']} â€” {job['company']}")
    print(f"{'='*60}")

    print("  â†’ GÃ©nÃ©ration CV + LM...")
    try:
        cv_docx, cv_pdf, lm_docx = generate_docs(job, cv_data, client, output_dir)
    except Exception as e:
        logger.error(f"  Erreur gÃ©nÃ©ration docs : {e}")
        return False

    print("  â†’ Candidature Easy Apply en cours...")
    success = apply_easy_apply(driver, job["url"], cv_data, cv_pdf)
    if success:
        print(f"  âœ“ Candidature soumise !")
    else:
        print(f"  âœ— Easy Apply Ã©chouÃ© pour cette offre.")
    return success


def process_job_classic(job: dict, cv_data: dict, client: anthropic.Anthropic, output_dir: Path):
    """Traite une offre Indeed/HelloWork (gÃ©nÃ©ration uniquement, sans auto-apply)."""
    slug = slugify(f"{job['title']}_{job['company']}")
    print(f"\n{'='*60}")
    print(f"  {job['title']} â€” {job['company']}")
    print(f"  Source : {job['source']} | Lieu : {job.get('location', 'N/A')}")
    print(f"{'='*60}")

    try:
        cv_docx, cv_pdf, lm_docx = generate_docs(job, cv_data, client, output_dir)
        print(f"  âœ“ CV : {cv_docx}")
        print(f"  âœ“ LM : {lm_docx}")
    except Exception as e:
        logger.error(f"  Erreur : {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Optimise le CV, postule automatiquement (LinkedIn Easy Apply) et notifie par mail."
    )
    parser.add_argument(
        "--source",
        choices=["linkedin", "indeed", "hellowork", "all"],
        default="linkedin",
        help="Source de scraping (dÃ©faut : linkedin)",
    )
    parser.add_argument("--max", type=int, default=20,
                        help="Nombre de candidatures Easy Apply Ã  soumettre (dÃ©faut : 20)")
    parser.add_argument(
        "--query", type=str,
        default="stage microelectronique IA embarquÃ©e intelligence artificielle",
        help="RequÃªte de recherche",
    )
    parser.add_argument("--location", type=str, default="France",
                        help="Localisation (dÃ©faut : France)")
    parser.add_argument("--cv", type=str, default="cv_data.json",
                        help="Chemin vers cv_data.json")
    parser.add_argument("--output", type=str, default="output",
                        help="Dossier de sortie (dÃ©faut : output/)")
    parser.add_argument("--headless", action="store_true", default=False,
                        help="Mode headless pour le navigateur (dÃ©faut : False = fenÃªtre visible)")
    args = parser.parse_args()

    # --- VÃ©rifications ---
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERREUR : ANTHROPIC_API_KEY manquante dans .env")
        sys.exit(1)

    if not Path(args.cv).exists():
        print(f"ERREUR : Fichier CV '{args.cv}' introuvable.")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    client = anthropic.Anthropic(api_key=api_key)
    cv_data = load_cv_data(args.cv)

    gmail_address = os.getenv("GMAIL_ADDRESS", "")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "")
    notify_email = os.getenv("NOTIFY_EMAIL", gmail_address)

    jobs = []

    # --- Scraping LinkedIn ---
    if args.source in ("linkedin", "all"):
        linkedin_email = os.getenv("LINKEDIN_EMAIL", "")
        linkedin_password = os.getenv("LINKEDIN_PASSWORD", "")
        if not linkedin_email or not linkedin_password:
            print("ERREUR : LINKEDIN_EMAIL et LINKEDIN_PASSWORD manquants dans .env")
            sys.exit(1)

        from scrapers.linkedin import scrape_linkedin
        print(f"\n[Scraping LinkedIn] query='{args.query}' location='{args.location}' max={args.max}")
        linkedin_cookies = os.getenv("LINKEDIN_COOKIES", "")
    linkedin_jobs, driver = scrape_linkedin(
            cookies_json=linkedin_cookies,
            email=linkedin_email,
            password=linkedin_password,
        query=args.query,
                location=args.location,
                max_jobs=args.max,
                headless=args.headless,
        )
        print(f"[LinkedIn] {len(linkedin_jobs)} offre(s) trouvÃ©e(s).")

        if linkedin_jobs and driver:
            applied_jobs = []
            for i, job in enumerate(linkedin_jobs, 1):
                print(f"\n[LinkedIn {i}/{len(linkedin_jobs)}]")
                success = process_job_linkedin(job, cv_data, client, output_dir, driver)
                if success:
                    applied_jobs.append(job)

            driver.quit()

            # Mail rÃ©capitulatif unique
            if applied_jobs and gmail_address and gmail_app_password:
                print(f"\nâ†’ Envoi du rÃ©capitulatif : {len(applied_jobs)} candidatures soumises...")
                send_daily_summary(gmail_address, gmail_app_password, notify_email, applied_jobs)
                print(f"âœ“ RÃ©capitulatif envoyÃ© Ã  {notify_email}")
            else:
                print(f"\nAucune candidature Easy Apply soumise aujourd'hui.")

    # --- Scraping Indeed ---
    if args.source in ("indeed", "all"):
        print(f"\n[Scraping Indeed] query='{args.query}' location='{args.location}' max={args.max}")
        indeed_jobs = scrape_indeed(query=args.query, location=args.location, max_results=args.max)
        jobs += indeed_jobs
        print(f"[Indeed] {len(indeed_jobs)} offre(s) trouvÃ©e(s).")

    # --- Scraping HelloWork ---
    if args.source in ("hellowork", "all"):
        print(f"\n[Scraping HelloWork] query='{args.query}' location='{args.location}' max={args.max}")
        hw_jobs = scrape_hellowork(query=args.query, location=args.location, max_results=args.max)
        jobs += hw_jobs
        print(f"[HelloWork] {len(hw_jobs)} offre(s) trouvÃ©e(s).")

    # --- Traitement Indeed / HelloWork (gÃ©nÃ©ration uniquement) ---
    for i, job in enumerate(jobs, 1):
        print(f"\n[{job['source']} {i}/{len(jobs)}]")
        process_job_classic(job, cv_data, client, output_dir)

    print(f"\n{'='*60}")
    print("TerminÃ© !")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
