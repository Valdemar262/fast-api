import asyncio
import logging
from typing import Any

from app.core.mail import send_email
from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def send_email_task(self: Any, *, to: str, subject: str, body: str) -> None:
    logger.info("Sending %r to %s", subject, to)
    asyncio.run(send_email(to=to, subject=subject, body=body))
