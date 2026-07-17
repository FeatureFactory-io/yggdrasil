"""URL patterns for the changeset bounded context."""

from django.urls import path

from yggdrasil.changeset import views

app_name = "changeset"

urlpatterns = [
    path("", views.ChangeSetListView.as_view(), name="list"),
    path("<int:changeset_id>/", views.ChangeSetDetailView.as_view(), name="detail"),
    path("<int:changeset_id>/approve/", views.ChangeSetApproveView.as_view(), name="approve"),
    path("<int:changeset_id>/reject/", views.ChangeSetRejectView.as_view(), name="reject"),
    path("<int:changeset_id>/do-other/", views.ChangeSetDoOtherView.as_view(), name="do_other"),
    path("<int:changeset_id>/rollback/", views.ChangeSetRollbackView.as_view(), name="rollback"),
]
