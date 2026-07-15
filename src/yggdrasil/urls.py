"""
Root URL configuration for Yggdrasil.

URL namespacing convention:
  /           → web app (HTMX views)
  /api/v1/    → REST API (DRF)
  /mcp/       → MCP facade (FastMCP)
  /admin/     → Django admin
  /health/    → health check (no auth)
"""

from django.contrib import admin
from django.urls import include, path

from yggdrasil.web.views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("api/v1/", include("yggdrasil.api.urls", namespace="api")),
    path("", include("yggdrasil.web.urls", namespace="web")),
]
