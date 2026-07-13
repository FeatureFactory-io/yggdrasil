from django.urls import path

from api.views import HealthView

urlpatterns = [
    path("", HealthView.as_view(), name="health"),
]
