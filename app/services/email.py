"""
Email sending utilities using Resend and SMTP fallback.
Handles sending verification codes and password reset codes.
"""

import os
import logging
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
MAIL_FROM = os.getenv("MAIL_FROM", "DevEarn <onboarding@resend.dev>")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else None
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() in ("1", "true", "yes")


def is_smtp_configured() -> bool:
    return bool(SMTP_HOST and SMTP_PORT and SMTP_USER and SMTP_PASSWORD)


def send_email_via_smtp(to_email: str, subject: str, html_content: str) -> bool:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = MAIL_FROM
    msg["To"] = to_email
    msg.set_content("Veuillez ouvrir cet email dans un client prenant en charge le HTML.")
    msg.add_alternative(html_content, subtype="html")

    try:
        if SMTP_USE_SSL:
            smtp = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30)
        else:
            smtp = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)

        with smtp as server:
            if SMTP_USE_TLS and not SMTP_USE_SSL:
                server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"SMTP email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"SMTP send failed for {to_email}: {e}")
        return False


def send_email_via_resend(to_email: str, subject: str, html_content: str) -> bool:
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY is not configured, skipping Resend send")
        return False

    try:
        import requests

        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": MAIL_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code in (200, 201, 202):
            logger.info(f"Resend email sent successfully to {to_email}")
            return True

        logger.error(f"Resend send failed for {to_email}: {response.status_code} {response.text}")
        return False
    except Exception as e:
        logger.error(f"Resend send error for {to_email}: {e}")
        return False


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    # Prioritize SMTP if configured, as it supports sending to any address (unlike Resend sandbox)
    if is_smtp_configured():
        if send_email_via_smtp(to_email, subject, html_content):
            return True
        logger.warning("SMTP failed, falling back to Resend")

    if RESEND_API_KEY:
        return send_email_via_resend(to_email, subject, html_content)

    logger.warning("No email provider configured. Set RESEND_API_KEY or SMTP_* credentials.")
    return False


def send_verification_code_email(to_email: str, code: str) -> bool:
    subject = "Vérifiez votre adresse e-mail - DevEarn"
    html_content = f"""
    <html>
        <head></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f4f5fb; padding: 20px; margin: 0;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 40px 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #1a1a1a; font-size: 24px; margin: 0 0 10px 0;">Bienvenue sur DevEarn !</h1>
                    <p style="color: #666; font-size: 14px; margin: 0;">Veuillez vérifier votre adresse e-mail pour continuer.</p>
                </div>

                <p style="color: #334155; font-size: 15px; line-height: 1.6; margin-bottom: 30px;">
                    Merci de vous être inscrit ! Utilisez le code ci-dessous pour activer votre compte :
                </p>

                <div style="text-align: center; margin: 40px 0;">
                    <div style="display: inline-block; padding: 20px 40px; background-color: #f0f4ff; border: 2px solid #5a43f8; border-radius: 8px;">
                        <span style="font-size: 36px; font-weight: bold; color: #5a43f8; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                            {code}
                        </span>
                    </div>
                </div>

                <p style="color: #666; font-size: 13px; text-align: center; margin: 30px 0 0 0;">
                    Ce code expire dans 10 minutes.
                </p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">
                    Si vous n'avez pas créé ce compte, vous pouvez ignorer ce message.
                </p>
            </div>
        </body>
    </html>
    """
    return send_email(to_email, subject, html_content)


def send_password_reset_code_email(to_email: str, code: str) -> bool:
    subject = "Réinitialisez votre mot de passe - DevEarn"
    html_content = f"""
    <html>
        <head></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f4f5fb; padding: 20px; margin: 0;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 40px 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #1a1a1a; font-size: 24px; margin: 0 0 10px 0;">Réinitialisez votre mot de passe</h1>
                    <p style="color: #666; font-size: 14px; margin: 0;">Utilisez le code ci-dessous pour finaliser la réinitialisation.</p>
                </div>

                <p style="color: #334155; font-size: 15px; line-height: 1.6; margin-bottom: 30px;">
                    Nous avons reçu une demande de réinitialisation de votre mot de passe. Entrez le code ci-dessous pour continuer :
                </p>

                <div style="text-align: center; margin: 40px 0;">
                    <div style="display: inline-block; padding: 20px 40px; background-color: #f0f4ff; border: 2px solid #5a43f8; border-radius: 8px;">
                        <span style="font-size: 36px; font-weight: bold; color: #5a43f8; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                            {code}
                        </span>
                    </div>
                </div>

                <p style="color: #666; font-size: 13px; text-align: center; margin: 30px 0 0 0;">
                    Ce code expire dans 30 minutes.
                </p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">
                    Si vous n'avez pas demandé de réinitialisation, ignorez simplement cet email.
                </p>
            </div>
        </body>
    </html>
    """
    return send_email(to_email, subject, html_content)
