# Make Celery app available when Django starts.
from yggdrasil.celery import app as celery_app

__all__ = ["celery_app"]
