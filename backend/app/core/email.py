"""邮件发送服务 — SMTP"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings

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


def send_password_reset_email(to: str, token: str) -> bool:
    url = f"{settings.app_url}/reset-password?token={token}"
    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
        <h2>重置密码</h2>
        <p>你请求了重置密码。点击下面的链接设置新密码：</p>
        <p><a href="{url}" style="display:inline-block;padding:12px 24px;background:#2563eb;color:white;text-decoration:none;border-radius:8px;">重置密码</a></p>
        <p style="color:#999;font-size:13px;">链接 30 分钟内有效。如果不是你操作，请忽略此邮件。</p>
    </div>
    """
    return send_email(to, "Clawzy.ai — 重置密码", html)


def send_verification_email(to: str, token: str) -> bool:
    url = f"{settings.app_url}/verify-email?token={token}"
    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
        <h2>验证邮箱</h2>
        <p>点击下面的链接验证你的邮箱：</p>
        <p><a href="{url}" style="display:inline-block;padding:12px 24px;background:#2563eb;color:white;text-decoration:none;border-radius:8px;">验证邮箱</a></p>
        <p style="color:#999;font-size:13px;">链接 24 小时内有效。</p>
    </div>
    """
    return send_email(to, "Clawzy.ai — 验证邮箱", html)
