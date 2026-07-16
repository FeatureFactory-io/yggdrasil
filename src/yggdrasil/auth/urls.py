"""URL routes for the auth app. Namespace: auth."""

from django.urls import path

from yggdrasil.auth import views

app_name = "auth"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("tokens/", views.TokenListView.as_view(), name="token_list"),
    path("tokens/create/", views.TokenCreateView.as_view(), name="token_create"),
    path("tokens/<int:token_id>/revoke/", views.TokenRevokeView.as_view(), name="token_revoke"),
]
