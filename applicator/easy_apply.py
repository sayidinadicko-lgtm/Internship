"""
Automatisation du formulaire Easy Apply de LinkedIn.
- Remplit les champs du formulaire étape par étape
- Upload le CV en PDF
- Soumet la candidature
"""

import os
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementClickInterceptedException
)

logger = logging.getLogger(__name__)

MAX_STEPS = 10  # Nombre max d'étapes dans le formulaire


def _human_delay(min_s: float = 0.5, max_s: float = 1.5):
    time.sleep(random.uniform(min_s, max_s))


def _fill_text_field(field, value: str):
    """Efface et remplit un champ texte de façon humaine."""
    field.clear()
    _human_delay(0.2, 0.5)
    for char in value:
        field.send_keys(char)
        time.sleep(random.uniform(0.03, 0.1))


def _handle_form_step(driver: webdriver.Chrome, wait: WebDriverWait, cv_data: dict, cv_pdf_path: str) -> bool:
    """
    Gère une étape du formulaire Easy Apply.
    Retourne True si on peut passer à l'étape suivante.
    """
    _human_delay(1, 2)

    # --- Upload CV ---
    try:
        upload_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        for inp in upload_inputs:
            if inp.is_displayed() or True:
                inp.send_keys(os.path.abspath(cv_pdf_path))
                logger.info("  [EasyApply] CV uploadé.")
                _human_delay(1, 2)
                break
    except Exception:
        pass

    # --- Champs texte (téléphone, email, etc.) ---
    personal = cv_data.get("personal_info", {})
    field_mappings = {
        "phone": personal.get("phone", ""),
        "phoneNumber": personal.get("phone", ""),
        "mobile": personal.get("phone", ""),
        "email": personal.get("email", ""),
        "firstName": personal.get("first_name", ""),
        "lastName": personal.get("last_name", ""),
        "city": "Marseille",
        "location": "France",
    }

    text_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='tel'], input[type='email']")
    for inp in text_inputs:
        try:
            if not inp.is_displayed():
                continue
            name = (inp.get_attribute("name") or "").lower()
            placeholder = (inp.get_attribute("placeholder") or "").lower()
            label_id = inp.get_attribute("id") or ""

            current_val = inp.get_attribute("value") or ""
            if current_val.strip():
                continue  # Déjà rempli

            for key, value in field_mappings.items():
                if value and (key.lower() in name or key.lower() in placeholder or key.lower() in label_id.lower()):
                    _fill_text_field(inp, value)
                    break
        except Exception:
            continue

    # --- Questions oui/non (radio buttons) ---
    try:
        radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
        for radio in radios:
            try:
                if not radio.is_selected():
                    label = radio.find_element(By.XPATH, "following-sibling::label")
                    label_text = label.text.lower()
                    # Répondre "oui" aux questions standard
                    if any(w in label_text for w in ["oui", "yes", "j'accepte", "i agree", "autorisation"]):
                        driver.execute_script("arguments[0].click();", radio)
                        _human_delay(0.3, 0.8)
            except Exception:
                continue
    except Exception:
        pass

    # --- Dropdowns (select) ---
    try:
        selects = driver.find_elements(By.CSS_SELECTOR, "select")
        for sel in selects:
            try:
                if not sel.is_displayed():
                    continue
                s = Select(sel)
                options = [o.text for o in s.options if o.text.strip() and o.get_attribute("value")]
                if options:
                    s.select_by_index(1)  # Première option disponible
                    _human_delay(0.3, 0.8)
            except Exception:
                continue
    except Exception:
        pass

    # --- Textareas (lettre de motivation texte) ---
    try:
        textareas = driver.find_elements(By.CSS_SELECTOR, "textarea")
        for ta in textareas:
            try:
                if not ta.is_displayed():
                    continue
                if ta.get_attribute("value") or ta.text:
                    continue
                # Laisser vide — la LM est dans le .docx uploadé
            except Exception:
                continue
    except Exception:
        pass

    return True


