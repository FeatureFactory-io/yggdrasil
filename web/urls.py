from django.urls import path

from web import views

urlpatterns = [
    path("", views.welcome, name="welcome"),
    path("views/browse/", views.view_browse, name="view_browse"),
    path("elements/", views.element_list, name="element_list"),
    path("changesets/", views.changeset_list, name="changeset_list"),
    path("chat/", views.chat_assist, name="chat_assist"),
]
