"""
Instagram posting via Playwright browser automation (persistent Chromium profile).

Flow:
  First run:
    → Opens Chromium with a persistent profile (data/session/chromium_profile/)
    → User logs in to Instagram manually (accepts cookies, enters credentials)
    → Browser state saved automatically in the profile directory
    → Browser closes

  Posting runs:
    → Reuses the same persistent profile (already logged in, cookies intact)
    → Navigates to Instagram, creates carousel post, publishes
    → No re-login needed (session lasts weeks/months)

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

# Persistent Chromium profile — survives between runs, stores cookies/session
_PROFILE_DIR: Path = settings.data_dir / "session" / "chromium_profile"

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_LAUNCH_ARGS = [
    "--start-maximized",
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-default-browser-check",
]


# ── Caption builder ───────────────────────────────────────────────────────────

def _build_caption(content: PostContent, audio: AudioTrack) -> str:
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
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        return sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright non installe. Lance :\n"
            "  pip install playwright\n"
            "  python -m playwright install chromium"
        ) from exc


def _launch_context(p, headless: bool = False, slow_mo: int = 80):
    """
    Launch a persistent Chromium context that saves all cookies/sessions
    automatically to _PROFILE_DIR (like a real browser profile).
    Returns a BrowserContext — call context.close() when done.
    """
    _PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return p.chromium.launch_persistent_context(
        str(_PROFILE_DIR),
        headless=headless,
        slow_mo=slow_mo,
        args=_LAUNCH_ARGS,
        viewport={"width": 1280, "height": 900},
        user_agent=_USER_AGENT,
    )


def _dismiss_cookie_banner(page) -> None:
    """Try to auto-dismiss Instagram's cookie consent popup."""
    time.sleep(2)
    candidates = [
        "Decline optional cookies",
        "Refuser les cookies optionnels",
        "Only allow essential cookies",
        "Allow all cookies",
        "Autoriser tous les cookies",
        "Tout autoriser",
        "Accepter",
        "Accept all",
    ]
    for text in candidates:
        try:
            btn = page.get_by_role("button", name=text, exact=False)
            if btn.count() > 0:
                btn.first.click()
                logger.info("Popup cookies fermee : '%s'", text)
                time.sleep(1)
                return
        except Exception:
            pass

    # Last resort: click the last button inside any cookie dialog
    try:
        for dialog_sel in ('[role="dialog"]', 'div[data-focus-lock-disabled]'):
            dialog = page.query_selector(dialog_sel)
            if dialog:
                buttons = dialog.query_selector_all("button")
                if buttons:
                    buttons[-1].click()
                    logger.info("Popup cookies fermee via dernier bouton du dialogue.")
                    time.sleep(1)
                    return
    except Exception:
        pass


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


def _click_next(page, label: str = "") -> None:
    """Click the 'Next / Suivant' button in the post-creation wizard."""
    for sel in (
        'div[role="button"]:has-text("Next")',
        'div[role="button"]:has-text("Suivant")',
        'button:has-text("Next")',
        'button:has-text("Suivant")',
    ):
        try:
            page.click(sel, timeout=8_000)
            logger.info("'Next' clique (%s).", label)
            return
        except Exception:
            pass
    logger.warning("Bouton 'Next' introuvable (%s).", label)
    _screenshot(page, f"error_next_{label.replace(' ', '_')}.png")


def _screenshot(page, filename: str) -> None:
    try:
        path = settings.data_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path))
        logger.info("Capture d'ecran : %s", path)
    except Exception:
        pass


# ── Session management ────────────────────────────────────────────────────────

def _has_session() -> bool:
    """True if a Chromium profile directory exists with any content."""
    return _PROFILE_DIR.exists() and any(_PROFILE_DIR.iterdir())