def apply_easy_apply(
    driver: webdriver.Chrome,
    job_url: str,
    cv_data: dict,
    cv_pdf_path: str,
) -> bool:
    """
    Postule à une offre via Easy Apply.
    Le driver doit déjà être connecté à LinkedIn.
    Retourne True si la candidature a été soumise avec succès.
    """
    wait = WebDriverWait(driver, 20)

    try:
        driver.get(job_url)
        _human_delay(3, 5)

        # Cliquer sur le bouton Easy Apply — cherche par texte dans tous les boutons
        apply_btn = None
        for attempt in range(3):
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                try:
                    txt = (btn.text or "").lower()
                    aria = (btn.get_attribute("aria-label") or "").lower()
                    if any(w in txt or w in aria for w in [
                        "easy apply", "candidature simplifiée", "postuler maintenant"
                    ]):
                        apply_btn = btn
                        break
                except Exception:
                    continue
            if apply_btn:
                break
            _human_delay(2, 3)

        if not apply_btn:
            logger.warning(f"[EasyApply] Bouton Easy Apply non trouvé pour {job_url}")
            return False

        driver.execute_script("arguments[0].scrollIntoView(true);", apply_btn)
        _human_delay(0.5, 1)
        driver.execute_script("arguments[0].click();", apply_btn)
        logger.info(f"[EasyApply] Formulaire ouvert pour {job_url}")
        _human_delay(2, 3)

        # Parcourir les étapes du formulaire
        for step in range(MAX_STEPS):
            _handle_form_step(driver, wait, cv_data, cv_pdf_path)
            _human_delay(1, 2)

            # Chercher tous les boutons visibles et cliquables
            submit_btn = None
            next_btn = None

            try:
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in all_buttons:
                    try:
                        if not btn.is_displayed() or not btn.is_enabled():
                            continue
                        txt = (btn.text or "").lower().strip()
                        aria = (btn.get_attribute("aria-label") or "").lower()
                        combined = txt + " " + aria
                        if any(w in combined for w in ["soumettre", "submit", "envoyer", "send"]):
                            submit_btn = btn
                            break
                        if any(w in combined for w in ["suivant", "next", "continuer", "continue", "vérifier"]):
                            next_btn = btn
                    except Exception:
                        continue
            except Exception:
                pass

            if submit_btn:
                driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                _human_delay(0.5, 1)
                driver.execute_script("arguments[0].click();", submit_btn)
                _human_delay(2, 3)
                logger.info("[EasyApply] Candidature soumise avec succès.")
                try:
                    close_btn = driver.find_element(
                        By.CSS_SELECTOR,
                        "button[aria-label='Fermer'], button[aria-label='Close'], "
                        "button[aria-label='Dismiss']"
                    )
                    driver.execute_script("arguments[0].click();", close_btn)
                except Exception:
                    pass
                return True

            elif next_btn:
                driver.execute_script("arguments[0].click();", next_btn)
                _human_delay(1, 2)
            else:
                # Essayer de trouver n'importe quel bouton primary
                try:
                    primary_btns = driver.find_elements(By.CSS_SELECTOR, "button.artdeco-button--primary")
                    for btn in primary_btns:
                        if btn.is_displayed() and btn.is_enabled():
                            txt = btn.text.lower()
                            if any(w in txt for w in ["soumettre", "submit", "suivant", "next", "continuer"]):
                                driver.execute_script("arguments[0].click();", btn)
                                _human_delay(1, 2)
                                break
                except Exception:
                    pass

                # Si toujours bloqué après plusieurs tentatives
                if step > 5:
                    logger.warning("[EasyApply] Formulaire bloqué, abandon.")
                    break

        logger.warning("[EasyApply] Soumission non confirmée.")
        return False

    except TimeoutException:
        logger.error("[EasyApply] Timeout — bouton Easy Apply non trouvé.")
        return False
    except Exception as e:
        logger.error(f"[EasyApply] Erreur : {e}")
        return False
