import requests
import logging

logger = logging.getLogger(__name__)

API_URL = "https://www.apec.fr/cms/webservices/rechercheOffre/rechercherOffres"


def scrape_apec(query="electronique embarquee", max_results=10):
    try:
        payload = {
            "motsCles": query,
            "typeContrat": [7],
            "nbResultats": max_results,
            "debut": 0,
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=15)
        logger.info(f"[APEC] Status: {resp.status_code}")

        if resp.status_code != 200:
            logger.error(f"[APEC] Erreur {resp.status_code}")
            return []

        data = resp.json()
        offres = data.get("resultats", [])
        jobs = []
        for o in offres:
            jobs.append({
                "title": o.get("intitule", ""),
                "company": o.get("nomCommercialSociete", "Entreprise inconnue"),
                "location": o.get("lieuTravaill", {}).get("libelle", ""),
                "description": o.get("texteHtml", "")[:1000],
                "url": f"https://www.apec.fr/candidat/recherche-emploi.html/emploi/detail-offre/{o.get('numeroOffre','')}",
                "source": "apec",
                "easy_apply": False,
            })
        logger.info(f"[APEC] {len(jobs)} offre(s) trouvee(s).")
        return jobs

    except Exception as e:
        logger.error(f"[APEC] Erreur : {e}")
        return []