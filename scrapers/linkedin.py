"""
Scraper LinkedIn avec Selenium.
- Login automatique
- Recherche d'offres de stage
- Détection Easy Apply
- Extraction des détails de chaque offre
"""

import time
import random
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementClickInterceptedException
)

logger = logging.getLogger(__name__)


def _human_delay(min_s: float = 1.0, max_s: float = 3.0):
    """Pause aléatoire pour simuler un comportement humain."""
    time.sleep(random.uniform(min_s, max_s))


def _build_driver(headless: bool = False) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    # Options anti-détection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def _login(driver: webdriver.Chrome, email: str, password: str) -> bool:
    """Se connecte à LinkedIn. Retourne True si succès."""
    try:
        driver.get("https://www.linkedin.com/login")
        wait = WebDriverWait(driver, 15)

        email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        email_field.clear()
        for char in email:
            email_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

        _human_delay(0.5, 1.0)

        pwd_field = driver.find_element(By.ID, "password")
        pwd_field.clear()
        for char in password:
            pwd_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

        _human_delay(0.5, 1.0)
        pwd_field.send_keys(Keys.RETURN)

        # Vérifier la connexion
        wait.until(EC.presence_of_element_located((By.ID, "global-nav")))
        logger.info("[LinkedIn] Connexion réussie.")
        return True

    except TimeoutException:
        logger.error("[LinkedIn] Échec de connexion (timeout). Vérifier identifiants ou captcha.")
        return False


def _extract_job_details(driver: webdriver.Chrome, wait: WebDriverWait, job_url: str) -> dict:
    """Ouvre une offre et extrait ses détails."""
    driver.get(job_url)
    _human_delay(2, 4)

    details = {
        "url": job_url,
        "title": "",
        "company": "",
        "location": "",
        "description": "",
        "easy_apply": False,
        "source": "linkedin",
    }

    # Attendre que le contenu JavaScript soit chargé
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
    except TimeoutException:
        pass
    _human_delay(2, 3)

    # Titre — essayer plusieurs sélecteurs dans l'ordre
    for selector in [
        "h1.job-details-jobs-unified-top-card__job-title",
        "h1.t-24",
        "h1",
        ".job-details-jobs-unified-top-card__job-title",
        "[data-test-job-title]",
    ]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            text = el.text.strip()
            if text:
                details["title"] = text
                break
        except NoSuchElementException:
            continue

    # Entreprise
    for selector in [
        "a.job-details-jobs-unified-top-card__company-name",
        ".job-details-jobs-unified-top-card__primary-description a",
        ".jobs-unified-top-card__company-name a",
        ".jobs-unified-top-card__company-name",
        "[data-test-employer-name]",
    ]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            text = el.text.strip()
            if text:
                details["company"] = text
                break
        except NoSuchElementException:
            continue

    # Localisation
    for selector in [
        ".job-details-jobs-unified-top-card__primary-description .tvm__text",
        ".jobs-unified-top-card__bullet",
        ".jobs-unified-top-card__workplace-type",
        "[data-test-job-location]",
    ]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            text = el.text.strip()
            if text:
                details["location"] = text
                break
        except NoSuchElementException:
            continue

    # Description
    for selector in [
        "#job-details",
        ".jobs-description__content",
        ".jobs-description",
        ".job-details-jobs-unified-top-card__job-insight",
        "article",
    ]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            text = el.text.strip()
            if len(text) > 50:
                details["description"] = text[:3000]
                break
        except NoSuchElementException:
            continue

    # Si toujours pas de description, prendre le body entier comme fallback
    if not details["description"]:
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            details["description"] = body_text[:3000]
        except Exception:
            pass

    # Si toujours pas de titre, utiliser l'URL comme fallback
    if not details["title"]:
        details["title"] = f"Offre LinkedIn {job_url.split('/')[-2]}"

    # Si toujours pas d'entreprise, essayer via le titre de la page
    if not details["company"]:
        try:
            page_title = driver.title  # ex: "Ingénieur IA | STMicroelectronics | LinkedIn"
            parts = [p.strip() for p in page_title.split("|")]
            if len(parts) >= 2:
                details["title"] = details["title"] or parts[0]
                details["company"] = parts[1] if parts[1].lower() != "linkedin" else ""
        except Exception:
            pass

    # Easy Apply — LinkedIn filtre déjà avec f_AL=true dans l'URL de recherche
    # Toutes les offres retournées sont donc Easy Apply par définition.
    # On essaie quand même de confirmer via le bouton, mais on défaut à True.
    details["easy_apply"] = True
    try:
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            try:
                btn_text = (btn.text or "").lower()
                aria = (btn.get_attribute("aria-label") or "").lower()
                # Si on trouve explicitement un bouton "Postuler" non-Easy Apply, on corrige
                if "postuler sur le site" in btn_text or "apply on company" in aria:
                    details["easy_apply"] = False
                    break
            except Exception:
                continue
    except Exception:
        pass

    return details


