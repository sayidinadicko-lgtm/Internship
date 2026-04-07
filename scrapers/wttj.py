import requests
import json
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.welcometothejungle.com"


def scrape_wttj(query="electronique embarquee", max_results=10):
    try:
        url = f"{BASE_URL}/fr/jobs"
        params = {
            "query": query,
            "contract_type[]": "internship",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "fr-FR,fr;q=0.9",
        }
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        logger.info(f"[WTTJ] Status: {resp.status_code}")

        if resp.status_code != 200:
            logger.error(f"[WTTJ] Erreur {resp.status_code}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        script = soup.find("script", {"id": "__NEXT_DATA__"})
        if not script:
            logger.error("[WTTJ] Pas de donnees __NEXT_DATA__")
            return []

        data = json.loads(script.string)
        jobs_data = (
            data.get("props", {})
                .get("pageProps", {})
                .get("jobs", [])
        )

        jobs = []
        for job in jobs_data[:max_results]:
            org = job.get("organization", {})
            office = job.get("office", {})
            jobs.append({
                "title": job.get("name", ""),
                "company": org.get("name", "Inconnu"),
                "location": office.get("city", ""),
                "description": job.get("description", "")[:1000],
                "url": f"{BASE_URL}/fr/companies/{org.get('slug','')}/jobs/{job.get('slug','')}",
                "source": "wttj",
                "easy_apply": False,
            })

        logger.info(f"[WTTJ] {len(jobs)} offre(s) trouvee(s).")
        return jobs

    except Exception as e:
        logger.error(f"[WTTJ] Erreur : {e}")
        return []