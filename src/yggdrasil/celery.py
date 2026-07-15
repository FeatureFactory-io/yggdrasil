"""
Celery application for Yggdrasil.

Tasks are discovered automatically from each Django app's ``tasks.py``.
The broker and result backend are both Redis (see settings.CELERY_BROKER_URL).
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yggdrasil.settings")

app = Celery("yggdrasil")

# Read Celery config from Django settings (CELERY_* prefix)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in each installed app
app.autodiscover_tasks()
