from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "chancery",
    broker=settings.redis_url,
    backend=None,
    include=["app.tasks.mail"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60,
    task_always_eager=settings.celery_eager,
)
