"""DEBUG-only mockup routes."""

from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path(
        "elements/",
        TemplateView.as_view(template_name="mockups/elements/list.html"),
        name="mockup_elements_list",
    ),
    path(
        "views/browse/",
        TemplateView.as_view(template_name="mockups/views/browse.html"),
        name="mockup_view_browse",
    ),
]
