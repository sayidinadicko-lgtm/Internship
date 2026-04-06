"""
Scraper France Travail API (ex-Pole Emploi) - gratuit, officiel, pas de blocage.
"""
import requests
import logging

logger = logging.getLogger(__name__)

API_TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
API_SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"


def _get_token(client_id: str, client_secret: str) -> str:
    resp = requests.post(API_TOKEN_URL, data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "api_offresdemploiv2 o2dsoffre",
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def scrape_francetravail(
    client_id: str,
    client_secret: str,
    query: str = "stage microelectronique",
    location: str = "",
    max_results: int = 10,
) -> list[dict]:
    try:
        token = _get_token(client_id, client_secret)
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "motsCles": query,
            "typeContrat": "ST",
            "range": f"0-{max_results - 1}",
        }
        resp = requests.get(API_SEARCH_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        offres = data.get("resultats", [])
        jobs = []
        for o in offres:
            jobs.append({
                "title": o.get("intitule", ""),
                "company": o.get("entreprise", {}).get("nom", "Entreprise inconnue"),
                "location": o.get("lieuTravail", {}).get("libelle", ""),
                "description": o.get("description", ""),
                "url": o.get("origineOffre", {}).get("urlOrigine", ""),
                "source": "francetravail",
                "easy_apply": False,
            })
        logger.info(f"[FranceTravail] {len(jobs)} offre(s) trouvee(s).")
        return jobs
    except Exception as e:
        logger.error(f"[FranceTravail] Erreur : {e}")
        return []