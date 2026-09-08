import logging
from email.message import EmailMessage

import aiosmtplib

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def send_email(*, to: str, subject: str, body: str) -> None:
    if not settings.mail_enabled:
        logger.info("Mail disabled, skipping message to %s (%s)", to, subject)
        return

    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(message, hostname=settings.smtp_host, port=settings.smtp_port)
