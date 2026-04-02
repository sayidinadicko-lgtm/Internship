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


def _build_driver(headless: bool = True) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
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

    # Détecter Easy Apply
    try:
        apply_btn = driver.find_element(
            By.CSS_SELECTOR,
            "button.jobs-apply-button, "
            "button[aria-label*='Easy Apply'], "
            "button[aria-label*='Candidature simplifiée']"
        )
        btn_text = apply_btn.text.lower()
        details["easy_apply"] = (
            "easy apply" in btn_text
            or "candidature simplifiée" in btn_text
            or "easy" in btn_text
        )
    except NoSuchElementException:
        details["easy_apply"] = False

    return details


def scrape_linkedin(
    email: str,
    password: str,
    query: str = "stage microelectronique IA embarquée",
    location: str = "France",
    max_jobs: int = 10,
    headless: bool = True,
) -> list[dict]:
    """
    Se connecte à LinkedIn, cherche des offres de stage et retourne la liste.

    Chaque offre contient :
      title, company, location, description, easy_apply, url, source
    """
    driver = _build_driver(headless=headless)
    wait = WebDriverWait(driver, 15)
    jobs = []

    try:
        if not _login(driver, email, password):
            return []

        _human_delay(2, 4)

        # Construire l'URL de recherche LinkedIn Jobs
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        encoded_location = urllib.parse.quote(location)
        search_url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={encoded_query}"
            f"&location={encoded_location}"
            f"&f_JT=I"          # I = Internship
            f"&f_TPR=r2592000"  # 30 derniers jours
            f"&sortBy=R"        # Pertinence
        )

        logger.info(f"[LinkedIn] Recherche : {query} | {location}")
        driver.get(search_url)
        _human_delay(3, 5)

        # Collecter les liens des offres
        job_links = []
        scroll_attempts = 0

        while len(job_links) < max_jobs and scroll_attempts < 5:
            cards = driver.find_elements(
                By.CSS_SELECTOR,
                "a.job-card-list__title, a.job-card-container__link"
            )
            for card in cards:
                href = card.get_attribute("href")
                if href and "/jobs/view/" in href and href not in job_links:
                    job_links.append(href.split("?")[0])
                if len(job_links) >= max_jobs:
                    break

            if len(job_links) < max_jobs:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                _human_delay(2, 3)
                scroll_attempts += 1

        logger.info(f"[LinkedIn] {len(job_links)} offres trouvées.")

        # Extraire les détails de chaque offre
        for i, url in enumerate(job_links[:max_jobs]):
            logger.info(f"[LinkedIn] Offre {i+1}/{len(job_links[:max_jobs])} : {url}")
            try:
                job = _extract_job_details(driver, wait, url)
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
    finally:
        driver.quit()

    return jobs
