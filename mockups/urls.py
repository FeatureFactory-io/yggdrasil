from django.urls import path

from . import views

urlpatterns = [
    # AUTH-LOGIN-1, AUTH-TOKEN-1
    path("auth/login/", views.auth_login, name="mockup_auth_login"),
    path("auth/token/", views.auth_token, name="mockup_auth_token"),
    # MUNIN-BRIEFING-1
    path("munin/briefing/", views.munin_briefing, name="mockup_munin_briefing"),
    # VIEW-BROWSE-1, EXPORT-BRIEFING-1, VIEW-HISTORY-1
    path("view/browse/", views.view_browse, name="mockup_view_browse"),
    path("view/export/", views.view_export, name="mockup_view_export"),
    path("view/history/", views.view_history, name="mockup_view_history"),
    # ELEMENT CRUDLF
    path("element/", views.element_list, name="mockup_element_list"),
    path("element/create/", views.element_create, name="mockup_element_create"),
    path("element/<int:id>/", views.element_view, name="mockup_element_view"),
    path("element/<int:id>/edit/", views.element_edit, name="mockup_element_edit"),
    # Delete is a modal on ELEMENT-VIEW_ELEMENT-1, not a standalone screen — IA_guidelines.md §12.4
    # RELATIONSHIP CRUDLF
    path("relationship/", views.relationship_list, name="mockup_relationship_list"),
    path("relationship/create/", views.relationship_create, name="mockup_relationship_create"),
    path("relationship/<int:id>/", views.relationship_view, name="mockup_relationship_view"),
    path("relationship/<int:id>/edit/", views.relationship_edit, name="mockup_relationship_edit"),
    # Delete is a modal on RELATIONSHIP-VIEW_RELATIONSHIP-1, not a standalone screen — IA_guidelines.md §12.4
    # CHANGESET-LIST+FIND-1, CHANGESET-VIEW_CHANGESET-1
    path("changeset/", views.changeset_list, name="mockup_changeset_list"),
    path("changeset/<int:id>/", views.changeset_view, name="mockup_changeset_view"),
    # RATATOSK_RUN-LIST+FIND-1, RATATOSK_RUN-VIEW_RATATOSK_RUN-1
    path("ratatosk-run/", views.ratatosk_run_list, name="mockup_ratatosk_run_list"),
    path("ratatosk-run/<int:id>/", views.ratatosk_run_view, name="mockup_ratatosk_run_view"),
]
