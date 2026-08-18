"""URL routes for the web (HTMX) layer."""

from django.urls import path

from yggdrasil.munin.views import MuninChatView
from yggdrasil.web import views

app_name = "web"

urlpatterns = [
    path("", views.index, name="index"),
    path("views/", views.ViewBrowseRedirectView.as_view(), name="view_browse"),
    path(
        "models/<slug:model_slug>/views/",
        views.ViewBrowseView.as_view(),
        name="view_browse_model",
    ),
    path(
        "models/<slug:model_slug>/views/save/",
        views.ViewBrowseSaveView.as_view(),
        name="view_browse_save",
    ),
    path(
        "models/<slug:model_slug>/views/<slug:view_slug>/delete/",
        views.ViewBrowseDeleteView.as_view(),
        name="view_browse_delete",
    ),
    path(
        "models/<slug:model_slug>/views/graph.json",
        views.ViewBrowseGraphJsonView.as_view(),
        name="view_browse_graph_model",
    ),
    path(
        "models/<slug:model_slug>/views/inspector/element/<int:pk>/",
        views.ViewBrowseInspectorElementView.as_view(),
        name="view_browse_inspector_element_model",
    ),
    path(
        "models/<slug:model_slug>/views/inspector/relationship/<int:pk>/",
        views.ViewBrowseInspectorRelationshipView.as_view(),
        name="view_browse_inspector_relationship_model",
    ),
    path("chat/munin/", MuninChatView.as_view(), name="munin_chat"),
]
