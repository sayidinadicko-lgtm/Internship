#!/usr/bin/env python3
import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
import anthropic

from scrapers.francetravail import scrape_francetravail
from cv_optimizer import optimize_cv, generate_cover_letter, build_cv_docx, build_cover_letter_docx, docx_to_pdf
from notifier.email_sender import send_daily_summary

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text[:60]


def load_cv_data(path="cv_data.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def generate_docs(job, cv_data, client, output_dir):
    slug = slugify(f"{job['title']}_{job['company']}")
    optimized = optimize_cv(cv_data, job, client)
    letter = generate_cover_letter(cv_data, optimized, job, client)
    cv_docx = str(output_dir / f"CV_{slug}.docx")
    lm_docx = str(output_dir / f"LM_{slug}.docx")
    build_cv_docx(optimized, cv_docx)
    build_cover_letter_docx(letter, lm_docx)
    cv_pdf = cv_docx
    try:
        cv_pdf = docx_to_pdf(cv_docx, str(output_dir))
    except Exception as e:
        logger.warning(f"PDF echoue : {e}")
    json_path = output_dir / f"data_{slug}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"job": job, "optimized_cv": optimized, "cover_letter": letter}, f, ensure_ascii=False, indent=2)
    return cv_docx, cv_pdf, lm_docx


def process_job(job, cv_data, client, output_dir):
    print(f"\n{'='*60}\n  {job['title']} - {job['company']}\n  Lieu : {job.get('location','')}\n{'='*60}")
    try:
        cv_docx, cv_pdf, lm_docx = generate_docs(job, cv_data, client, output_dir)
        print(f"  CV : {cv_docx}\n  LM : {lm_docx}")
        return True
    except Exception as e:
        logger.error(f"Erreur : {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, default="stage microelectronique IA embarquee")
    parser.add_argument("--location", type=str, default="")
    parser.add_argument("--max", type=int, default=10)
    parser.add_argument("--cv", type=str, default="cv_data.json")
    parser.add_argument("--output", type=str, default="output")
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERREUR : ANTHROPIC_API_KEY manquante")
        sys.exit(1)

    ft_client_id = os.getenv("FT_CLIENT_ID", "")
    ft_client_secret = os.getenv("FT_CLIENT_SECRET", "")
    if not ft_client_id or not ft_client_secret:
        print("ERREUR : FT_CLIENT_ID ou FT_CLIENT_SECRET manquants")
        sys.exit(1)

    if not Path(args.cv).exists():
        print(f"ERREUR : Fichier CV '{args.cv}' introuvable.")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    cv_data = load_cv_data(args.cv)
    gmail_address = os.getenv("GMAIL_ADDRESS", "")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "")
    notify_email = os.getenv("NOTIFY_EMAIL", gmail_address)

    print(f"\n[France Travail] query='{args.query}' max={args.max}")
    jobs = scrape_francetravail(
        client_id=ft_client_id,
        client_secret=ft_client_secret,
        query=args.query,
        location=args.location,
        max_results=args.max,
    )
    print(f"[France Travail] {len(jobs)} offre(s) trouvee(s).")

    done = []
    for i, job in enumerate(jobs, 1):
        print(f"\n[{i}/{len(jobs)}]")
        if process_job(job, cv_data, client, output_dir):
            done.append(job)

    if done and gmail_address and gmail_app_password:
        send_daily_summary(gmail_address, gmail_app_password, notify_email, done)
        print(f"\nRecapitulatif envoye a {notify_email}")

    print(f"\n{'='*60}\nTermine ! {len(done)} CV genere(s).\n{'='*60}")


if __name__ == "__main__":
    main()