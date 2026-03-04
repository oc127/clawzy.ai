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


_EMAIL_WRAPPER = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;padding:40px 0;">
    <tr><td align="center">
      <table width="480" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#2563eb,#7c3aed);padding:32px 40px;text-align:center;">
            <span style="font-size:36px;">🦞</span>
            <h1 style="color:#ffffff;font-size:22px;margin:8px 0 0;font-weight:700;">Clawzy.ai</h1>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:36px 40px;">
            {content}
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="padding:20px 40px;border-top:1px solid #eee;text-align:center;">
            <p style="color:#999;font-size:12px;margin:0;">Clawzy.ai — OpenClaw as a Service</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def _wrap_email(content: str) -> str:
    return _EMAIL_WRAPPER.replace("{content}", content)


def send_password_reset_email(to: str, token: str, locale: str = DEFAULT_LOCALE) -> bool:
    url = f"{settings.app_url}/reset-password?token={token}"
    content = f"""
    <h2 style="color:#1a1a2e;font-size:20px;margin:0 0 16px;">{t("email.resetTitle", locale)}</h2>
    <p style="color:#4a4a68;font-size:15px;line-height:1.6;margin:0 0 24px;">{t("email.resetBody", locale)}</p>
    <p style="text-align:center;margin:0 0 24px;">
      <a href="{url}" style="display:inline-block;padding:14px 32px;background:#2563eb;color:#ffffff;text-decoration:none;border-radius:8px;font-weight:600;font-size:15px;">
        {t("email.resetButton", locale)}
      </a>
    </p>
    <p style="color:#999;font-size:13px;margin:0;">{t("email.resetExpiry", locale)}</p>
    """
    return send_email(to, t("email.resetSubject", locale), _wrap_email(content))


def send_verification_email(to: str, token: str, locale: str = DEFAULT_LOCALE) -> bool:
    url = f"{settings.app_url}/verify-email?token={token}"
    content = f"""
    <h2 style="color:#1a1a2e;font-size:20px;margin:0 0 16px;">{t("email.verifyTitle", locale)}</h2>
    <p style="color:#4a4a68;font-size:15px;line-height:1.6;margin:0 0 24px;">{t("email.verifyBody", locale)}</p>
    <p style="text-align:center;margin:0 0 24px;">
      <a href="{url}" style="display:inline-block;padding:14px 32px;background:#2563eb;color:#ffffff;text-decoration:none;border-radius:8px;font-weight:600;font-size:15px;">
        {t("email.verifyButton", locale)}
      </a>
    </p>
    <p style="color:#999;font-size:13px;margin:0;">{t("email.verifyExpiry", locale)}</p>
    """
    return send_email(to, t("email.verifySubject", locale), _wrap_email(content))
