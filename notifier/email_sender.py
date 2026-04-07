"""
Envoi d'emails de notification via Gmail SMTP.

Deux types de mails :
1. Confirmation de candidature (Easy Apply soumis)
2. Notification d'offre (non Easy Apply) avec CV + LM en piÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¨ces jointes
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

logger = logging.getLogger(__name__)


def _build_smtp(gmail_address: str, gmail_app_password: str) -> smtplib.SMTP_SSL:
    """Ouvre une connexion SMTP Gmail."""
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(gmail_address, gmail_app_password)
    return server


def _attach_file(msg: MIMEMultipart, file_path: str):
    """Attache un fichier au mail."""
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"Fichier introuvable pour l'attachement : {file_path}")
        return
    with open(file_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={path.name}")
    msg.attach(part)


def send_applied_confirmation(
    gmail_address: str,
    gmail_app_password: str,
    to_email: str,
    job: dict,
):
    """
    Envoie un mail de confirmation aprÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¨s une candidature Easy Apply rÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©ussie.
    """
    msg = MIMEMultipart()
    msg["Subject"] = f"ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Â¦ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¦ Candidature envoyÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©e ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â {job['title']} chez {job['company']}"
    msg["From"] = gmail_address
    msg["To"] = to_email

    html = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto;">
      <h2 style="color: #0a66c2;">ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Â¦ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¦ Candidature envoyÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©e avec succÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¨s</h2>
      <table style="width:100%; border-collapse:collapse;">
        <tr><td style="padding:8px; font-weight:bold;">Poste</td>
            <td style="padding:8px;">{job['title']}</td></tr>
        <tr style="background:#f5f5f5;"><td style="padding:8px; font-weight:bold;">Entreprise</td>
            <td style="padding:8px;">{job['company']}</td></tr>
        <tr><td style="padding:8px; font-weight:bold;">Localisation</td>
            <td style="padding:8px;">{job.get('location', 'N/A')}</td></tr>
        <tr style="background:#f5f5f5;"><td style="padding:8px; font-weight:bold;">Source</td>
            <td style="padding:8px;">LinkedIn (Easy Apply)</td></tr>
        <tr><td style="padding:8px; font-weight:bold;">Offre</td>
            <td style="padding:8px;"><a href="{job['url']}" style="color:#0a66c2;">Voir l'offre</a></td></tr>
      </table>
      <p style="margin-top:20px; color:#666; font-size:13px;">
        Ta candidature a ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©tÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â© soumise automatiquement via LinkedIn Easy Apply.<br>
        Le CV et la lettre de motivation ont ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©tÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â© adaptÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©s spÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©cifiquement pour cette offre.
      </p>
      <hr style="border:none; border-top:1px solid #eee; margin:20px 0;">
      <p style="color:#999; font-size:12px;">CV Optimizer ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â Internship Automation</p>
    </body></html>
    """

    msg.attach(MIMEText(html, "html"))

    for item in applied_jobs:
        if isinstance(item, dict) and "cv_path" in item:
            _attach_file(msg, item["cv_path"])
            _attach_file(msg, item["lm_path"])

    try:
        with _build_smtp(gmail_address, gmail_app_password) as server:
            server.sendmail(gmail_address, to_email, msg.as_string())
        logger.info(f"[Email] Confirmation envoyÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©e pour {job['title']} chez {job['company']}")
    except Exception as e:
        logger.error(f"[Email] ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â°chec envoi confirmation : {e}")


