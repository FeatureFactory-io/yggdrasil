"""Yggdrasil URL configuration."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("api.urls")),
    path("", include("web.urls")),
    path("health/", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns.append(path("mockups/", include("web.mockup_urls")))
