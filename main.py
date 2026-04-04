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

from scrapers import scrape_indeed, scrape_hellowork
from cv_optimizer import optimize_cv, generate_cover_letter, build_cv_docx, build_cover_letter_docx, docx_to_pdf
from notifier.email_sender import send_applied_confirmation, send_offer_notification, send_daily_summary

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
        logger.warning(f"Conversion PDF echouee : {e}")
    json_path = output_dir / f"data_{slug}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"job": job, "optimized_cv": optimized, "cover_letter": letter}, f, ensure_ascii=False, indent=2)
    return cv_docx, cv_pdf, lm_docx


def process_job_linkedin(job, cv_data, client, output_dir, driver):
    from applicator.easy_apply import apply_easy_apply
    print(f"\n{'='*60}\n  {job['title']} - {job['company']}\n{'='*60}")
    try:
        cv_docx, cv_pdf, lm_docx = generate_docs(job, cv_data, client, output_dir)
    except Exception as e:
        logger.error(f"Erreur generation docs : {e}")
        return False
    success = apply_easy_apply(driver, job["url"], cv_data, cv_pdf)
    print("  Candidature soumise !" if success else "  Easy Apply echoue.")
    return success


def process_job_classic(job, cv_data, client, output_dir):
    print(f"\n{'='*60}\n  {job['title']} - {job['company']}\n  Source : {job['source']}\n{'='*60}")
    try:
        cv_docx, cv_pdf, lm_docx = generate_docs(job, cv_data, client, output_dir)
        print(f"  CV : {cv_docx}\n  LM : {lm_docx}")
    except Exception as e:
        logger.error(f"Erreur : {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["linkedin", "indeed", "hellowork", "all"], default="linkedin")
    parser.add_argument("--max", type=int, default=20)
    parser.add_argument("--query", type=str, default="stage microelectronique IA embarquee")
    parser.add_argument("--location", type=str, default="France")
    parser.add_argument("--cv", type=str, default="cv_data.json")
    parser.add_argument("--output", type=str, default="output")
    parser.add_argument("--headless", action="store_true", default=False)
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERREUR : ANTHROPIC_API_KEY manquante")
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
    jobs = []

    if args.source in ("linkedin", "all"):
        from scrapers.linkedin import scrape_linkedin
        linkedin_cookies = os.getenv("LINKEDIN_COOKIES", "")
        linkedin_email = os.getenv("LINKEDIN_EMAIL", "")
        linkedin_password = os.getenv("LINKEDIN_PASSWORD", "")
        print(f"\n[Scraping LinkedIn] query='{args.query}' location='{args.location}' max={args.max}")
        linkedin_jobs, driver = scrape_linkedin(
            cookies_json=linkedin_cookies,
            email=linkedin_email,
            password=linkedin_password,
            query=args.query,
            location=args.location,
            max_jobs=args.max,
            headless=args.headless,
        )
        print(f"[LinkedIn] {len(linkedin_jobs)} offre(s) trouvee(s).")
        if linkedin_jobs and driver:
            applied_jobs = []
            for i, job in enumerate(linkedin_jobs, 1):
                print(f"\n[LinkedIn {i}/{len(linkedin_jobs)}]")
                success = process_job_linkedin(job, cv_data, client, output_dir, driver)
                if success:
                    applied_jobs.append(job)
            driver.quit()
            if applied_jobs and gmail_address and gmail_app_password:
                send_daily_summary(gmail_address, gmail_app_password, notify_email, applied_jobs)
                print(f"Recapitulatif envoye a {notify_email}")
            else:
                print("\nAucune candidature soumise aujourd'hui.")

    if args.source in ("indeed", "all"):
        indeed_jobs = scrape_indeed(query=args.query, location=args.location, max_results=args.max)
        jobs += indeed_jobs

    if args.source in ("hellowork", "all"):
        hw_jobs = scrape_hellowork(query=args.query, location=args.location, max_results=args.max)
        jobs += hw_jobs

    for i, job in enumerate(jobs, 1):
        print(f"\n[{job['source']} {i}/{len(jobs)}]")
        process_job_classic(job, cv_data, client, output_dir)

    print(f"\n{'='*60}\nTermine !\n{'='*60}")


if __name__ == "__main__":
    main()