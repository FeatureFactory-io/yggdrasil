"""WSGI entry point for Yggdrasil (Gunicorn / Elastic Beanstalk)."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yggdrasil.settings")

application = get_wsgi_application()
