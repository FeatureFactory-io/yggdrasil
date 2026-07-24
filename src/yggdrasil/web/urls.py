"""URL routes for the web (HTMX) layer."""

from django.urls import path

from yggdrasil.munin.views import MuninChatView
from yggdrasil.web import views

app_name = "web"

urlpatterns = [
    path("", views.index, name="index"),
    path("views/", views.ViewBrowseView.as_view(), name="view_browse"),
    path("chat/munin/", MuninChatView.as_view(), name="munin_chat"),
]
