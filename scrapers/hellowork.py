"""
Scraper pour HelloWork – stages microélectronique / IA embarquée.
"""
import time
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

BASE_URL = "https://www.hellowork.com"


def _get_job_detail(url: str, session: requests.Session) -> Optional[str]:
    """Récupère la description complète d'une offre HelloWork."""
    try:
        time.sleep(1.5)
        resp = session.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        desc = (
            soup.find("div", class_=re.compile(r"job-description|jobDescription|tw-prose"))
            or soup.find("section", class_=re.compile(r"description"))
            or soup.find("div", attrs={"data-testid": "job-description"})
        )
        if desc:
            return desc.get_text(separator="\n", strip=True)
        return None
    except Exception:
        return None


def scrape_hellowork(
    query: str = "stage microelectronique intelligence artificielle embarquée",
    location: str = "France",
    max_results: int = 20,
) -> list[dict]:
    """
    Scrape HelloWork pour des offres de stage.

    Retourne une liste de dicts avec les clés :
        title, company, location, url, description, source
    """
    jobs = []
    session = requests.Session()
    page = 1

    while len(jobs) < max_results:
        params = {
            "k": query,
            "l": location,
            "c": "stage",   # contrat = stage
            "p": page,
        }
        try:
            resp = session.get(
                f"{BASE_URL}/fr-fr/emploi/recherche.html",
                params=params,
                headers=HEADERS,
                timeout=15,
            )
        except requests.RequestException as e:
            print(f"[HelloWork] Erreur réseau : {e}")
            break

        if resp.status_code != 200:
            print(f"[HelloWork] HTTP {resp.status_code} – arrêt du scraping.")
            break

        soup = BeautifulSoup(resp.text, "lxml")

        cards = soup.find_all(
            "article",
            class_=re.compile(r"job-item|offer-item|tw-group"),
        )
        if not cards:
            # Fallback : cherche les liens d'offres
            cards = soup.find_all("li", class_=re.compile(r"offer|job"))

        if not cards:
            print("[HelloWork] Aucune offre trouvée sur cette page, fin du scraping.")
            break

        for card in cards:
            if len(jobs) >= max_results:
                break

            # Titre
            title_tag = card.find(["h2", "h3", "a"], class_=re.compile(r"title|job-title"))
            title = title_tag.get_text(strip=True) if title_tag else "Titre inconnu"

            # Entreprise
            company_tag = card.find(
                ["span", "p", "div"], class_=re.compile(r"company|entreprise")
            )
            company = company_tag.get_text(strip=True) if company_tag else "Entreprise inconnue"

            # Localisation
            loc_tag = card.find(
                ["span", "p", "div"], class_=re.compile(r"location|localisation|city")
            )
            location_text = loc_tag.get_text(strip=True) if loc_tag else "France"

            # URL
            link_tag = card.find("a", href=re.compile(r"/fr-fr/emploi/|/offre/"))
            if not link_tag:
                link_tag = card.find("a", href=True)
            href = link_tag["href"] if link_tag else None
            if href and not href.startswith("http"):
                href = BASE_URL + href
            job_url = href

            # Description complète
            description = None
            if job_url:
                description = _get_job_detail(job_url, session)

            jobs.append({
                "title": title,
                "company": company,
                "location": location_text,
                "url": job_url or "",
                "description": description or "Description non disponible.",
                "source": "HelloWork",
            })
            print(f"[HelloWork] ✓ {title} – {company} ({location_text})")

        page += 1
        time.sleep(2)

    return jobs