def send_offer_notification(
    gmail_address: str,
    gmail_app_password: str,
    to_email: str,
    job: dict,
    cv_path: str,
    lm_path: str,
):
    """
    Envoie un mail de notification pour une offre non Easy Apply,
    avec le CV et la LM en piÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¨ces jointes.
    """
    msg = MIMEMultipart()
    msg["Subject"] = f"ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â°ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¹ Offre correspondante ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â {job['title']} chez {job['company']}"
    msg["From"] = gmail_address
    msg["To"] = to_email

    # Description tronquÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©e pour le mail
    description_preview = job.get("description", "")[:500].replace("\n", "<br>")
    if len(job.get("description", "")) > 500:
        description_preview += "..."

    html = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto;">
      <h2 style="color: #e07b00;">ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â°ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¹ Nouvelle offre de stage correspondant ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â  ton profil</h2>
      <p>Cette offre n'a pas de candidature directe (pas de Easy Apply).<br>
         <strong>Le CV et la lettre de motivation sont en piÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¨ces jointes.</strong></p>

      <table style="width:100%; border-collapse:collapse;">
        <tr><td style="padding:8px; font-weight:bold;">Poste</td>
            <td style="padding:8px;">{job['title']}</td></tr>
        <tr style="background:#f5f5f5;"><td style="padding:8px; font-weight:bold;">Entreprise</td>
            <td style="padding:8px;">{job['company']}</td></tr>
        <tr><td style="padding:8px; font-weight:bold;">Localisation</td>
            <td style="padding:8px;">{job.get('location', 'N/A')}</td></tr>
        <tr style="background:#f5f5f5;"><td style="padding:8px; font-weight:bold;">Source</td>
            <td style="padding:8px;">LinkedIn</td></tr>
      </table>

      <h3 style="margin-top:20px;">AperÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â§u de l'offre</h3>
      <div style="background:#f9f9f9; padding:15px; border-left:4px solid #e07b00; font-size:14px;">
        {description_preview}
      </div>

      <div style="margin-top:20px; text-align:center;">
        <a href="{job['url']}"
           style="background:#0a66c2; color:white; padding:12px 24px;
                  text-decoration:none; border-radius:5px; font-weight:bold;">
          ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â°ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¹Ã…â€œÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â° Postuler sur LinkedIn
        </a>
      </div>

      <p style="margin-top:20px; color:#666; font-size:13px;">
        ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â°ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â½ <strong>CV_optimisÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©.docx</strong> ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â CV adaptÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â© pour cette offre<br>
        ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â°ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â½ <strong>Lettre_motivation.docx</strong> ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â Lettre de motivation personnalisÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©e
      </p>
      <hr style="border:none; border-top:1px solid #eee; margin:20px 0;">
      <p style="color:#999; font-size:12px;">CV Optimizer ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â Internship Automation</p>
    </body></html>
    """

    msg.attach(MIMEText(html, "html"))
    _attach_file(msg, cv_path)
    _attach_file(msg, lm_path)

    try:
        with _build_smtp(gmail_address, gmail_app_password) as server:
            server.sendmail(gmail_address, to_email, msg.as_string())
        logger.info(f"[Email] Notification envoyÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©e pour {job['title']} chez {job['company']}")
    except Exception as e:
        logger.error(f"[Email] ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â°chec envoi notification : {e}")


def send_daily_summary(
    gmail_address: str,
    gmail_app_password: str,
    to_email: str,
    applied_jobs: list[dict],
    date_str: str = None,
):
    """
    Envoie un mail rÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©capitulatif quotidien listant toutes les candidatures soumises.
    """
    from datetime import date
    if not date_str:
        date_str = date.today().strftime("%d/%m/%Y")

    msg = MIMEMultipart()
    msg["Subject"] = f"ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Â¦ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¦ RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©cap du jour ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â {len(applied_jobs)} candidatures envoyÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©es ({date_str})"
    msg["From"] = gmail_address
    msg["To"] = to_email

    rows = ""
    for i, item in enumerate(applied_jobs, 1):
        job = item["job"] if isinstance(item, dict) and "job" in item else item
        bg = "#f5f5f5" if i % 2 == 0 else "#ffffff"
        rows += f"""
        <tr style="background:{bg};">
          <td style="padding:8px; text-align:center; font-weight:bold;">{i}</td>
          <td style="padding:8px;">{job.get('title', 'N/A')}</td>
          <td style="padding:8px;">{job.get('company', 'N/A')}</td>
          <td style="padding:8px;">{job.get('location', 'N/A')}</td>
          <td style="padding:8px; text-align:center;">
            <a href="{job.get('url', '#')}" style="color:#0a66c2;">Voir</a>
          </td>
        </tr>"""

    html = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333; max-width: 700px; margin: auto;">
      <h2 style="color: #0a66c2;">ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Â¦ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¦ RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©capitulatif des candidatures ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â {date_str}</h2>
      <p style="font-size:16px;">
        <strong>{len(applied_jobs)} candidatures</strong> ont ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©tÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â© soumises automatiquement aujourd'hui via LinkedIn Easy Apply.
      </p>

      <table style="width:100%; border-collapse:collapse; margin-top:15px;">
        <thead>
          <tr style="background:#0a66c2; color:white;">
            <th style="padding:10px;">#</th>
            <th style="padding:10px; text-align:left;">Poste</th>
            <th style="padding:10px; text-align:left;">Entreprise</th>
            <th style="padding:10px; text-align:left;">Localisation</th>
            <th style="padding:10px;">Lien</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>

      <p style="margin-top:20px; color:#666; font-size:13px;">
        Toutes ces candidatures ont ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©tÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â© soumises avec ton CV et ta lettre de motivation personnalisÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©s.<br>
        Tu peux recevoir des rÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©ponses directement sur <strong>sayidina.dicko@etu.univ-amu.fr</strong>.
      </p>
      <hr style="border:none; border-top:1px solid #eee; margin:20px 0;">
      <p style="color:#999; font-size:12px;">CV Optimizer ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â Internship Automation</p>
    </body></html>
    """

    msg.attach(MIMEText(html, "html"))

    for item in applied_jobs:
        if isinstance(item, dict) and "cv_path" in item:
            _attach_file(msg, item["cv_path"])
            _attach_file(msg, item["lm_path"])

    try:
        with _build_smtp(gmail_address, gmail_app_password) as server:
            server.sendmail(gmail_address, to_email, msg.as_string())
        logger.info(f"[Email] RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©capitulatif envoyÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â© : {len(applied_jobs)} candidatures.")
    except Exception as e:
        logger.error(f"[Email] ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â°chec envoi rÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©capitulatif : {e}")
