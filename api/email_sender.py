"""Invio promemoria via email con SMTP (gratis: Gmail, Brevo, ecc.).

Variabili d'ambiente:
  SMTP_USER      indirizzo email del locale (es. makai.pigneto@gmail.com)
  SMTP_PASSWORD  "password per le app" di Gmail (serve la verifica in 2 passaggi)
  SMTP_HOST      default smtp.gmail.com
  SMTP_PORT      default 587
  MAIL_FROM      facoltativo, default = SMTP_USER
"""
import os
import smtplib
import logging
from datetime import datetime
from email.message import EmailMessage

logger = logging.getLogger("makai.email")

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
MAIL_FROM = os.environ.get("MAIL_FROM") or SMTP_USER


def is_configured() -> bool:
    return bool(SMTP_USER and SMTP_PASSWORD)


def send_reminder(booking_id: int, to_email: str, name: str, date_str: str, time_str: str, party_size: int) -> bool:
    try:
        date_it = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        date_it = date_str

    msg = EmailMessage()
    msg["Subject"] = "Promemoria prenotazione - Makai Grand Line Pigneto"
    msg["From"] = MAIL_FROM
    msg["To"] = to_email
    msg.set_content(
        f"Ciao {name}! 🏴‍☠️\n\n"
        f"Ti ricordiamo la tua prenotazione al Makai Grand Line Pigneto:\n"
        f"📅 {date_it} alle {time_str}\n"
        f"👥 {party_size} persone\n\n"
        f"In caso di imprevisti rispondi a questa email.\n"
        f"Ti aspettiamo, ciurma!"
    )
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
        return True
    except (smtplib.SMTPException, OSError):
        logger.exception("Email: errore di invio (prenotazione %s)", booking_id)
        return False