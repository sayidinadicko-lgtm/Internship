"""
Instagram posting via Playwright browser automation.

Flow:
  First run (no saved session):
    → Opens a visible Chromium browser
    → User logs in to Instagram manually
    → Browser state (cookies + localStorage) saved to disk
    → Browser closes

  Posting run (saved session found):
    → Loads saved browser state
    → Opens Chromium (visible) and navigates to Instagram
    → Clicks "Create" → uploads carousel images via file picker
    → Types caption → clicks "Share"
    → Saves updated state, closes browser

To force a new manual login:
    python -m ledeclicmental --login

Requirements:
    pip install playwright
    python -m playwright install chromium
"""
from __future__ import annotations

import random
import time
from pathlib import Path

from ledeclicmental.config import settings
from ledeclicmental.content.audio import AudioTrack
from ledeclicmental.content.generator import PostContent
from ledeclicmental.content.hashtags import format_hashtags, get_hashtags
from ledeclicmental.utils.logger import get_logger

logger = get_logger(__name__)

_MAX_RETRIES = 3
_RETRY_BACKOFF = 60

# Playwright browser state persisted between runs
_STATE_FILE: Path = settings.data_dir / "session" / "playwright_state.json"


# ── Caption builder ───────────────────────────────────────────────────────────

def _build_caption(content: PostContent, audio: AudioTrack) -> str:
    """
    Assemble la légende complète du post Instagram.

    Structure :
      [Légende FR + CTA FR]

      - - -

      [Légende EN + CTA EN]

      .
      .
      .
      [30 hashtags]
    """
    fr_block = f"{content.caption_fr}\n\n{content.cta_fr}"
    en_block = f"{content.caption_en}\n\n{content.cta_en}"

    tags = get_hashtags(content.topic.keyword_fr, content.slot)
    hashtag_line = format_hashtags(tags)

    return (
        f"{fr_block}\n\n"
        f"- - -\n\n"
        f"{en_block}\n\n"
        f".\n.\n.\n\n"
        f"{hashtag_line}"
    )


# ── Playwright helpers ────────────────────────────────────────────────────────

def _sync_playwright():
    """Import and return sync_playwright (raises clear error if not installed)."""
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        return sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright non installé. Lance :\n"
            "  pip install playwright\n"
            "  python -m playwright install chromium"
        ) from exc


def _dismiss_popups(page) -> None:
    """Dismiss Instagram's 'Not Now' popups (notifications, save info, etc.)."""
    for text in ("Not Now", "Pas maintenant", "Not now"):
        try:
            btn = page.query_selector(f'button:has-text("{text}")')
            if btn:
                btn.click()
                time.sleep(0.5)
        except Exception:
            pass


def _click_next(page, context: str = "") -> None:
    """Click the 'Next / Suivant' button in the post-creation wizard."""
    for sel in (
        'div[role="button"]:has-text("Next")',
        'div[role="button"]:has-text("Suivant")',
        'button:has-text("Next")',
        'button:has-text("Suivant")',
    ):
        try:
            page.click(sel, timeout=8_000)
            logger.info("'Next' cliqué (%s).", context)
            return
        except Exception:
            pass
    logger.warning("Bouton 'Next' introuvable (%s) — capture d'écran.", context)
    _screenshot(page, f"error_next_{context.replace(' ', '_')}.png")


def _screenshot(page, filename: str) -> None:
    """Save a debug screenshot to the data directory."""
    try:
        path = settings.data_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path))
        logger.info("Capture d'écran : %s", path)
    except Exception:
        pass


# ── Session management ────────────────────────────────────────────────────────

def interactive_login() -> None:
    """
    Open a visible Chromium browser so the user can log in to Instagram manually.
    Once the home feed is detected, saves browser state and closes.

    Called via:  python -m ledeclicmental --login
    """
    sync_playwright = _sync_playwright()
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("  CONNEXION INSTAGRAM — Navigateur en cours d'ouverture...")
    print("  Connectez-vous normalement, puis attendez.")
    print("=" * 60 + "\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=50,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle")
        time.sleep(2)

        # Auto-dismiss cookie consent popup if present
        for sel in (
            'button:has-text("Decline optional cookies")',
            'button:has-text("Refuser les cookies optionnels")',
            'button:has-text("Only allow essential cookies")',
            'button:has-text("Allow all cookies")',
            'button:has-text("Autoriser tous les cookies")',
        ):
            try:
                el = page.query_selector(sel)
                if el:
                    el.click()
                    logger.info("Popup cookies fermee automatiquement.")
                    time.sleep(1)
                    break
            except Exception:
                pass

        logger.info("Navigateur ouvert — connectez-vous a Instagram (max 10 min).")

        # Poll page.url in Python — avoids Instagram CSP blocking JS eval
        deadline = time.time() + 600  # 10 minutes
        logged_in = False
        while time.time() < deadline:
            try:
                current_url = page.url
            except Exception:
                break
            if (
                current_url
                and "/accounts/login" not in current_url
                and "instagram.com" in current_url
            ):
                logged_in = True
                break
            time.sleep(2)

        if not logged_in:
            logger.warning("Connexion non detectee apres 10 minutes.")

        time.sleep(3)  # Let cookies settle
        _dismiss_popups(page)
        time.sleep(1)

        context.storage_state(path=str(_STATE_FILE))
        logger.info("Session sauvegardee dans %s", _STATE_FILE)

        browser.close()
        if logged_in:
            print("\nConnexion reussie ! Session sauvegardee.\n")
        else:
            print("\nConnexion non confirmee — relancez --login et connectez-vous dans le navigateur.\n")


