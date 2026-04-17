"""Envoi des posts par email via Gmail SMTP."""
from __future__ import annotations

import smtplib
from datetime import date
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from ledeclicmental.config import settings
from ledeclicmental.utils.logger import get_logger

logger = get_logger(__name__)


def send_post_email(
    post_number: int,
    slide_fr: Path,
    slide_en: Path,
    caption: str,
) -> None:
    msg = MIMEMultipart()
    msg["From"] = settings.email_sender
    msg["To"] = settings.email_recipient
    today = date.today().strftime("%d/%m/%Y")
    msg["Subject"] = f"POST_{post_number} \u2014 {today}"

    msg.attach(MIMEText(caption, "plain", "utf-8"))

    for path, cid in [(slide_fr, "slide_fr"), (slide_en, "slide_en")]:
        with open(path, "rb") as f:
            img = MIMEImage(f.read(), _subtype="jpeg")
        img.add_header("Content-Disposition", "attachment", filename=path.name)
        img.add_header("Content-ID", f"<{cid}>")
        msg.attach(img)

    password = settings.email_app_password.replace(" ", "")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.email_sender, password)
        server.sendmail(settings.email_sender, settings.email_recipient, msg.as_string())

    logger.info("Email POST_%d envoy\u00e9 \u00e0 %s", post_number, settings.email_recipient)
