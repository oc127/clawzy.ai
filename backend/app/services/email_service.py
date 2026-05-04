import logging
from email.message import EmailMessage

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


async def send_verification_email(to_email: str, token: str) -> None:
    """Send an email verification link. Fails silently if SMTP is not configured."""
    verify_url = f"{settings.frontend_url}/verify-email?token={token}"

    if not settings.smtp_host:
        logger.warning("SMTP not configured — logging verification link instead")
        logger.info("Email verification link for %s: %s", to_email, verify_url)
        return

    msg = EmailMessage()
    msg["Subject"] = "Clawzy - メール認証 / Verify Your Email"
    msg["From"] = settings.smtp_from_email
    msg["To"] = to_email
    msg.set_content(
        f"メールアドレスを確認するには、以下のリンクをクリックしてください。\n"
        f"Click the link below to verify your email address.\n\n"
        f"{verify_url}\n\n"
        f"心当たりがない場合は、このメールを無視してください。\n"
        f"If you did not create this account, please ignore this email."
    )

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
    except Exception:
        logger.exception("Failed to send verification email to %s", to_email)


async def send_password_reset_email(to_email: str, reset_token: str) -> None:
    """Send a password reset email. Fails silently if SMTP is not configured."""
    if not settings.smtp_host:
        logger.warning("SMTP not configured — logging reset link instead")
        link = f"{settings.frontend_url}/reset-password?token={reset_token}"
        logger.info("Password reset link for %s: %s", to_email, link)
        return

    reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"

    msg = EmailMessage()
    msg["Subject"] = "NipponClaw - パスワードリセット / Password Reset"
    msg["From"] = settings.smtp_from_email
    msg["To"] = to_email
    msg.set_content(
        f"パスワードをリセットするには、以下のリンクをクリックしてください。\n"
        f"Click the link below to reset your password.\n\n"
        f"{reset_url}\n\n"
        f"このリンクは{settings.password_reset_expire_minutes}分間有効です。\n"
        f"This link expires in {settings.password_reset_expire_minutes} minutes.\n\n"
        f"心当たりがない場合は、このメールを無視してください。\n"
        f"If you did not request this, please ignore this email."
    )

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
    except Exception:
        logger.exception("Failed to send password reset email to %s", to_email)