def _has_session() -> bool:
    return _STATE_FILE.exists() and _STATE_FILE.stat().st_size > 100


# ── Post automation ───────────────────────────────────────────────────────────

def _post_carousel(image_paths: list[Path], caption: str) -> bool:
    """
    Automate carousel (album) upload via Instagram web UI.
    Returns True on success, False if session expired or flow fails.
    """
    sync_playwright = _sync_playwright()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=80,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            storage_state=str(_STATE_FILE),
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            # ── 1. Navigate to Instagram home ─────────────────────────────
            page.goto("https://www.instagram.com/", wait_until="networkidle", timeout=30_000)
            time.sleep(2)

            # Check session validity
            if "/accounts/login" in page.url:
                logger.warning("Session expiree — re-connexion necessaire.")
                browser.close()
                _STATE_FILE.unlink(missing_ok=True)
                return False

            _dismiss_popups(page)
            time.sleep(1)

            # ── 2. Click the "Create / Nouveau post" button ───────────────
            create_clicked = False
            create_selectors = [
                # SVG aria-label in the left nav
                'svg[aria-label="New post"]',
                'svg[aria-label="Nouveau post"]',
                # Wrapper elements
                '[aria-label="New post"]',
                '[aria-label="Nouveau post"]',
                # Text-based button
                'span:has-text("Create")',
                'span:has-text("Créer")',
            ]
            for sel in create_selectors:
                try:
                    el = page.wait_for_selector(sel, timeout=4_000)
                    if el:
                        el.click()
                        create_clicked = True
                        logger.info("Bouton 'Create' clique.")
                        break
                except Exception:
                    pass

            if not create_clicked:
                # Fallback: click the nav item that contains the "+" SVG
                page.evaluate("""() => {
                    const svgs = document.querySelectorAll('svg');
                    for (const svg of svgs) {
                        const label = svg.getAttribute('aria-label') || '';
                        if (label.toLowerCase().includes('post') ||
                            label.toLowerCase().includes('creat') ||
                            label.toLowerCase().includes('nouveau')) {
                            svg.closest('a, div[role="button"], button')?.click();
                            return;
                        }
                    }
                }""")
                time.sleep(1)
                logger.info("Create clique via fallback JS.")

            time.sleep(2)

            # ── 3. Select images via file chooser ─────────────────────────
            # "Select from computer" button opens a file input
            with page.expect_file_chooser(timeout=12_000) as fc_info:
                for sel in (
                    'button:has-text("Select from computer")',
                    "button:has-text(\"Sélectionner sur l'ordinateur\")",
                    'button:has-text("Select From Computer")',
                    'div[role="button"]:has-text("Select from computer")',
                ):
                    try:
                        page.click(sel, timeout=4_000)
                        break
                    except Exception:
                        pass

            file_chooser = fc_info.value
            # Selecting multiple files at once creates a carousel on Instagram
            file_chooser.set_files([str(p) for p in image_paths])
            logger.info("Images selectionnees : %s", [p.name for p in image_paths])
            time.sleep(3)

            # ── 4. Handle optional "OK / Crop" confirmation ───────────────
            # Instagram may ask to crop to square or keep original aspect ratio
            for sel in (
                'button:has-text("OK")',
                'button:has-text("Original")',
                "button:has-text(\"Sélectionner tout\")",
            ):
                try:
                    el = page.query_selector(sel)
                    if el:
                        el.click()
                        time.sleep(1)
                        break
                except Exception:
                    pass

            time.sleep(2)

            # ── 5. "Next" — past crop / aspect-ratio screen ───────────────
            _click_next(page, "crop screen")
            time.sleep(2)

            # ── 6. "Next" — past filter / edit screen ────────────────────
            _click_next(page, "filter screen")
            time.sleep(2)

            # ── 7. Type caption ───────────────────────────────────────────
            caption_el = None
            for sel in (
                'div[aria-label="Write a caption..."]',
                "div[aria-label=\"Écrivez une légende…\"]",
                'div[aria-label*="caption"]',
                'div[role="textbox"]',
                'textarea[aria-label*="caption"]',
            ):
                try:
                    caption_el = page.wait_for_selector(sel, timeout=6_000)
                    if caption_el:
                        break
                except Exception:
                    pass

            if caption_el:
                caption_el.click()
                time.sleep(0.5)
                # Inject text via execCommand (fast, works in Chromium)
                page.evaluate(
                    """(text) => {
                        const el =
                            document.querySelector('div[role="textbox"]') ||
                            document.querySelector('div[aria-label*="caption"]') ||
                            document.querySelector('textarea');
                        if (!el) return;
                        el.focus();
                        document.execCommand('selectAll', false, null);
                        document.execCommand('insertText', false, text);
                    }""",
                    caption,
                )
                logger.info("Legende saisie (%d caracteres).", len(caption))
            else:
                logger.warning("Zone de legende introuvable — post sans legende.")
                _screenshot(page, "error_caption.png")

            time.sleep(2)

            # ── 8. Click "Share / Partager" ───────────────────────────────
            shared = False
            for sel in (
                'div[role="button"]:has-text("Share")',
                'div[role="button"]:has-text("Partager")',
                'button:has-text("Share")',
                'button:has-text("Partager")',
            ):
                try:
                    page.click(sel, timeout=6_000)
                    shared = True
                    logger.info("Bouton 'Share' clique.")
                    break
                except Exception:
                    pass

            if not shared:
                logger.error("Impossible de cliquer sur 'Share'.")
                _screenshot(page, "error_share.png")
                browser.close()
                return False

            # ── 9. Wait for confirmation ──────────────────────────────────
            time.sleep(5)
            for sel in (
                'text=Your post has been shared',
                'text=Votre publication a ete partagee',
                'text=Post shared',
                'span:has-text("Your post has been shared")',
            ):
                try:
                    page.wait_for_selector(sel, timeout=20_000)
                    logger.info("Publication confirmee !")
                    break
                except Exception:
                    pass
            else:
                # No confirmation found — still likely published; log warning
                logger.warning(
                    "Confirmation non detectee (le post a probablement ete publie)."
                )

            # Save refreshed cookies
            context.storage_state(path=str(_STATE_FILE))
            browser.close()
            return True

        except Exception as exc:
            logger.error("Erreur inattendue lors du post browser : %s", exc)
            _screenshot(page, "error_unexpected.png")
            browser.close()
            return False