def scrape_linkedin(
    email: str,
    password: str,
    query: str = "stage microelectronique IA embarquée",
    location: str = "France",
    max_jobs: int = 10,
    headless: bool = True,
) -> tuple[list[dict], object]:
    """
    Se connecte à LinkedIn, cherche des offres de stage Easy Apply.
    Retourne (jobs, driver) — le driver reste ouvert pour la phase d'apply.
    Appeler driver.quit() après avoir terminé les candidatures.
    """
    driver = _build_driver(headless=headless)
    wait = WebDriverWait(driver, 15)
    jobs = []

    try:
        if not _login(driver, email, password):
            driver.quit()
            return [], None

        _human_delay(2, 4)

        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        encoded_location = urllib.parse.quote(location)
        search_url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={encoded_query}"
            f"&location={encoded_location}"
            f"&f_JT=I"
            f"&f_AL=true"
            f"&f_TPR=r2592000"
            f"&sortBy=R"
        )

        logger.info(f"[LinkedIn] Recherche : {query} | {location}")
        driver.get(search_url)
        _human_delay(3, 5)

        # Collecter les liens des offres
        job_links = []
        scroll_attempts = 0

        # On scanne jusqu'à 3x plus d'offres pour trouver assez d'Easy Apply
        scan_limit = max_jobs * 3
        while len(job_links) < scan_limit and scroll_attempts < 8:
            cards = driver.find_elements(
                By.CSS_SELECTOR,
                "a.job-card-list__title, a.job-card-container__link"
            )
            for card in cards:
                href = card.get_attribute("href")
                if href and "/jobs/view/" in href and href not in job_links:
                    job_links.append(href.split("?")[0])
                if len(job_links) >= scan_limit:
                    break

            if len(job_links) < scan_limit:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                _human_delay(2, 3)
                scroll_attempts += 1

        logger.info(f"[LinkedIn] {len(job_links)} offres trouvées.")

        # Extraire les détails de chaque offre — s'arrêter quand on a max_jobs Easy Apply
        for i, url in enumerate(job_links):
            if len(jobs) >= max_jobs:
                break
            logger.info(f"[LinkedIn] Scan offre {i+1}/{len(job_links)} (Easy Apply trouvés: {len(jobs)}/{max_jobs}) : {url}")
            try:
                job = _extract_job_details(driver, wait, url)
                if not job["easy_apply"]:
                    logger.info("  → Pas Easy Apply, ignorée.")
                    continue
                if job["title"] and job["description"]:
                    jobs.append(job)
                    logger.info(
                        f"  → {job['title']} chez {job['company']} "
                        f"| Easy Apply: {job['easy_apply']}"
                    )
            except Exception as e:
                logger.warning(f"  → Erreur extraction : {e}")
            _human_delay(2, 4)

    except Exception as e:
        logger.error(f"[LinkedIn] Erreur : {e}")
        driver.quit()
        return [], None

    # NE PAS quitter le driver — il sera réutilisé pour les candidatures
    return jobs, driver
