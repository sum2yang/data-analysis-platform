from celery import Celery

from app.core.config import get_settings

__all__ = ["celery_app"]

settings = get_settings()

celery_app = Celery(
    "data_analysis",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_always_eager=settings.CELERY_ALWAYS_EAGER,
    task_eager_propagates=True,
)

celery_app.autodiscover_tasks(["app.tasks"])
