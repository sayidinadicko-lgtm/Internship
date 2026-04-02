"""
Envoi d'emails de notification via Gmail SMTP.

Deux types de mails :
1. Confirmation de candidature (Easy Apply soumis)
2. Notification d'offre (non Easy Apply) avec CV + LM en pièces jointes
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
    Envoie un mail de confirmation après une candidature Easy Apply réussie.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"✅ Candidature envoyée — {job['title']} chez {job['company']}"
    msg["From"] = gmail_address
    msg["To"] = to_email

    html = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto;">
      <h2 style="color: #0a66c2;">✅ Candidature envoyée avec succès</h2>
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
        Ta candidature a été soumise automatiquement via LinkedIn Easy Apply.<br>
        Le CV et la lettre de motivation ont été adaptés spécifiquement pour cette offre.
      </p>
      <hr style="border:none; border-top:1px solid #eee; margin:20px 0;">
      <p style="color:#999; font-size:12px;">CV Optimizer — Internship Automation</p>
    </body></html>
    """

    msg.attach(MIMEText(html, "html"))

    try:
        with _build_smtp(gmail_address, gmail_app_password) as server:
            server.sendmail(gmail_address, to_email, msg.as_string())
        logger.info(f"[Email] Confirmation envoyée pour {job['title']} chez {job['company']}")
    except Exception as e:
        logger.error(f"[Email] Échec envoi confirmation : {e}")


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
    avec le CV et la LM en pièces jointes.
    """
    msg = MIMEMultipart()
    msg["Subject"] = f"📋 Offre correspondante — {job['title']} chez {job['company']}"
    msg["From"] = gmail_address
    msg["To"] = to_email

    # Description tronquée pour le mail
    description_preview = job.get("description", "")[:500].replace("\n", "<br>")
    if len(job.get("description", "")) > 500:
        description_preview += "..."

    html = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto;">
      <h2 style="color: #e07b00;">📋 Nouvelle offre de stage correspondant à ton profil</h2>
      <p>Cette offre n'a pas de candidature directe (pas de Easy Apply).<br>
         <strong>Le CV et la lettre de motivation sont en pièces jointes.</strong></p>

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

      <h3 style="margin-top:20px;">Aperçu de l'offre</h3>
      <div style="background:#f9f9f9; padding:15px; border-left:4px solid #e07b00; font-size:14px;">
        {description_preview}
      </div>

      <div style="margin-top:20px; text-align:center;">
        <a href="{job['url']}"
           style="background:#0a66c2; color:white; padding:12px 24px;
                  text-decoration:none; border-radius:5px; font-weight:bold;">
          👉 Postuler sur LinkedIn
        </a>
      </div>

      <p style="margin-top:20px; color:#666; font-size:13px;">
        📎 <strong>CV_optimisé.docx</strong> — CV adapté pour cette offre<br>
        📎 <strong>Lettre_motivation.docx</strong> — Lettre de motivation personnalisée
      </p>
      <hr style="border:none; border-top:1px solid #eee; margin:20px 0;">
      <p style="color:#999; font-size:12px;">CV Optimizer — Internship Automation</p>
    </body></html>
    """

    msg.attach(MIMEText(html, "html"))
    _attach_file(msg, cv_path)
    _attach_file(msg, lm_path)

    try:
        with _build_smtp(gmail_address, gmail_app_password) as server:
            server.sendmail(gmail_address, to_email, msg.as_string())
        logger.info(f"[Email] Notification envoyée pour {job['title']} chez {job['company']}")
    except Exception as e:
        logger.error(f"[Email] Échec envoi notification : {e}")


def send_daily_summary(
    gmail_address: str,
    gmail_app_password: str,
    to_email: str,
    applied_jobs: list[dict],
    date_str: str = None,
):
    """
    Envoie un mail récapitulatif quotidien listant toutes les candidatures soumises.
    """
    from datetime import date
    if not date_str:
        date_str = date.today().strftime("%d/%m/%Y")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"✅ Récap du jour — {len(applied_jobs)} candidatures envoyées ({date_str})"
    msg["From"] = gmail_address
    msg["To"] = to_email

    rows = ""
    for i, job in enumerate(applied_jobs, 1):
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
      <h2 style="color: #0a66c2;">✅ Récapitulatif des candidatures — {date_str}</h2>
      <p style="font-size:16px;">
        <strong>{len(applied_jobs)} candidatures</strong> ont été soumises automatiquement aujourd'hui via LinkedIn Easy Apply.
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
        Toutes ces candidatures ont été soumises avec ton CV et ta lettre de motivation personnalisés.<br>
        Tu peux recevoir des réponses directement sur <strong>sayidina.dicko@etu.univ-amu.fr</strong>.
      </p>
      <hr style="border:none; border-top:1px solid #eee; margin:20px 0;">
      <p style="color:#999; font-size:12px;">CV Optimizer — Internship Automation</p>
    </body></html>
    """

    msg.attach(MIMEText(html, "html"))

    try:
        with _build_smtp(gmail_address, gmail_app_password) as server:
            server.sendmail(gmail_address, to_email, msg.as_string())
        logger.info(f"[Email] Récapitulatif envoyé : {len(applied_jobs)} candidatures.")
    except Exception as e:
        logger.error(f"[Email] Échec envoi récapitulatif : {e}")