def interactive_login() -> None:
    """
    Open a visible Chromium browser so the user can log in to Instagram manually.
    The session is persisted automatically in the Chromium profile directory.

    Called via:  python -m ledeclicmental --login
    """
    sync_playwright = _sync_playwright()

    print("\n" + "=" * 60)
    print("  CONNEXION INSTAGRAM — Navigateur en cours d'ouverture...")
    print("  1. Acceptez ou refusez les cookies Instagram")
    print("  2. Connectez-vous avec votre email et mot de passe")
    print("  3. Le navigateur se fermera automatiquement")
    print("=" * 60 + "\n")

    with sync_playwright() as p:
        context = _launch_context(p, headless=False, slow_mo=50)
        page = context.new_page()

        page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded", timeout=60_000)

        # Try to auto-dismiss cookie banner
        _dismiss_cookie_banner(page)

        logger.info("Navigateur ouvert — en attente de connexion (max 10 min).")

        # Poll page.url — no JS eval needed (avoids CSP issues)
        deadline = time.time() + 600
        logged_in = False
        while time.time() < deadline:
            try:
                url = page.url
            except Exception:
                break
            if url and "/accounts/login" not in url and "instagram.com" in url:
                logged_in = True
                break
            time.sleep(2)

        if logged_in:
            time.sleep(3)
            _dismiss_popups(page)
            time.sleep(1)
            logger.info("Connexion detectee — profil sauvegarde dans %s", _PROFILE_DIR)

        context.close()

        if logged_in:
            print("\nConnexion reussie ! Session sauvegardee.\n")
        else:
            print("\nConnexion non confirmee. Relancez --login et connectez-vous.\n")


# ── Post automation ───────────────────────────────────────────────────────────