# ── Public API ────────────────────────────────────────────────────────────────

def upload_post(image_paths: list[Path], content: PostContent, audio: AudioTrack) -> str:
    """
    Publie un carousel sur Instagram via Playwright.

    image_paths : [slide_fr.jpg, slide_en.jpg]
    Retourne "BROWSER_POST_OK" (ou "DRY_RUN_MEDIA_ID" en mode DRY_RUN).
    """
    caption = _build_caption(content, audio)

    if settings.dry_run:
        logger.info("[DRY RUN] Browser post simule : %s", [str(p) for p in image_paths])
        logger.info("[DRY RUN] Legende (300 premiers caracteres) :\n%s", caption[:300])
        return "DRY_RUN_MEDIA_ID"

    # Ensure we have a saved session
    if not _has_session():
        logger.info("Aucune session Playwright — ouverture du navigateur pour connexion manuelle.")
        interactive_login()

    # Anti-bot delay
    delay = random.uniform(10, 30)
    logger.info("Attente de %.0f secondes avant publication...", delay)
    time.sleep(delay)

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            success = _post_carousel(image_paths, caption)

            if success:
                logger.info("Publication reussie (tentative %d/%d).", attempt, _MAX_RETRIES)
                return "BROWSER_POST_OK"

            # _post_carousel returned False → session expired, re-login
            if not _has_session():
                logger.info("Session expiree — re-connexion manuelle requise.")
                interactive_login()

        except Exception as exc:
            logger.error("Tentative %d/%d echouee : %s", attempt, _MAX_RETRIES, exc)

        if attempt < _MAX_RETRIES:
            logger.info("Nouvelle tentative dans %d secondes...", _RETRY_BACKOFF)
            time.sleep(_RETRY_BACKOFF)

    raise RuntimeError(f"Echec de la publication apres {_MAX_RETRIES} tentatives")
