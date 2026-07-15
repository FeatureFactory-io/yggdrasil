"""URL routes for the web (HTMX) layer."""

from django.urls import path

from yggdrasil.web import views

app_name = "web"

urlpatterns = [
    path("", views.index, name="index"),
]
