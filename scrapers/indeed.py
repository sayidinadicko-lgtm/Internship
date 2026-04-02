"""
Scraper pour Indeed France – stages microélectronique / IA embarquée.
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
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

BASE_URL = "https://fr.indeed.com"


def _get_job_detail(url: str, session: requests.Session) -> Optional[str]:
    """Récupère la description complète d'une offre."""
    try:
        time.sleep(1.5)
        resp = session.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        desc_div = soup.find("div", id="jobDescriptionText") or soup.find(
            "div", class_=re.compile(r"jobsearch-jobDescriptionText")
        )
        if desc_div:
            return desc_div.get_text(separator="\n", strip=True)
        return None
    except Exception:
        return None


def scrape_indeed(
    query: str = "stage microelectronique IA embarquée",
    location: str = "France",
    max_results: int = 20,
) -> list[dict]:
    """
    Scrape Indeed France pour des offres de stage.

    Retourne une liste de dicts avec les clés :
        title, company, location, url, description, source
    """
    jobs = []
    session = requests.Session()
    start = 0
    per_page = 10

    while len(jobs) < max_results:
        params = {
            "q": query,
            "l": location,
            "jt": "internship",
            "start": start,
        }
        try:
            resp = session.get(
                f"{BASE_URL}/jobs", params=params, headers=HEADERS, timeout=15
            )
        except requests.RequestException as e:
            print(f"[Indeed] Erreur réseau : {e}")
            break

        if resp.status_code != 200:
            print(f"[Indeed] HTTP {resp.status_code} – arrêt du scraping.")
            break

        soup = BeautifulSoup(resp.text, "lxml")

        # Indeed utilise plusieurs structures selon la version A/B
        cards = soup.find_all("div", class_=re.compile(r"job_seen_beacon|jobsearch-SerpJobCard"))
        if not cards:
            # Structure alternative avec data-jk
            cards = soup.find_all("div", attrs={"data-jk": True})

        if not cards:
            print("[Indeed] Aucune offre trouvée sur cette page, fin du scraping.")
            break

        for card in cards:
            if len(jobs) >= max_results:
                break

            # Titre
            title_tag = card.find(["h2", "a"], class_=re.compile(r"jobTitle|title"))
            title = title_tag.get_text(strip=True) if title_tag else "Titre inconnu"

            # Entreprise
            company_tag = card.find(
                ["span", "div"], attrs={"data-testid": "company-name"}
            ) or card.find("span", class_=re.compile(r"companyName"))
            company = company_tag.get_text(strip=True) if company_tag else "Entreprise inconnue"

            # Localisation
            loc_tag = card.find(
                ["div", "span"], attrs={"data-testid": "text-location"}
            ) or card.find("div", class_=re.compile(r"companyLocation"))
            location_text = loc_tag.get_text(strip=True) if loc_tag else "France"

            # URL de l'offre
            link_tag = card.find("a", href=re.compile(r"/rc/clk|/pagead/clk|/viewjob"))
            if not link_tag:
                link_tag = card.find("a", href=True)
            job_url = BASE_URL + link_tag["href"] if link_tag else None

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
                "source": "Indeed",
            })
            print(f"[Indeed] ✓ {title} – {company} ({location_text})")

        start += per_page
        time.sleep(2)

    return jobs
