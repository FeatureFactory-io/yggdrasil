from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "yggdrasil.auth"
    # Avoids collision with Django's built-in django.contrib.auth (label: "auth")
    label = "yggdrasil_auth"
