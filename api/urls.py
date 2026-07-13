"""API URL routing."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    ChangeSetViewSet,
    ElementViewSet,
    PackageViewSet,
    RelationshipViewSet,
    StereotypeViewSet,
    TraverseView,
)

router = DefaultRouter()
router.register("stereotypes", StereotypeViewSet)
router.register("packages", PackageViewSet)
router.register("elements", ElementViewSet)
router.register("relationships", RelationshipViewSet)
router.register("changesets", ChangeSetViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("traverse/", TraverseView.as_view(), name="traverse"),
]
