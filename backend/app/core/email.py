"""邮件发送服务 — SMTP"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings
from app.i18n import t, DEFAULT_LOCALE

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, html_body: str) -> bool:
    """Send an HTML email via SMTP. Returns True on success."""
    if not settings.smtp_host:
        logger.warning("SMTP not configured, email to %s suppressed: %s", to, subject)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.app_name} <{settings.smtp_from_email}>"
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.ehlo()
            if settings.smtp_port != 25:
                server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from_email, to, msg.as_string())
        logger.info("Email sent to %s: %s", to, subject)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to)
        return False


def send_password_reset_email(to: str, token: str, locale: str = DEFAULT_LOCALE) -> bool:
    url = f"{settings.app_url}/reset-password?token={token}"
    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
        <h2>{t("email.resetTitle", locale)}</h2>
        <p>{t("email.resetBody", locale)}</p>
        <p><a href="{url}" style="display:inline-block;padding:12px 24px;background:#2563eb;color:white;text-decoration:none;border-radius:8px;">{t("email.resetButton", locale)}</a></p>
        <p style="color:#999;font-size:13px;">{t("email.resetExpiry", locale)}</p>
    </div>
    """
    return send_email(to, t("email.resetSubject", locale), html)


def send_verification_email(to: str, token: str, locale: str = DEFAULT_LOCALE) -> bool:
    url = f"{settings.app_url}/verify-email?token={token}"
    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
        <h2>{t("email.verifyTitle", locale)}</h2>
        <p>{t("email.verifyBody", locale)}</p>
        <p><a href="{url}" style="display:inline-block;padding:12px 24px;background:#2563eb;color:white;text-decoration:none;border-radius:8px;">{t("email.verifyButton", locale)}</a></p>
        <p style="color:#999;font-size:13px;">{t("email.verifyExpiry", locale)}</p>
    </div>
    """
    return send_email(to, t("email.verifySubject", locale), html)
