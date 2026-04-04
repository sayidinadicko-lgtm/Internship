"""
Scraper LinkedIn avec Selenium — authentification par cookies.
"""

import json
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)


def _human_delay(min_s: float = 1.0, max_s: float = 3.0):
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
        "Chrome/124.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def _inject_cookies(driver: webdriver.Chrome, cookies_json: str) -> bool:
    """Injecte les cookies LinkedIn pour éviter le login (contourne le blocage)."""
    try:
        driver.get("https://www.linkedin.com")
        _human_delay(2, 3)

        cookies = json.loads(cookies_json)
        for cookie in cookies:
            # Nettoyer les champs non supportés par Selenium
            cookie.pop("storeId", None)
            cookie.pop("hostOnly", None)
            cookie.pop("session", None)
            if "expirationDate" in cookie:
                cookie["expiry"] = int(cookie.pop("expirationDate"))
            if cookie.get("sameSite") is None:
                cookie["sameSite"] = "None"
            # Forcer le bon domaine
            if not cookie.get("domain", "").startswith("."):
                cookie["domain"] = ".linkedin.com"
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                logger.debug(f"Cookie {cookie.get('name')} ignoré : {e}")

        driver.get("https://www.linkedin.com/feed/")
        _human_delay(3, 5)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "global-nav"))
            )
            logger.info("[LinkedIn] Connecté via cookies.")
            return True
        except TimeoutException:
            logger.error("[LinkedIn] Cookies invalides ou expirés.")
            return False

    except Exception as e:
        logger.error(f"[LinkedIn] Erreur injection cookies : {e}")
        return False


def _extract_job_details(driver, wait, job_url: str) -> dict:
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

    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
    except TimeoutException:
        pass
    _human_delay(2, 3)

    for selector in ["h1.job-details-jobs-unified-top-card__job-title", "h1.t-24", "h1"]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            text = el.text.strip()
            if text:
                details["title"] = text
                break
        except NoSuchElementException:
            continue

    for selector in [
        "a.job-details-jobs-unified-top-card__company-name",
        ".job-details-jobs-unified-top-card__primary-description a",
        ".jobs-unified-top-card__company-name",
    ]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            text = el.text.strip()
            if text:
                details["company"] = text
                break
        except NoSuchElementException:
            continue

    for selector in [
        ".job-details-jobs-unified-top-card__primary-description .tvm__text",
        ".jobs-unified-top-card__bullet",
    ]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            text = el.text.strip()
            if text:
                details["location"] = text
                break
        except NoSuchElementException:
            continue

    for selector in ["#job-details", ".jobs-description__content", ".jobs-description", "article"]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            text = el.text.strip()
            if len(text) > 50:
                details["description"] = text[:3000]
                break
        except NoSuchElementException:
            continue

    if not details["description"]:
        try:
            details["description"] = driver.find_element(By.TAG_NAME, "body").text[:3000]
        except Exception:
            pass

    if not details["title"]:
        details["title"] = f"Offre LinkedIn {job_url.split('/')[-2]}"

    details["easy_apply"] = True
    return details


def scrape_linkedin(
    cookies_json: str = "",
    email: str = "",
    password: str = "",
    query: str = "stage",
    location: str = "France",
    max_jobs: int = 10,
    headless: bool = True,
) -> tuple[list[dict], object]:
    """
    Scrape LinkedIn via cookies (recommandé) ou email/password.
    """
    driver = _build_driver(headless=headless)
    wait = WebDriverWait(driver, 15)
    jobs = []

    try:
        # Connexion : cookies en priorité, sinon email/password
        if cookies_json:
            connected = _inject_cookies(driver, cookies_json)
        elif email and password:
            from scrapers.linkedin_login import _login
            connected = _login(driver, email, password)
        else:
            logger.error("[LinkedIn] Aucune méthode d'authentification fournie.")
            driver.quit()
            return [], None

        if not connected:
            driver.quit()
            return [], None

        _human_delay(2, 4)

        import urllib.parse
        search_url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={urllib.parse.quote(query)}"
            f"&location={urllib.parse.quote(location)}"
            f"&f_JT=I&f_AL=true&f_TPR=r2592000&sortBy=R"
        )

        driver.get(search_url)
        _human_delay(3, 5)

        job_links = []
        scroll_attempts = 0
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

        for i, url in enumerate(job_links):
            if len(jobs) >= max_jobs:
                break
            try:
                job = _extract_job_details(driver, wait, url)
                if job["title"] and job["description"]:
                    jobs.append(job)
                    logger.info(f"  → {job['title']} chez {job['company']}")
            except Exception as e:
                logger.warning(f"  → Erreur extraction : {e}")
            _human_delay(2, 4)

    except Exception as e:
        logger.error(f"[LinkedIn] Erreur : {e}")
        driver.quit()
        return [], None

    return jobs, driver