def _post_carousel(image_paths: list[Path], caption: str) -> bool:
    """
    Automate carousel upload via Instagram web UI using the persistent profile.
    Returns True on success, False if session expired or flow fails.
    """
    sync_playwright = _sync_playwright()

    with sync_playwright() as p:
        context = _launch_context(p, headless=False, slow_mo=80)
        page = context.new_page()

        try:
            # ── 1. Navigate to Instagram ──────────────────────────────────
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=60_000)

            # Wait for React to fully render the left navigation
            try:
                page.wait_for_selector("nav", timeout=15_000)
            except Exception:
                pass
            time.sleep(3)

            if "/accounts/login" in page.url:
                logger.warning("Session expiree — re-connexion necessaire.")
                context.close()
                return "session_expired"

            _dismiss_cookie_banner(page)
            _dismiss_popups(page)
            time.sleep(1)

            # ── 2. Click "Create / Nouveau post" ─────────────────────────
            create_clicked = False
            for sel in (
                'svg[aria-label="New post"]',
                'svg[aria-label="Nouveau post"]',
                'svg[aria-label="Créer"]',
                '[aria-label="New post"]',
                '[aria-label="Nouveau post"]',
                '[aria-label="Create"]',
                '[aria-label="Créer"]',
                'span:has-text("Create")',
                'span:has-text("Créer")',
                # Broader: any nav link containing an SVG (Create is usually last before Profile)
                'nav svg[aria-label]',
            ):
                try:
                    el = page.wait_for_selector(sel, timeout=3_000)
                    if el:
                        # For SVG, click the parent clickable element
                        parent = el.evaluate_handle(
                            "el => el.closest('a, div[role=\"button\"], button') || el"
                        )
                        parent.as_element().click()
                        create_clicked = True
                        logger.info("Bouton 'Create' clique via : %s", sel)
                        break
                except Exception:
                    pass

            if not create_clicked:
                logger.warning("Bouton Create introuvable — capture d'ecran.")
                _screenshot(page, "error_create.png")
                context.close()
                return "ui_failed"

            time.sleep(2)

            # ── 2b. Click "Post" in the create sub-menu (if present) ──────
            # Instagram shows a menu: Post / Story / Reel / Live
            for sel in (
                'span:has-text("Post")',
                'div[role="menuitem"]:has-text("Post")',
                'button:has-text("Post")',
                'span:has-text("Publication")',
                'div[role="menuitem"]:has-text("Publication")',
            ):
                try:
                    el = page.wait_for_selector(sel, timeout=3_000)
                    if el:
                        el.click()
                        logger.info("'Post' selectionne dans le menu.")
                        time.sleep(2)
                        break
                except Exception:
                    pass

            # ── 3. Upload images via file chooser ─────────────────────────
            with page.expect_file_chooser(timeout=15_000) as fc_info:
                for sel in (
                    'button:has-text("Select from computer")',
                    "button:has-text(\"S\u00e9lectionner sur l'ordinateur\")",
                    'button:has-text("Select From Computer")',
                    'div[role="button"]:has-text("Select from computer")',
                    'button:has-text("Importer depuis")',
                    'button:has-text("Choisir")',
                ):
                    try:
                        page.click(sel, timeout=4_000)
                        break
                    except Exception:
                        pass

            file_chooser = fc_info.value
            file_chooser.set_files([str(img) for img in image_paths])
            logger.info("Images selectionnees : %s", [img.name for img in image_paths])
            time.sleep(3)

            # ── 4. Dismiss crop / aspect ratio dialog ─────────────────────
            for sel in ('button:has-text("OK")', 'button:has-text("Original")'):
                try:
                    el = page.query_selector(sel)
                    if el:
                        el.click()
                        time.sleep(1)
                        break
                except Exception:
                    pass
            time.sleep(2)

            # ── 5. Next (crop screen) ─────────────────────────────────────
            _click_next(page, "crop")
            time.sleep(2)

            # ── 6. Next (filter screen) ───────────────────────────────────
            _click_next(page, "filter")
            time.sleep(2)

            # ── 7. Caption ────────────────────────────────────────────────
            caption_el = None
            for sel in (
                'div[aria-label="Write a caption..."]',
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
                page.keyboard.press("Control+a")
                page.keyboard.type(caption, delay=5)
                logger.info("Legende saisie (%d caracteres).", len(caption))
            else:
                logger.warning("Zone de legende introuvable.")
                _screenshot(page, "error_caption.png")

            time.sleep(2)

            # ── 8. Share ──────────────────────────────────────────────────
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
                context.close()
                return "ui_failed"

            # ── 9. Confirm ────────────────────────────────────────────────
            time.sleep(5)
            confirmed = False
            for sel in (
                'span:has-text("Your post has been shared")',
                'span:has-text("Post shared")',
                'span:has-text("Votre publication")',
            ):
                try:
                    page.wait_for_selector(sel, timeout=20_000)
                    logger.info("Publication confirmee !")
                    confirmed = True
                    break
                except Exception:
                    pass

            if not confirmed:
                logger.warning("Confirmation non detectee (post probablement publie).")

            context.close()
            return "ok"

        except Exception as exc:
            logger.error("Erreur inattendue : %s", exc)
            _screenshot(page, "error_unexpected.png")
            try:
                context.close()
            except Exception:
                pass
            return "ui_failed"


# ── Public API ────────────────────────────────────────────────────────────────

def upload_post(image_paths: list[Path], content: PostContent, audio: AudioTrack) -> str:
    """
    Publie un carousel sur Instagram via Playwright (profil persistant).
    Retourne "BROWSER_POST_OK" ou "DRY_RUN_MEDIA_ID".
    """
    caption = _build_caption(content, audio)

    if settings.dry_run:
        logger.info("[DRY RUN] Browser post simule : %s", [str(p) for p in image_paths])
        logger.info("[DRY RUN] Legende (300 premiers caracteres) :\n%s", caption[:300])
        return "DRY_RUN_MEDIA_ID"

    if not _has_session():
        logger.info("Aucun profil Chromium — ouverture pour connexion manuelle.")
        interactive_login()

    delay = random.uniform(10, 30)
    logger.info("Attente de %.0f secondes avant publication...", delay)
    time.sleep(delay)

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            result = _post_carousel(image_paths, caption)

            if result == "ok":
                logger.info("Publication reussie (tentative %d/%d).", attempt, _MAX_RETRIES)
                return "BROWSER_POST_OK"

            if result == "session_expired":
                logger.info("Session expiree — re-connexion manuelle requise.")
                interactive_login()
            else:
                # UI detection failed — just retry without re-login
                logger.warning("Echec UI (tentative %d/%d) — nouvelle tentative.", attempt, _MAX_RETRIES)

        except Exception as exc:
            logger.error("Tentative %d/%d echouee : %s", attempt, _MAX_RETRIES, exc)

        if attempt < _MAX_RETRIES:
            logger.info("Nouvelle tentative dans %d secondes...", _RETRY_BACKOFF)
            time.sleep(_RETRY_BACKOFF)

    raise RuntimeError(f"Echec de la publication apres {_MAX_RETRIES} tentatives")
